# CHANGELOG — Price Desk

## v0.3.0 — 2026-04-23 — Session state + data quality (kill silent-null bug)

**Trigger:** user flagged P1 🔴 Critical — `post_market_price: null` with zero reason. Downstream caller couldn't distinguish "no aftermarket session" from "info() returned null." Silent lag.

### Shipped
- `session_state` field — one of `pre_market` / `regular` / `post_market` / `closed`, based on US Eastern clock
- `data_quality` block — per-field reason string for every null aftermarket price; null now carries actionable `"missing: not in X session (current: Y)"` instead of bare null
- `get_session_state()` helper with zoneinfo (3.9+) → pytz fallback (3.8)
- `_quality_for()` helper — single source of truth for null-reason strings

### Schema
- `schema_version` 0.1.2 → 0.2.0 (additive, backward-compat — old log entries lack new fields)
- Skill `version` 0.2.0 → 0.3.0

### Verified (2026-04-23 21:35 UTC)
NVDA pull returned `session_state: "post_market"`, `post_market_price: 198.95` (real value), `pre_market_price: null` with reason `"missing: not in pre_market session (current: post_market)"`. Bug fixed.

### Why this ships P1 of Data-Integrity Foundation
Future-proof substrate: downstream skills (royal-rumble, accuracy-tracker, journalist) can now branch on `session_state` + trust `data_quality`. No more silent disagreement with the Yahoo UI.

---

## v0.2.0 — 2026-04-18

**World-Class Overhaul shipped.** Part of the fleet-wide upgrade to tree+plugin+unix architecture.

- 🌳 **Tree:** `domain:` field added to frontmatter (fund)
- 🎮 **Plugin:** `capabilities:` block declares reads / writes / calls / cannot
- 🐧 **Unix:** `unix_contract:` block declares data_format / schema_version / stdin_support / stdout_format / composable_with
- 🛡️ Schema v0.3 validation required at install (via `future-proof/scripts/validate-skill.py`)
- 🔗 Install converted to symlink pattern (kills drift between Desktop source and live install)
- 🏷️ Tagged at `v-2026-04-18-world-class` for rollback

See `memory/project_world_class_architecture.md` for the full model.

---


---

## [2026-04-18] — v0.1.2 — Menu + watchlist + log commands

### Shipped
- **Menu on bare invocation** — `.price` with no args displays 6-option menu
- **`.price watchlist`** — reads `blue-hill-capital/watchlist.md`, pulls prices for every ticker in the table
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

For Blue Hill's 12-month horizon, these limits are irrelevant.

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
