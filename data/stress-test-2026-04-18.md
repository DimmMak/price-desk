# Stress Test — 2026-04-18

**Run at:** 2026-04-18T04:00:48.715854+00:00

## Summary

- Tickers tested: 10
- Successful pulls: 9
- Errored pulls: 1
- Expected failures matched: True
- Avg time per pull: 362.0ms
- Total test time: 3624ms

## Results

| Ticker | Status | Price | Prev Close | Change % | ms |
|---|---|---|---|---|---|
| NVDA | OK | $201.68 | $197.9 | 1.91% | 419 |
| MSFT | OK | $422.79 | $420.93 | 0.44% | 254 |
| NOW | OK | $96.66 | $96.56 | 0.1% | 181 |
| MU | OK | $455.07 | $454.99 | 0.02% | 246 |
| JPM | OK | $310.29 | $309.69 | 0.19% | 322 |
| XOM | OK | $146.44 | $151.96 | -3.63% | 396 |
| SPY | OK | $710.14 | $702.26 | 1.12% | 295 |
| DOCU | OK | $45.74 | $46.5 | -1.63% | 363 |
| TSLA | OK | $400.62 | $388.2 | 3.2% | 289 |
| ZZZZINVALID | ERROR | $— | $— | —% | 855 |


## Raw JSON

```json
{
  "run_at": "2026-04-18T04:00:48.715854+00:00",
  "ticker_count": 10,
  "success_count": 9,
  "error_count": 1,
  "avg_elapsed_ms": 362.0,
  "total_elapsed_ms": 3624,
  "expected_failures_as_expected": true,
  "missing_successes": [],
  "unexpected_successes": [],
  "results": [
    {
      "ticker": "NVDA",
      "status": "OK",
      "price": 201.68,
      "previous_close": 197.9,
      "change_pct": 1.91,
      "day_high": 201.7,
      "day_low": 199.27,
      "currency": "USD",
      "source": "yfinance",
      "pulled_at": "2026-04-18T04:00:45.091534+00:00",
      "elapsed_ms": 419
    },
    {
      "ticker": "MSFT",
      "status": "OK",
      "price": 422.79,
      "previous_close": 420.93,
      "change_pct": 0.44,
      "day_high": 431.58,
      "day_low": 420.69,
      "currency": "USD",
      "source": "yfinance",
      "pulled_at": "2026-04-18T04:00:45.510974+00:00",
      "elapsed_ms": 254
    },
    {
      "ticker": "NOW",
      "status": "OK",
      "price": 96.66,
      "previous_close": 96.56,
      "change_pct": 0.1,
      "day_high": 98.82,
      "day_low": 96.13,
      "currency": "USD",
      "source": "yfinance",
      "pulled_at": "2026-04-18T04:00:45.765224+00:00",
      "elapsed_ms": 181
    },
    {
      "ticker": "MU",
      "status": "OK",
      "price": 455.07,
      "previous_close": 454.99,
      "change_pct": 0.02,
      "day_high": 470.97,
      "day_low": 452.2,
      "currency": "USD",
      "source": "yfinance",
      "pulled_at": "2026-04-18T04:00:45.946258+00:00",
      "elapsed_ms": 246
    },
    {
      "ticker": "JPM",
      "status": "OK",
      "price": 310.29,
      "previous_close": 309.69,
      "change_pct": 0.19,
      "day_high": 314.9,
      "day_low": 310.09,
      "currency": "USD",
      "source": "yfinance",
      "pulled_at": "2026-04-18T04:00:46.193113+00:00",
      "elapsed_ms": 322
    },
    {
      "ticker": "XOM",
      "status": "OK",
      "price": 146.44,
      "previous_close": 151.96,
      "change_pct": -3.63,
      "day_high": 146.8,
      "day_low": 141.97,
      "currency": "USD",
      "source": "yfinance",
      "pulled_at": "2026-04-18T04:00:46.516044+00:00",
      "elapsed_ms": 396
    },
    {
      "ticker": "SPY",
      "status": "OK",
      "price": 710.14,
      "previous_close": 702.26,
      "change_pct": 1.12,
      "day_high": 712.39,
      "day_low": 705.76,
      "currency": "USD",
      "source": "yfinance",
      "pulled_at": "2026-04-18T04:00:46.912108+00:00",
      "elapsed_ms": 295
    },
    {
      "ticker": "DOCU",
      "status": "OK",
      "price": 45.74,
      "previous_close": 46.5,
      "change_pct": -1.63,
      "day_high": 47.55,
      "day_low": 45.4,
      "currency": "USD",
      "source": "yfinance",
      "pulled_at": "2026-04-18T04:00:47.207500+00:00",
      "elapsed_ms": 363
    },
    {
      "ticker": "TSLA",
      "status": "OK",
      "price": 400.62,
      "previous_close": 388.2,
      "change_pct": 3.2,
      "day_high": 409.28,
      "day_low": 391.65,
      "currency": "USD",
      "source": "yfinance",
      "pulled_at": "2026-04-18T04:00:47.571038+00:00",
      "elapsed_ms": 289
    },
    {
      "ticker": "ZZZZINVALID",
      "status": "ERROR",
      "error": "No price returned from yfinance (ticker may be invalid or delisted)",
      "source": "yfinance",
      "pulled_at": "2026-04-18T04:00:47.860680+00:00",
      "elapsed_ms": 855
    }
  ]
}
```
