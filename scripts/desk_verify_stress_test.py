#!/usr/bin/env python3
"""
desk_verify — stress test.

Validates desk_verify.py across:
  - 10 diverse tickers (mega-cap, mid-cap, ETF, ADR, leveraged ETF)
  - 5 raw-text domain types (IR page, news, SEC, blog, anti-bot site)

Reports per-source success rate, latency, agreement rate, max spread, and
which raw-text targets pass vs fail.

Writes results to data/desk_verify_stress_YYYY-MM-DD.md.

Usage:
  python3 desk_verify_stress_test.py
"""
from __future__ import annotations

import sys
import time
import json
import statistics
from pathlib import Path
from datetime import datetime

# Import the verifier from the same directory
sys.path.insert(0, str(Path(__file__).parent))
from desk_verify import triangulate_price, fetch_raw_text  # noqa: E402

TICKER_BASKET = [
    # Mega-cap tech
    ("NVDA",  "mega-cap tech"),
    ("AAPL",  "mega-cap tech"),
    ("MSFT",  "mega-cap tech"),
    ("GOOGL", "mega-cap tech"),
    # Mega-cap non-tech
    ("BRK-B", "mega-cap non-tech (ticker uses dash)"),
    ("JPM",   "mega-cap finance"),
    # Mid-cap
    ("ROKU",  "mid-cap"),
    # ETF
    ("SPY",   "ETF (broad market)"),
    # Leveraged ETF
    ("TQQQ",  "leveraged ETF (3x QQQ)"),
    # ADR
    ("BABA",  "ADR (Chinese listing)"),
]

RAW_TEXT_TARGETS = [
    ("IR page (NVIDIA newsroom)",
     "https://nvidianews.nvidia.com/news"),
    ("News article (Reuters tech)",
     "https://www.reuters.com/technology/"),
    ("SEC EDGAR (NVIDIA submissions)",
     "https://data.sec.gov/submissions/CIK0001045810.json"),
    ("Blog (Anthropic news)",
     "https://www.anthropic.com/news"),
    ("Likely anti-bot (Bloomberg)",
     "https://www.bloomberg.com/markets"),
]


def run_triangulation_battery() -> dict:
    print("\n=== TRIANGULATION BATTERY ===\n", file=sys.stderr)
    rows = []
    source_success = {"yfinance": 0, "google": 0, "marketwatch": 0}
    spreads = []
    latencies = []

    for ticker, category in TICKER_BASKET:
        t0 = time.time()
        result = triangulate_price(ticker)
        elapsed = round(time.time() - t0, 2)
        latencies.append(elapsed)

        for src, val in result["sources"].items():
            if val is not None and val > 0:
                source_success[src] += 1

        spread = result.get("spread_pct", 0.0)
        if result["valid_count"] >= 2:
            spreads.append(spread)

        rows.append({
            "ticker": ticker,
            "category": category,
            "elapsed_sec": elapsed,
            "valid_count": result["valid_count"],
            "median": result.get("median"),
            "spread_pct": spread,
            "status": result["status"],
            "sources": result["sources"],
        })
        print(f"  {ticker:<6} {result['status']:<25} median={result.get('median', 'N/A'):<10} spread={spread:.3f}%  ({elapsed}s)", file=sys.stderr)

    n = len(TICKER_BASKET)
    return {
        "ticker_count": n,
        "source_success_rate": {k: f"{v}/{n} ({v/n*100:.0f}%)" for k, v in source_success.items()},
        "median_latency_sec": round(statistics.median(latencies), 2),
        "max_latency_sec": round(max(latencies), 2),
        "agreement_rate": f"{sum(1 for r in rows if r['status'] == 'CONSISTENT')}/{n}",
        "max_spread_pct": round(max(spreads), 3) if spreads else 0,
        "median_spread_pct": round(statistics.median(spreads), 3) if spreads else 0,
        "rows": rows,
    }


