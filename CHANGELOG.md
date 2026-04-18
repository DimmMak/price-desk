# CHANGELOG — Price Desk

---

## [2026-04-18] — v0.1.2 — Menu + watchlist + log commands

### Shipped
- **Menu on bare invocation** — `.price` with no args displays 6-option menu
- **`.price watchlist`** — reads `waypoint-capital/watchlist.md`, pulls prices for every ticker in the table
- **`.price log [N]`** — displays last N entries from `price-log.jsonl` (human-readable)
- **`.price stress-test`** — now works via price.py passthrough (was previously only via stress_test.py)

### Why
User asked for a menu + discoverability. Watchlist pull was already implicit via batch mode but needed the convenience wrapper. Audit log was hidden in JSONL; now surface-level.

### Note on versioning
v0.1.1 added post-market/pre-market prices. This version (v0.1.2) adds command surface.

---

## [2026-04-18] — v0.1.1 — Post-market + pre-market prices

### Shipped
- Added `post_market_price` and `pre_market_price` fields to output
- Pulls via `tkr.info` (slower but comprehensive) in addition to `fast_info`

### Trigger
User caught that NOW showed $96.66 regular close but Yahoo UI had after-hours $97.21. yfinance default returns regular market only. Fixed.

### Verified
NOW now returns both $96.66 (regular) and $97.21 (post-market) — exact match to Yahoo Finance UI.

---

## [2026-04-18] — v0.1.0 — Initial ship + stress test passed

**Trigger:** User caught the critical stale-price bug on the 2026-04-17 rumble batch. Web search cited NOW at $82.91 while actual price was $96.66 (+16.6% discrepancy). This invalidated the entry plan. Fund operations paused until fix shipped.

### Shipped
- `scripts/price.py` — yfinance wrapper with single-ticker + batch + --check modes
- `scripts/stress_test.py` — 10-ticker validation suite
- `scripts/install.sh` — sync to `~/.claude/skills/price-desk/`
- `SKILL.md` — architectural invariant: no trade without live-price verification
- Every pull logs to `data/price-log.jsonl` (append-only audit trail)

### Validation — 2026-04-18 stress test

```
Tickers tested:     10
Successful pulls:   9/9 valid
Errored pulls:      1 (ZZZZINVALID — expected failure)
Avg pull time:      362ms
NOW verification:   $96.66 (exact match to Yahoo Finance UI screenshot)
```

### Architectural rule

**Every skill that cites a price must call price-desk first. Every trade decision must pass `.price-check TICKER $cited` within 15 min of execution. No exceptions.**

### Known limits (honest, not hidden)

- ~15 min delay during market hours on free Yahoo tier
- Not suitable for day trading / scalping / HFT
- International ADRs occasionally flaky
- Rate-limited at hundreds of calls/minute

For Waypoint's 12-month horizon, these limits are irrelevant.

### Retroactive impact

The following rumbles from 2026-04-17 were anchored on stale prices:

| Ticker | Old cited | Live (2026-04-18) | Delta |
|---|---|---|---|
| NOW | $82.91 | $96.66 | +16.6% |
| NVDA | $189.31 | $201.68 | +6.5% |
| TSLA | $391.95 | $400.62 | +2.2% |
| MU | $377.58 | $455.07 | +20.5% |
| AMD | $255.07 | _(re-verify required)_ | _?_ |

**All of yesterday's rumbles must be re-anchored before any trade.** This is what the Market Data Officer prevents going forward.
