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
    from zoneinfo import ZoneInfo  # Python 3.9+ stdlib
    ET = ZoneInfo("America/New_York")
except ImportError:
    import pytz
    ET = pytz.timezone("America/New_York")

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

def get_session_state(now=None):
    """
    Returns one of: pre_market | regular | post_market | closed.
    Clock-only; US market holidays are best-effort (treated as regular if weekday).
    """
    now = (now or datetime.now(ET)).astimezone(ET)
    if now.weekday() >= 5:
        return "closed"
    minutes = now.hour * 60 + now.minute
    if 4 * 60 <= minutes < 9 * 60 + 30:
        return "pre_market"
    if 9 * 60 + 30 <= minutes < 16 * 60:
        return "regular"
    if 16 * 60 <= minutes < 20 * 60:
        return "post_market"
    return "closed"


def _quality_for(field_value, expected_session, current_session):
    """Reason string for any null aftermarket field — kills silent-null bug."""
    if field_value is not None:
        return "OK"
    if current_session == expected_session:
        return f"missing: session is {expected_session} but yfinance returned null (info() may have failed)"
    return f"missing: not in {expected_session} session (current: {current_session})"


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

        session_state = get_session_state()
        post_market_val = round(post_market, 2) if post_market else None
        pre_market_val = round(pre_market, 2) if pre_market else None

        record = {
            "ticker": ticker.upper(),
            "status": "OK",
            "price": round(current, 2),
            "previous_close": round(previous_close, 2) if previous_close else None,
            "change_pct": change_pct,
            "day_high": round(day_high, 2) if day_high else None,
            "day_low": round(day_low, 2) if day_low else None,
            "post_market_price": post_market_val,
            "pre_market_price": pre_market_val,
            "session_state": session_state,
            "data_quality": {
                "post_market_price": _quality_for(post_market_val, "post_market", session_state),
                "pre_market_price": _quality_for(pre_market_val, "pre_market", session_state),
            },
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


MENU = """
📊 PRICE DESK — Market Data Officer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What do you want to check?

1. 💲 Single / batch quote
     .price NVDA
     .price NVDA AMD MU TSLA        (batch — any number)

2. ✅ Verify a cited price
     .price --check NVDA 189.31     (is it within 2% of live?)

3. 👀 Pull the watchlist
     .price watchlist               (reads blue-hill-capital/watchlist.md)

4. 🧪 Stress-test the data layer
     .price stress-test             (10-ticker validation suite)

5. 📜 Show recent pulls
     .price log                     (last 10 from price-log.jsonl)

6. ❓ This menu
     .price                         (no args = you see this)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: yfinance (Yahoo)    Delay: ~15 min on free tier
Logged: data/price-log.jsonl every pull
"""


def read_watchlist():
    """Read tickers from blue-hill-capital/watchlist.md markdown table."""
    watchlist_path = Path.home() / "Desktop/CLAUDE CODE/blue-hill-capital/watchlist.md"
    if not watchlist_path.exists():
        return None, f"No watchlist found at {watchlist_path}"

    tickers = []
    try:
        with watchlist_path.open() as f:
            in_table = False
            for line in f:
                line = line.strip()
                # Detect the ticker table by finding a row that starts with "| "
                # followed by an UPPERCASE word (the ticker)
                if line.startswith("| TSLA") or line.startswith("| NVDA") or (
                    line.startswith("|") and "|---|" not in line and "Ticker" not in line
                ):
                    parts = [p.strip() for p in line.split("|")]
                    # First non-empty cell is the ticker
                    for p in parts:
                        if p and p.isupper() and 1 <= len(p) <= 6 and p.isalpha():
                            if p not in tickers:
                                tickers.append(p)
                            break
    except Exception as e:
        return None, f"Could not parse watchlist: {e}"

    if not tickers:
        return None, f"No tickers found in {watchlist_path}"
    return tickers, None


def show_recent_log(n=10):
    """Display last N lines from price-log.jsonl."""
    if not LOG_FILE.exists():
        print("No price log yet. Make a price call first.")
        return
    lines = LOG_FILE.read_text().strip().split("\n")
    recent = lines[-n:] if len(lines) > n else lines
    print(f"📜 Last {len(recent)} price pulls:\n")
    for line in recent:
        try:
            r = json.loads(line)
            ts = r.get("pulled_at", "—")[:19]
            ticker = r.get("ticker", "—")
            status = r.get("status", "?")
            price = r.get("price", "—")
            print(f"  {ts}  {ticker:>6}  {status:>6}  ${price}")
        except Exception:
            continue


def main():
    args = sys.argv[1:]

    # No args → show menu
    if not args:
        print(MENU)
        sys.exit(0)

    # --check TICKER PRICE
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

    # watchlist
    if args[0] == "watchlist":
        tickers, err = read_watchlist()
        if err:
            print(f"❌ {err}")
            sys.exit(1)
        print(f"👀 Pulling {len(tickers)} watchlist tickers: {' '.join(tickers)}\n")
        results = [get_price(t) for t in tickers]
        print(json.dumps(results, indent=2))
        any_error = any(r["status"] != "OK" for r in results)
        sys.exit(1 if any_error else 0)

    # log
    if args[0] == "log":
        n = 10
        if len(args) > 1:
            try:
                n = int(args[1])
            except ValueError:
                pass
        show_recent_log(n)
        sys.exit(0)

    # stress-test
    if args[0] == "stress-test":
        import subprocess

        result = subprocess.run(
            ["python3", str(Path(__file__).parent / "stress_test.py")]
        )
        sys.exit(result.returncode)

    # Default: treat each arg as a ticker
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
