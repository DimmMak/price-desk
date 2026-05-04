#!/usr/bin/env python3
"""
desk_verify — verification layer for .chief and the data desks.

Two T1 patterns from the 2026-05-03 verification audit:

1. triangulate_price(ticker)
   Pulls quote from 3 INDEPENDENT sources in parallel (yfinance, Google
   Finance scrape, MarketWatch scrape). Returns median, spread %, and a
   per-source breakdown. Flags >0.5% spread as DISAGREEMENT.

2. fetch_raw_text(url, css_selector=None)
   curl + BeautifulSoup, no LLM summarization. Returns raw text. For
   prose-fidelity work (analyst quotes, transcripts, IR press release
   wording) — closes the WebFetch summarization-leak gap (~60-70% to
   ~95% fidelity per the forensic critique).

Usage:
  python3 desk_verify.py NVDA              → triangulate one ticker
  python3 desk_verify.py NVDA AAPL MSFT    → triangulate multiple
  python3 desk_verify.py --raw <URL>       → raw-text pull
  python3 desk_verify.py --raw <URL> <css> → raw-text from selector

Output: JSON on stdout. Exit 0 = clean; 1 = any DISAGREEMENT or pull failure.
"""
from __future__ import annotations

import sys
import json
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_8) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"
HEADERS = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
TIMEOUT = 10
SPREAD_FLAG_PCT = 0.5  # >0.5% disagreement triggers warning


# ---------- Source 1: yfinance ----------
def _yfinance_price(ticker: str) -> float | None:
    try:
        import yfinance as yf
        fi = yf.Ticker(ticker).fast_info
        # yfinance 1.2.x uses camelCase 'lastPrice'; older versions used 'last_price'
        p = fi.get("lastPrice") or fi.get("last_price")
        return float(p) if p else None
    except Exception:
        return None


# ---------- Source 2: Google Finance scrape ----------
import re as _re
_GOOG_PRICE_RE = _re.compile(r">\s*\$(\d{1,7}(?:,\d{3})*(?:\.\d{1,4}))\s*<")

def _is_crypto(ticker: str) -> bool:
    return ticker.endswith(("-USD", "-USDT")) or ticker.startswith(("BTC", "ETH", "DOGE", "SOL"))


def _google_exchanges_for(ticker: str) -> list[str]:
    """Pick the right exchange ladder for the ticker class."""
    if _is_crypto(ticker):
        return ["CRYPTO"]
    if "." in ticker:  # e.g. "BABA.US", "0700.HK"
        suffix = ticker.split(".")[-1].upper()
        return {"L": ["LON"], "HK": ["HKG"], "T": ["TYO"], "TO": ["TSE"]}.get(suffix, ["NASDAQ", "NYSE"])
    return ["NASDAQ", "NYSE", "NYSEARCA"]


def _google_price(ticker: str, exchange: str | None = None) -> float | None:
    # Pick exchange list based on ticker class (US equity / ETF / crypto / international)
    google_ticker = ticker.replace("-", ".") if not _is_crypto(ticker) else ticker
    exchanges = [exchange] if exchange else _google_exchanges_for(ticker)
    for ex in exchanges:
        url = f"https://www.google.com/finance/quote/{google_ticker}:{ex}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if r.status_code != 200:
                continue
            m = _GOOG_PRICE_RE.search(r.text)
            if m:
                return float(m.group(1).replace(",", ""))
        except (requests.ConnectionError, requests.Timeout):
            continue  # network down or slow — let other sources fill in
        except Exception:
            continue
    return None


# ---------- Source 3: MarketWatch scrape ----------
def _marketwatch_price(ticker: str) -> float | None:
    # MarketWatch uses different URL paths for crypto vs equity
    if _is_crypto(ticker):
        # Crypto path: /investing/cryptocurrency/btcusd
        slug = ticker.lower().replace("-", "").replace("usd", "usd")
        url = f"https://www.marketwatch.com/investing/cryptocurrency/{slug}"
    else:
        url = f"https://www.marketwatch.com/investing/stock/{ticker.lower()}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        el = soup.find("bg-quote", class_="value")
        if el and el.get_text():
            return float(el.get_text().strip().replace(",", "").lstrip("$"))
        el = soup.select_one("h2.intraday__price .value")
        if el:
            return float(el.get_text().strip().replace(",", "").lstrip("$"))
        return None
    except (requests.ConnectionError, requests.Timeout):
        return None  # network gap — graceful degrade
    except Exception:
        return None


# ---------- Triangulator ----------
def triangulate_price(ticker: str) -> dict:
    """Fetch from 3 sources in parallel, return median + spread + per-source."""
    sources = {
        "yfinance": _yfinance_price,
        "google": _google_price,
        "marketwatch": _marketwatch_price,
    }
    results = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fn, ticker): name for name, fn in sources.items()}
        for fut in as_completed(futures, timeout=TIMEOUT + 2):
            name = futures[fut]
            try:
                results[name] = fut.result()
            except Exception:
                results[name] = None

    valid = {k: v for k, v in results.items() if v is not None and v > 0}
    n = len(valid)
    out = {
        "ticker": ticker,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sources": results,
        "valid_count": n,
    }
    if n == 0:
        out["status"] = "ALL_FAILED"
        return out
    if n == 1:
        only_source = list(valid.keys())[0]
        out["median"] = valid[only_source]
        out["spread_pct"] = 0.0
        out["status"] = f"SINGLE_SOURCE ({only_source})"
        return out

    prices = list(valid.values())
    median = statistics.median(prices)
    spread_pct = (max(prices) - min(prices)) / median * 100
    out["median"] = round(median, 4)
    out["spread_pct"] = round(spread_pct, 3)
    out["status"] = "DISAGREEMENT" if spread_pct > SPREAD_FLAG_PCT else "CONSISTENT"
    return out


# ---------- Raw-text fetcher (T1 fix #4) ----------
def fetch_raw_text(url: str, css_selector: str | None = None, max_chars: int = 50000) -> dict:
    """Direct curl + parse. No LLM compression. Returns raw text."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if r.status_code != 200:
            return {"url": url, "status": f"HTTP_{r.status_code}", "text": None}
        soup = BeautifulSoup(r.text, "html.parser")
        if css_selector:
            els = soup.select(css_selector)
            text = "\n\n".join(el.get_text(separator=" ", strip=True) for el in els)
        else:
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        truncated = len(text) > max_chars
        return {
            "url": url,
            "status": "OK",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "char_count": len(text),
            "truncated": truncated,
            "text": text[:max_chars],
        }
    except Exception as e:
        return {"url": url, "status": f"ERROR: {type(e).__name__}: {e}", "text": None}


# ---------- CLI ----------
def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    if args[0] == "--raw":
        if len(args) < 2:
            print("Error: --raw requires a URL", file=sys.stderr)
            sys.exit(1)
        url = args[1]
        css = args[2] if len(args) > 2 else None
        result = fetch_raw_text(url, css)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["status"] == "OK" else 1)

    # Triangulate one or more tickers
    tickers = args
    failed_or_disagree = False
    for ticker in tickers:
        result = triangulate_price(ticker.upper())
        print(json.dumps(result, indent=2))
        if result["status"] in ("ALL_FAILED", "DISAGREEMENT"):
            failed_or_disagree = True
    sys.exit(1 if failed_or_disagree else 0)


if __name__ == "__main__":
    main()
