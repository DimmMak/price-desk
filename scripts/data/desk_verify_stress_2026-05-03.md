# desk_verify stress test — 2026-05-03

Run at: 2026-05-03T18:32:01

## 🔢 Triangulation battery

- Tickers tested: **10**
- Source success rate: {"yfinance": "10/10 (100%)", "google": "10/10 (100%)", "marketwatch": "7/10 (70%)"}
- Agreement rate (CONSISTENT / total): **10/10**
- Median latency: **1.05s** · Max: 1.63s
- Median spread: **0.07%** · Max: 0.29%

| Ticker | Category | Median | Spread% | Status | Sources OK | Time |
|---|---|---|---|---|---|---|
| NVDA | mega-cap tech | 198.45 | 0.166% | CONSISTENT | marketwatch, google, yfinance | 1.63s |
| AAPL | mega-cap tech | 280.14 | 0.064% | CONSISTENT | marketwatch, yfinance, google | 0.67s |
| MSFT | mega-cap tech | 414.2 | 0.290% | CONSISTENT | marketwatch, yfinance, google | 0.73s |
| GOOGL | mega-cap tech | 385.69 | 0.091% | CONSISTENT | yfinance, marketwatch, google | 0.93s |
| BRK-B | mega-cap non-tech (ticker uses dash) | 473.01 | 0.000% | CONSISTENT | yfinance, google | 1.17s |
| JPM | mega-cap finance | 312.47 | 0.234% | CONSISTENT | yfinance, marketwatch, google | 1.37s |
| ROKU | mid-cap | 123.58 | 0.000% | CONSISTENT | marketwatch, yfinance, google | 0.85s |
| SPY | ETF (broad market) | 720.65 | 0.000% | CONSISTENT | yfinance, google | 1.37s |
| TQQQ | leveraged ETF (3x QQQ) | 65.3 | 0.000% | CONSISTENT | yfinance, google | 0.63s |
| BABA | ADR (Chinese listing) | 131.5 | 0.076% | CONSISTENT | yfinance, marketwatch, google | 1.23s |

## 📄 Raw-text battery

- Targets tested: **5**
- Successful pulls: **3/5**

| Label | Status | Chars | Time | URL |
|---|---|---|---|---|
| IR page (NVIDIA newsroom) | OK | 4778 | 0.52s | https://nvidianews.nvidia.com/news |
| News article (Reuters tech) | HTTP_401 | 0 | 0.21s | https://www.reuters.com/technology/ |
| SEC EDGAR (NVIDIA submissions) | OK | 160328 | 0.36s | https://data.sec.gov/submissions/CIK0001045810.json |
| Blog (Anthropic news) | OK | 3744 | 5.67s | https://www.anthropic.com/news |
| Likely anti-bot (Bloomberg) | HTTP_403 | 0 | 0.18s | https://www.bloomberg.com/markets |

## 🏁 Verdict

- Triangulation pass: 🟢 YES (need ≥90% per primary source)
- Raw-text pass: 🟢 YES (need ≥3/5 targets reachable)