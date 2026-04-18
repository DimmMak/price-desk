#!/usr/bin/env python3
"""
price-desk — stress test.

Validates yfinance against a basket of 10 diverse tickers.
Reports: pull success rate, time-to-pull, price sanity, edge cases.
Writes results to data/stress-test-YYYY-MM-DD.md

Usage:
  python3 stress_test.py
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from price import get_price

# 10 diverse tickers — stresses different edge cases
TEST_TICKERS = [
    # Mega-cap tech (active, high-volume)
    "NVDA",
    "MSFT",
    # Mid-cap (the user's target zone)
    "NOW",
    "MU",
    # Value / defensive
    "JPM",
    "XOM",
    # ETF (different quote structure)
    "SPY",
    # Small-cap (lower volume)
    "DOCU",
    # Volatile / meme-adjacent
    "TSLA",
    # Intentional edge case — malformed ticker
    "ZZZZINVALID",
]


def run_stress_test():
    results = []
    start = time.time()

    for ticker in TEST_TICKERS:
        t0 = time.time()
        r = get_price(ticker)
        elapsed_ms = int((time.time() - t0) * 1000)
        r["elapsed_ms"] = elapsed_ms
        results.append(r)
        print(f"  {ticker:>14}  {r['status']:>6}  {r.get('price', '—'):>10}  ({elapsed_ms}ms)")

    total_elapsed = int((time.time() - start) * 1000)

    # Summary
    success_count = sum(1 for r in results if r["status"] == "OK")
    error_count = sum(1 for r in results if r["status"] == "ERROR")
    avg_elapsed = (
        sum(r["elapsed_ms"] for r in results) / len(results) if results else 0
    )

    expected_failures = ["ZZZZINVALID"]
    expected_successes = [t for t in TEST_TICKERS if t not in expected_failures]
    actual_success_tickers = [r["ticker"] for r in results if r["status"] == "OK"]
    missing_successes = [t for t in expected_successes if t not in actual_success_tickers]
    unexpected_successes = [
        t for t in expected_failures if t in actual_success_tickers
    ]

    summary = {
        "run_at": datetime.now(timezone.utc).isoformat(),
        "ticker_count": len(TEST_TICKERS),
        "success_count": success_count,
        "error_count": error_count,
        "avg_elapsed_ms": round(avg_elapsed, 1),
        "total_elapsed_ms": total_elapsed,
        "expected_failures_as_expected": set(expected_failures) == set(
            [r["ticker"] for r in results if r["status"] == "ERROR"]
        ),
        "missing_successes": missing_successes,
        "unexpected_successes": unexpected_successes,
        "results": results,
    }

    # Write markdown report
    report_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = Path(__file__).parent.parent / "data" / f"stress-test-{report_date}.md"
    with report_path.open("w") as f:
        f.write(f"# Stress Test — {report_date}\n\n")
        f.write(f"**Run at:** {summary['run_at']}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- Tickers tested: {summary['ticker_count']}\n")
        f.write(f"- Successful pulls: {success_count}\n")
        f.write(f"- Errored pulls: {error_count}\n")
        f.write(f"- Expected failures matched: {summary['expected_failures_as_expected']}\n")
        f.write(f"- Avg time per pull: {summary['avg_elapsed_ms']}ms\n")
        f.write(f"- Total test time: {total_elapsed}ms\n\n")
        if missing_successes:
            f.write(f"**⚠️ MISSING SUCCESSES (should have worked): {missing_successes}**\n\n")
        if unexpected_successes:
            f.write(f"**⚠️ UNEXPECTED SUCCESSES (bad ticker resolved): {unexpected_successes}**\n\n")
        f.write(f"## Results\n\n")
        f.write("| Ticker | Status | Price | Prev Close | Change % | ms |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in results:
            f.write(
                f"| {r['ticker']} | {r['status']} | "
                f"${r.get('price', '—')} | "
                f"${r.get('previous_close', '—')} | "
                f"{r.get('change_pct', '—')}% | "
                f"{r['elapsed_ms']} |\n"
            )
        f.write("\n\n## Raw JSON\n\n```json\n")
        f.write(json.dumps(summary, indent=2))
        f.write("\n```\n")

    print(f"\n{'='*60}")
    print(f"STRESS TEST SUMMARY")
    print(f"{'='*60}")
    print(f"  Tickers tested:          {summary['ticker_count']}")
    print(f"  Successful pulls:        {success_count}")
    print(f"  Errored pulls:           {error_count}")
    print(f"  Expected failures OK?:   {summary['expected_failures_as_expected']}")
    print(f"  Avg time per pull:       {summary['avg_elapsed_ms']}ms")
    print(f"  Total test time:         {total_elapsed}ms")
    print(f"  Report saved to:         {report_path.name}")
    if missing_successes:
        print(f"  ⚠️ MISSING:              {missing_successes}")
    if unexpected_successes:
        print(f"  ⚠️ UNEXPECTED:           {unexpected_successes}")

    # Return exit code 0 if healthy, 1 if any concerns
    if missing_successes or unexpected_successes:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run_stress_test())
