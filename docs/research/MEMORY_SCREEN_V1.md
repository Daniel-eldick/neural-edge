# Memory comparison screen v1 — complete, inconclusive for learning

Run date: 2026-09-30. Protocol committed as `698a714` before downloading the selected data.
Decision/risk/replay sources remain byte-identical to `a3de91b`; hashes verified before and after.
**All three paired comparisons completed with zero policy errors, no capped candidates and no retries.**
Memory mode narrowly exceeded frozen Jev in two windows and tied in the third. The simple
breakout beat both in the first two; cash beat both Jev variants in June. No strategy promotion.

## Results after simulated trading costs

All windows are BTC/USDT five-minute candles, 00:00 UTC on the 10th through 00:00 on the
13th, end exclusive. Three independent 1,000-USDT accounts per window; no pooled portfolio
or compounded multi-window return. Each sees the same 864 candles and 21-bar warmup.

| Window | Simple breakout | Frozen Jev | Jev with memory | Cash | Buy & hold reference |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023-01 10–13 | +1.0249% | +0.1988% | +0.2464% | +0.0000% | +9.3288% |
| 2023-06 10–13 | +0.0121% | -0.5830% | -0.4998% | +0.0000% | -2.2176% |
| 2023-10 10–13 | -1.1768% | +0.0000% | +0.0000% | +0.0000% | -3.1486% |

Buy-and-hold is a full-allocation analytical reference, **not a risk-governed agent**.
It purchases at the common first tradable open after warmup, pays 0.1% entry fee and 0.1%
adverse slippage, and holds to the final mark without stops or a 24-hour exit. It bears more
exposure than the agent. All ending positions are marked to market; hypothetical liquidation
costs are excluded consistently. Bot executions pay the same fee/slippage on each actual fill.

## Coverage, exposure and costs

| Window | Raw candidate ceiling | Frozen calls | Memory calls | Memory calls seeing a prior outcome | Memory − frozen (percentage points) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023-01 | 42 | 34 | 35 | 7 | +0.047625 |
| 2023-06 | 33 | 23 | 33 | 21 | +0.083181 |
| 2023-10 | 49 | 49 | 49 | 0 | +0.000000 |

The upper bound counts all raw prior-20-bar breakouts, ignoring position/risk gates.
Actual call counts legitimately differ because each policy holds different positions.
Full coverage means every eligible candidate for each policy was evaluated, not identical
position-dependent candidate lists. Each run retained the original 100-attempt maximum.

| Window | Policy | Closed / open trades | Max sampled drawdown | Reviewed trades | AI cost (USD) |
| --- | --- | ---: | ---: | ---: | ---: |
| 2023-01 | breakout-baseline-v1 | 4 / 1 | 0.5413% | 0 | $0.000000000 |
| 2023-01 | jev-breakout-filter-v1 | 2 / 1 | 0.7694% | 0 | $0.003406074 |
| 2023-01 | jev-memory-filter-v1 | 2 / 0 | 0.4998% | 2 | $0.003821832 |
| 2023-06 | breakout-baseline-v1 | 2 / 1 | 0.4817% | 0 | $0.000000000 |
| 2023-06 | jev-breakout-filter-v1 | 2 / 0 | 0.7497% | 0 | $0.002291982 |
| 2023-06 | jev-memory-filter-v1 | 1 / 0 | 0.4998% | 1 | $0.003736068 |
| 2023-10 | breakout-baseline-v1 | 3 / 1 | 1.2447% | 0 | $0.000000000 |
| 2023-10 | jev-breakout-filter-v1 | 0 / 0 | 0.0000% | 0 | $0.004857174 |
| 2023-10 | jev-memory-filter-v1 | 0 / 0 | 0.0000% | 0 | $0.005075322 |

Study inference cost: **USD 0.023188452** across 223 successful requests.
This exactly equals the shared ledger increase; no failed/pending receipts or unresolved
reservations. Monthly accounted total is **USD 0.033189366**, leaving **USD 2.966810634**
under the existing USD 3 cap. AI spending is separate from USDT trading P&L; no unstated
USD/USDT conversion or net-operating-return claim is made.

