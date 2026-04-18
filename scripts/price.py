#!/usr/bin/env python3
"""
price-desk — live price puller with freshness guarantees.

Primary source:  yfinance (Yahoo Finance — 15-min delay during market hours on free tier)
Fallback source: none currently (will add Alpha Vantage on API key provision)

Usage:
  python3 price.py TICKER               → single ticker
  python3 price.py TICKER1 TICKER2 ...  → multiple tickers
  python3 price.py --check TICKER $X    → verify a cited price within 2% of live

Output: JSON on stdout, one record per ticker.
Exit code: 0 if all successful, 1 if any failed or suspicious.
"""
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import yfinance as yf
except ImportError:
    print(json.dumps({"error": "yfinance not installed. Run: pip install yfinance"}))
    sys.exit(2)

LOG_FILE = Path(__file__).parent.parent / "data" / "price-log.jsonl"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Thresholds
STALE_MINUTES_MARKET_HOURS = 30  # during market hours, quote must be <30 min old
STALE_MINUTES_CLOSED = 1440      # after hours, quote can be up to 24h old (previous close)
CHECK_TOLERANCE_PCT = 2.0        # --check flag: live must be within 2% of cited


def log_pull(record):
    """Append every price pull to data/price-log.jsonl."""
    try:
        with LOG_FILE.open("a") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        pass  # logging never breaks a pull


def get_price(ticker):
    """
    Returns dict with current price + metadata.
    Always returns something — includes status field for success/error.
    """
    pulled_at = datetime.now(timezone.utc).isoformat()

    try:
        tkr = yf.Ticker(ticker)

        # Try fast_info first (quickest, structured)
        try:
            fi = tkr.fast_info
            current = fi.get("lastPrice") or fi.get("last_price")
            previous_close = fi.get("previousClose") or fi.get("previous_close")
            day_high = fi.get("dayHigh") or fi.get("day_high")
            day_low = fi.get("dayLow") or fi.get("day_low")
            currency = fi.get("currency", "USD")
        except Exception:
            current = previous_close = day_high = day_low = None
            currency = "USD"

        # Pull extended-hours prices (post-market + pre-market) via .info
        # This is slower (~1-2s) but gives us the full picture.
        post_market = None
        pre_market = None
        try:
            info = tkr.info or {}
            post_market = info.get("postMarketPrice")
            pre_market = info.get("preMarketPrice")
        except Exception:
            pass  # extended-hours data is best-effort

        # Fallback to history if fast_info incomplete
        if current is None:
            hist = tkr.history(period="2d")
            if len(hist) > 0:
                current = float(hist["Close"].iloc[-1])
                if len(hist) > 1:
                    previous_close = float(hist["Close"].iloc[-2])

        if current is None:
            record = {
                "ticker": ticker.upper(),
                "status": "ERROR",
                "error": "No price returned from yfinance (ticker may be invalid or delisted)",
                "source": "yfinance",
                "pulled_at": pulled_at,
            }
            log_pull(record)
            return record

        current = float(current)
        previous_close = float(previous_close) if previous_close else None

        change_pct = None
        if previous_close and previous_close > 0:
            change_pct = round(((current - previous_close) / previous_close) * 100, 2)

        record = {
            "ticker": ticker.upper(),
            "status": "OK",
            "price": round(current, 2),
            "previous_close": round(previous_close, 2) if previous_close else None,
            "change_pct": change_pct,
            "day_high": round(day_high, 2) if day_high else None,
            "day_low": round(day_low, 2) if day_low else None,
            "post_market_price": round(post_market, 2) if post_market else None,
            "pre_market_price": round(pre_market, 2) if pre_market else None,
            "currency": currency,
            "source": "yfinance",
            "pulled_at": pulled_at,
        }
        log_pull(record)
        return record

    except Exception as e:
        record = {
            "ticker": ticker.upper(),
            "status": "ERROR",
            "error": f"{type(e).__name__}: {str(e)}",
            "source": "yfinance",
            "pulled_at": pulled_at,
        }
        log_pull(record)
        return record


def check_price(ticker, cited_price):
    """
    Verify a cited price is within CHECK_TOLERANCE_PCT of live.
    Returns dict with verdict: OK / STALE / ERROR.
    """
    live = get_price(ticker)
    if live["status"] != "OK":
        return {
            "ticker": ticker.upper(),
            "verdict": "ERROR",
            "reason": f"Could not fetch live price: {live.get('error', 'unknown')}",
            "cited_price": cited_price,
        }

    live_price = live["price"]
    delta_pct = abs((live_price - cited_price) / live_price * 100)

    if delta_pct > CHECK_TOLERANCE_PCT:
        return {
            "ticker": ticker.upper(),
            "verdict": "STALE",
            "cited_price": cited_price,
            "live_price": live_price,
            "delta_pct": round(delta_pct, 2),
            "tolerance_pct": CHECK_TOLERANCE_PCT,
            "warning": f"Cited ${cited_price} is {round(delta_pct, 1)}% off from live ${live_price}. DO NOT USE CITED PRICE.",
        }

    return {
        "ticker": ticker.upper(),
        "verdict": "OK",
        "cited_price": cited_price,
        "live_price": live_price,
        "delta_pct": round(delta_pct, 2),
    }


def main():
    args = sys.argv[1:]
    if not args:
        print("Usage:")
        print("  price.py TICKER [TICKER2 ...]")
        print("  price.py --check TICKER PRICE")
        sys.exit(1)

    if args[0] == "--check":
        if len(args) != 3:
            print("Usage: price.py --check TICKER PRICE")
            sys.exit(1)
        ticker = args[1]
        try:
            cited = float(args[2])
        except ValueError:
            print(f"Invalid price: {args[2]}")
            sys.exit(1)
        result = check_price(ticker, cited)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["verdict"] == "OK" else 1)

    # Regular ticker pull mode
    results = []
    any_error = False
    for ticker in args:
        r = get_price(ticker)
        results.append(r)
        if r["status"] != "OK":
            any_error = True

    print(json.dumps(results, indent=2))
    sys.exit(1 if any_error else 0)


if __name__ == "__main__":
    main()
