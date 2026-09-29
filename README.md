# NeuralEdge

Research project for an AI apprentice trader that learns selectively from historical market replay and later paper trading.

**Start here: [Apprentice trader reference and plan](docs/active/APPRENTICE_TRADER_PLAN.md).**

Status: offline replay includes causal observations, simulated accounting, risk enforcement,
restart recovery and daily performance reporting. Jev connectivity is verified under the
USD 3/month allowance. The AI trader, teacher and learning loop are still pending.
Profitability is unproven.

- [Documentation index](docs/README.md)
- [Agent instructions](AGENTS.md)
- [Historical setup plan](docs/archive/NEURAL_EDGE_PROJECT_SETUP.md)

Run the offline replay with your synchronized OHLCV CSV:

```bash
python -m src.replay --csv candles.csv --journal run-001.sqlite
# Or pause after 500 candle batches, then resume with identical inputs and settings:
python -m src.replay --csv candles.csv --journal run-002.sqlite --stop-after 500
python -m src.replay --csv candles.csv --journal run-002.sqlite --resume
```

See the reference plan's **Offline replay usage** section for setup, CSV format and simulation limits. This command runs a fixed comparison policy, not the AI apprentice.

Resume preserves cash, pending decisions, positions, policy state and the drawdown halt.
Each candle batch commits its events and checkpoint together. Changed data, settings,
replay code or policy identity/source are rejected; completed runs cannot resume. Keep the
journal and its `.lock` sidecar together; do not remove the sidecar while a replay is open.
Recovery supports local macOS/Linux filesystems; external model calls and exchange orders
need separate deduplication/reconciliation before integration.

The existing Freqtrade config remains separate: its three-position limit and legacy sizing helper do not enforce the new replay limits. No live trading or background worker is enabled.

## Results cockpit

The local cockpit displays saved experiments in one browser page, with returns, drawdown,
trade records, and recorded replay equity. It is a dated snapshot; the AI trading loop,
teacher/memory, live connection status, start/pause controls and online hosting are not connected yet.

Completed replays also report the number of complete UTC days and descriptive daily Sharpe
using sample standard deviation, zero risk-free return and sqrt(365) annualization.
Leading/trailing partial days are excluded; zero-return days count. Fewer than 30 full days
or zero variance shows an explanation instead of a score. This reporting threshold is not
proof of profitable learning. Legacy archives without these metrics show "Not reported".

```bash
.venv/bin/python -m src.cockpit --archive user_data/backtest_results/backtest-result-2026-04-06_04-41-23.zip
open user_data/cockpit/index.html
```

For new completed replay runs, use `--journal run-001.sqlite`. Both input flags can be
repeated. No inputs produces an honest empty state. Regenerate after each completed run;
browser refresh alone does not update the snapshot. Input files are opened read-only.
Missing, corrupt, failed or incomplete runs fail explicitly rather than showing a false
success. The journal chart samples at most approximately 1,000 observations; its displayed
range is not a substitute for the run's drawdown statistic. Decision details show the last
50 records. No saved API configuration is included in the page.

## Jev connection and AI allowance

Daniel approved **USD 3 total AI inference per UTC calendar month** on 2026-09-30.
Put the private token in the ignored `.env.local` as `TYPESAFE_API_KEY=...` or provide it
through the process environment. Never put it in chat, a command argument, or Git.

```bash
# One-time initialization. Refuses to replace an existing ledger.
.venv/bin/python -m src.agents.jev --init-budget
# Local accounting only; makes no API call.
.venv/bin/python -m src.agents.jev --status
# One harmless paid connection check, covered by the allowance.
.venv/bin/python -m src.agents.jev --check
```

The connector pins `jev-1.13.0`. Each request reserves $0.003 in the shared local
`user_data/ai/budget.sqlite` before contacting TypeSafe, then settles successful validated
responses at $0.042 per million reported input tokens (output tokens free). Failed or
ambiguous requests keep the full reservation; there are no automatic retries. Missing,
corrupt or exhausted accounting blocks new calls. Do not delete or replace the ledger:
it is the spending record shared by all local runs, and future model providers must use it.

Pricing was verified 2026-09-30. New calls stop on 2026-11-01 until pricing is reviewed.
The application guard covers calls made through this connector, not API spending in other
applications, taxes or provider-side billing changes. It is not a TypeSafe account-level cap.

The connection is verified; no trading policy calls Jev yet. The teacher, learned memory,
controlled learning evaluation and online cockpit controls remain pending. A connection-check
answer is not a trading result or evidence of profitable decisions.