## What the comparison does and does not establish

- Memory mode closed only three trades in total (2, 1, 0), with 28 choices receiving prior
  reviewed outcomes. October supplied no experience to retrieve; it cannot test learning.
- The variant changes instructions as well as adding cases. A single run per variant cannot
  isolate actual memory content from prompting or model nondeterminism. No confidence score
  is interpreted as calibrated profit probability, and no statistical significance is claimed.
- The fixed curriculum is unavailable in 2023 and was not included. No daily/weekly context
  or multi-year pattern retrieval was added. These are separate unfinished capabilities.
- These previously unused project windows are now consumed development evidence, not a final
  holdout. Contemporary model pretraining contamination remains possible. Three days/window
  is below the 30-day descriptive Sharpe display threshold and cannot validate a market cycle.
- Candle fills omit queueing, partial fills, explicit spread and measured model latency.
  No real exchange orders, forward paper worker or unattended process was started.
- Dates, limits, rules and prompts were not changed after outcomes. No unfavorable result
  was discarded, rerun or replaced. Read-only report validation was corrected without
  modifying any completed experiment or consuming new model calls.

## Decision

Keep the agent in research. Do not promote memory as proven useful. The next design work is
causal daily/weekly context and earlier pattern examples, with failed analogues and explicit
invalidation. Preserve frozen controls; predeclare fresh evaluation windows before measuring
that separate feature. Larger studies and forward paper operation remain required.

## Provenance and artifacts

Source format/checksums: [Binance public data](https://github.com/binance/binance-public-data).
Pinned model and price rechecked before calls: [TypeSafe models](https://docs.typesafe.ai/models).
No new provider or dependency was added.

| Window | Source ZIP SHA-256 | CSV SHA-256 |
| --- | --- | --- |
| 2023-01 | `0b77520b2fc89c896430fd885bda345a808d61a512ef34ce62cf6a150b81e9ff` | `385b914d3c850c2b583883de78551ab890b9004a1f5ff93df979aa5d9b67c153` |
| 2023-06 | `781415877a1eaf4b376351bb3dc3cc31bc941b009a7b89a6a833cb6fb757279f` | `bf63de9177d2ec7d0ad245de31c627ed463c3949414cfbcd4199cfff036c79df` |
| 2023-10 | `6a14d2b75ad5020d56c12cd17e90e6661023f34a12fa4173364fd26a9879ae56` | `553298708ba5750204b5dfea612e2eaab11bba7de5d868ebb3a7ee201193705d` |

Local artifacts: ignored `user_data/research/memory-screen-v1/`. Each window preserves
its source ZIP/checksum, CSV/manifest, three journals, two response stores and CLI output.
Root records: `preflight.json`, `execution-start.json`, `execution-end.json`,
`reconciliation.json`, `verified-comparison.json`, `verified-cockpit.html`, and
`evidence-hashes.json`. The latter locks each completed journal/receipt SHA-256.
Earlier intermediate reports remain saved; the verified report is the delivery artifact.

Generate a new report without making model calls (use new output filenames):

```bash
.venv/bin/python -m src.evaluation \
  --window user_data/research/memory-screen-v1/2023-01 \
  --window user_data/research/memory-screen-v1/2023-06 \
  --window user_data/research/memory-screen-v1/2023-10 \
  --output /private/tmp/memory-screen-report.json \
  --html /private/tmp/memory-screen-cockpit.html
```

Optional repeated `--journal` / `--archive` flags retain earlier evidence in the cockpit.
Published snapshot retains the three earlier runs plus fifteen new replay/reference records.
The overview selects October memory mode by predeclared input order, even though it stayed
flat; it does not select the best-returning window. Open dated evidence groups for other
periods. Memory graphs prioritize the matching frozen Jev comparator.

Code-review/QA: [comparison screen review](../reviews/2026-09-30_MEMORY_SCREEN_QA.md).
Cockpit access: [hosting guide](../guides/COCKPIT_HOSTING.md).
