# 📊 Price Desk

> The Market Data Officer for Waypoint Capital.
> Live-price single source of truth. Prevents the stale-data bug.

---

## Why this exists

The 2026-04-17 rumble batch anchored analyses on 7-day-old prices pulled via web search. The NOW rumble cited $82.91 when the stock was actually at $96.66 — a 16% discrepancy that invalidated the entry plan.

**Price Desk fixes it.** Every skill that cites a price must call this skill first. Live quote, timestamped, audit-logged. Stale data is now architecturally impossible.

---

## Install

```bash
./scripts/install.sh
```

Requires: `python3` + `yfinance` (auto-installed).

---

## Commands

```
python3 scripts/price.py TICKER              → live quote
python3 scripts/price.py TICKER1 TICKER2 ... → multiple
python3 scripts/price.py --check TICKER $X   → verify cited price
python3 scripts/stress_test.py               → 10-ticker validation
```

Via skill invocation:
```
.price TICKER
.price-check TICKER $X
.price stress-test
```

---

## Honest limitations

**yfinance = Yahoo Finance scraper.** Free, reliable for US equities, ~15-min delay during market hours on free tier.

```
✅ Position/swing trading (months)        ← our use case
❌ Day trading / scalping                  ← not our use case
❌ Bid/ask spread analysis                 ← not our use case
❌ Options market-making                   ← not our use case
```

At Waypoint's horizon (12-month track record), 15-min delay is irrelevant.

---

## Validation

Stress test result (2026-04-18): **9/9 valid tickers returned correct prices, invalid ticker correctly errored, avg pull 362ms.**

NOW verification: $96.66 — exact match to Yahoo Finance UI. 🎯

🃏⚔️
