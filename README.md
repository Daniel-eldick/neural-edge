# NeuralEdge

Research project for an AI apprentice trader that learns selectively from historical market replay and later paper trading.

**Start here: [Apprentice trader reference and plan](docs/active/APPRENTICE_TRADER_PLAN.md).**

Status: offline replay includes causal observations, simulated accounting, risk enforcement,
restart recovery and daily performance reporting. Jev can filter simulated breakout candidates
under the USD 3/month allowance. An opt-in evidence teacher now reviews closed trades and
provides causal, same-run memory to Jev. Improved performance is not yet demonstrated.
The first [historical pilot](docs/research/BTC_WEEK_2024_06_PILOT.md) is complete, with
incomplete Jev coverage after its predeclared attempt cap. Profitability remains unproven.

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

The cockpit displays saved experiments in one browser page, with returns, drawdown,
trade records, and recorded replay equity. The overview highlights Jev when present, four
headline metrics, switchable return/account-value charts, a same-input baseline overlay, daily
return bars, a candle-close drawdown chart, decision breakdown and timestamped trade timeline.
Full records and assumptions expand on demand. Market times are historical UTC; the snapshot
generation time is separate. Daily bars read recorded daily returns, not a sampled equity curve.
Incomplete evaluation warnings remain visible. Memory runs report reviewed trades, retrieval
counts and the last review timestamp. The original pilot did not use memory. This remains a
dated snapshot; live connection status, automatic updates and start/pause controls are pending.

[Open the private online cockpit](https://neural-edge-cockpit-16pe3ge3m-daniel-eldicks-projects.vercel.app) and sign in with the Vercel account
that owns this project. It uses your existing Vercel plan. Results update only when regenerated
and redeployed. See [hosting and refresh instructions](docs/guides/COCKPIT_HOSTING.md).

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
50 records. No saved API configuration is included in the page. Runs with matching input
hashes, dates and execution settings get a comparison table. Policy errors/attempt exhaustion
produce an explicit degraded-coverage warning. AI spending is shown in USD separately from
trading returns in USDT. The generated results page is `user_data/cockpit/index.html`;
`src/cockpit/template.html` is only the template and has no saved results.

To regenerate the first historical comparison:

```bash
.venv/bin/python -m src.cockpit --journal user_data/research/btc-week-2024-06-v1/baseline.sqlite --journal user_data/research/btc-week-2024-06-v1/jev.sqlite
```

To prepare a new dataset from an existing Binance spot monthly archive and its downloaded
official checksum, use new output paths (existing files are never overwritten):

```bash
.venv/bin/python -m src.replay.dataset --archive BTCUSDT-5m-2024-06.zip --checksum BTCUSDT-5m-2024-06.zip.CHECKSUM --symbol BTC/USDT --start 2024-06-01 --end 2024-06-08 --output candles.csv
```

The importer validates the source hash, timestamp units, OHLCV, candle close times and exact
contiguous coverage. It writes a CSV and adjacent provenance manifest without repairing data.

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

The experimental Jev filter is opt-in:

```bash
.venv/bin/python -m src.replay --csv candles.csv --journal user_data/ai/jev-run-001.sqlite --policy jev --max-model-calls 20
```

This makes paid calls for eligible 20-bar breakout candidates using only the most recent
21 closed OHLCV bars and current portfolio. Jev can accept or decline the candidate; code
still sets the 2% price stop / 4% target and enforces account-risk limits. This is an
experimental filter, not a complete trader or a validated profitable strategy.

The default is 20 attempts per run (configurable 1–100), within the shared monthly budget.
Keep the generated `.responses.sqlite` file beside its replay journal. Resume with the same
`--policy jev`, attempt limit, data and settings, adding `--resume`. Saved answers are reused
without calling the provider again. Failed or uncertain requests veto that candidate and are
never automatically retried. A lost or replaced response file cannot be recreated for resume.
Protective exits continue during provider failures. New code versions intentionally refuse
old recovery contracts; retain the original revision if an experiment must be resumed.

The cockpit's decision records include model choices and successful inference costs; summary
trading P&L excludes AI costs. Unresolved reservations remain in the authoritative budget ledger.
Controlled learning evaluation, a generative teacher and online controls remain pending.
One synthetic end-to-end check returned WAIT with one real Jev call (1,885 input tokens,
$0.000079170). It verifies integration, not trading performance; it is excluded from the
saved-market-results cockpit.


## Evidence teacher and memory

Use a fresh journal for the opt-in memory variant:

```bash
.venv/bin/python -m src.replay --csv candles.csv --journal user_data/ai/memory-run-001.sqlite --policy jev-memory --max-model-calls 20
```

This uses the same paid Jev connector, durable responses and monthly budget. The deterministic
teacher itself makes no API calls. It pairs this run's completed trades, waits at least one
replay interval after exit, then records a review. Jev receives the last six eligible cases
for the same symbol, including losses, with candidate status and explicit uncertainty.
Memory retains at most 64 cases; the journal preserves full evidence. Separate runs start
empty. There is no rule promotion, model training or change to risk limits.

Six original [curriculum cards](src/memory/curriculum.json) are separate from the
[exercise answer keys](docs/curriculum/FOUNDATIONS.md). They are available only from
2026-09-30 UTC; a 2024 replay receives none. Model pretraining contamination remains an
unresolved historical-testing limitation.

Pause/resume uses `--policy jev-memory` and the identical source/data/settings. Reviews,
retrieval records and memory checkpoint commit with each candle. Recovery reconstructs
and verifies memory from that run's journal; mismatched evidence or response stores fail
before new provider calls. Integrity failures roll back the candle. Provider outages veto
new decisions while existing protective exits continue.

Verification uses synthetic candles and recorded providers, not performance evidence.
Next: predeclare unseen comparison windows for memory-on, frozen Jev and simple controls,
with full candidate coverage and costs. Then forward paper evaluation. Daily unattended
learning and an always-on worker are not implemented or started.