def run_raw_text_battery() -> dict:
    print("\n=== RAW-TEXT BATTERY ===\n", file=sys.stderr)
    rows = []
    for label, url in RAW_TEXT_TARGETS:
        t0 = time.time()
        result = fetch_raw_text(url, max_chars=5000)
        elapsed = round(time.time() - t0, 2)
        rows.append({
            "label": label,
            "url": url,
            "status": result["status"],
            "char_count": result.get("char_count", 0),
            "elapsed_sec": elapsed,
            "preview": (result.get("text") or "")[:200].replace("\n", " "),
        })
        print(f"  {label:<35} {result['status']:<10}  chars={result.get('char_count', 0):>6}  ({elapsed}s)", file=sys.stderr)
    return {
        "target_count": len(RAW_TEXT_TARGETS),
        "success_count": sum(1 for r in rows if r["status"] == "OK"),
        "rows": rows,
    }


def write_report(triang: dict, raw: dict) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"desk_verify_stress_{today}.md"

    md = []
    md.append(f"# desk_verify stress test — {today}")
    md.append("")
    md.append(f"Run at: {datetime.now().isoformat(timespec='seconds')}")
    md.append("")

    # Triangulation summary
    md.append("## 🔢 Triangulation battery")
    md.append("")
    md.append(f"- Tickers tested: **{triang['ticker_count']}**")
    md.append(f"- Source success rate: {json.dumps(triang['source_success_rate'])}")
    md.append(f"- Agreement rate (CONSISTENT / total): **{triang['agreement_rate']}**")
    md.append(f"- Median latency: **{triang['median_latency_sec']}s** · Max: {triang['max_latency_sec']}s")
    md.append(f"- Median spread: **{triang['median_spread_pct']}%** · Max: {triang['max_spread_pct']}%")
    md.append("")
    md.append("| Ticker | Category | Median | Spread% | Status | Sources OK | Time |")
    md.append("|---|---|---|---|---|---|---|")
    for r in triang["rows"]:
        srcs = ", ".join(k for k, v in r["sources"].items() if v is not None and v > 0)
        med = r["median"] if r["median"] is not None else "-"
        md.append(f"| {r['ticker']} | {r['category']} | {med} | {r['spread_pct']:.3f}% | {r['status']} | {srcs} | {r['elapsed_sec']}s |")
    md.append("")

    # Raw text summary
    md.append("## 📄 Raw-text battery")
    md.append("")
    md.append(f"- Targets tested: **{raw['target_count']}**")
    md.append(f"- Successful pulls: **{raw['success_count']}/{raw['target_count']}**")
    md.append("")
    md.append("| Label | Status | Chars | Time | URL |")
    md.append("|---|---|---|---|---|")
    for r in raw["rows"]:
        md.append(f"| {r['label']} | {r['status']} | {r['char_count']} | {r['elapsed_sec']}s | {r['url']} |")
    md.append("")

    # Verdict
    md.append("## 🏁 Verdict")
    md.append("")
    triang_pass = (
        triang["source_success_rate"]["yfinance"].startswith(("9", "10")) and
        triang["source_success_rate"]["google"].startswith(("9", "10"))
    )
    raw_pass = raw["success_count"] >= 3
    md.append(f"- Triangulation pass: {'🟢 YES' if triang_pass else '🟡 PARTIAL'} (need ≥90% per primary source)")
    md.append(f"- Raw-text pass: {'🟢 YES' if raw_pass else '🟡 PARTIAL'} (need ≥3/5 targets reachable)")

    out_path.write_text("\n".join(md))
    return out_path


def main():
    print(f"desk_verify stress test starting at {datetime.now().isoformat(timespec='seconds')}", file=sys.stderr)
    triang = run_triangulation_battery()
    raw = run_raw_text_battery()
    report_path = write_report(triang, raw)
    print(f"\nReport: {report_path}", file=sys.stderr)
    print(f"\n=== SUMMARY ===", file=sys.stderr)
    print(f"  Triangulation agreement: {triang['agreement_rate']}", file=sys.stderr)
    print(f"  Raw-text success:        {raw['success_count']}/{raw['target_count']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
