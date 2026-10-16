# NeuralEdge

Research project for an AI apprentice trader that learns selectively from historical market replay and later paper trading.

**Start here: [Apprentice trader reference and plan](docs/active/APPRENTICE_TRADER_PLAN.md).**

Status: offline replay includes causal observations, simulated accounting, risk enforcement,
restart recovery and daily performance reporting. Jev can filter simulated breakout candidates
under the USD 3/month allowance. An opt-in evidence teacher now reviews closed trades and
provides causal, same-run memory to Jev. Improved performance is not yet demonstrated.
The first [historical pilot](docs/research/BTC_WEEK_2024_06_PILOT.md) is complete, with
incomplete Jev coverage after its predeclared attempt cap. The subsequent
[three-window memory screen](docs/research/MEMORY_SCREEN_V1.md) completed with full coverage:
memory mode narrowly beat frozen Jev twice and tied once, but only closed three trades.
The simple baseline beat both in the first two windows. A subsequent
[context screen](docs/research/CONTEXT_SCREEN_V1.md) completed three fresh 2022 comparisons:
context Jev stayed in cash throughout, avoiding memory-only losses but matching cash.
The subsequent [opportunity screen](docs/research/OPPORTUNITY_SCREEN_V1.md) stopped on a
connection failure in its first context run; the comparison is incomplete. A durable failure
gate now blocks further model requests for that run, including after restart. Profitability remains unproven.

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
counts and the last review timestamp. The original pilot did not use memory. The online link
below still serves a dated snapshot. A live-updating shell is implemented and verified locally;
cloud connection awaits acceptance of the free storage integration. Start/pause controls remain pending.

[Open the private online cockpit](https://neural-edge-cockpit-fnrbbq9de-daniel-eldicks-projects.vercel.app) and sign in with the Vercel account
that owns this project. It uses your existing Vercel plan. Results update only when regenerated
and redeployed on that existing preview. The new shell polls every 30 seconds, distinguishes
source freshness from historical result dates, retains charts during outages and preserves view
choices on refresh. See [live setup and hosting instructions](docs/guides/COCKPIT_HOSTING.md#live-updates-local-implementation-online-connection-pending).

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
Robust learning evaluation, a generative teacher and online controls remain pending.
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
before new provider calls. Integrity failures roll back the candle. A failed or uncertain provider attempt blocks all new model requests in that response store,
including after restart. Saved successful answers remain readable; existing protective exits continue.

Correctness verification uses synthetic candles and recorded providers. The first actual
[memory comparison screen](docs/research/MEMORY_SCREEN_V1.md) is complete; its report includes
results, limits, costs and a read-only regeneration command (`python -m src.evaluation`).
An opt-in daily/weekly context variant is now implemented and correctness-tested (below).
The first context comparison is complete (below). The fresh opportunity screen stopped after a
provider failure; see its preserved evidence below. Next: resolve uncertain provider accounting,
then establish a new frozen evaluation protocol that separates context from prompt effects.
Recurring-pattern retrieval remains a separate unfinished capability. Larger studies and forward paper evaluation
remain required. Daily unattended learning and an always-on worker are not implemented or started.

## Daily and weekly context (experimental)

A separate `jev-context` variant combines the same trade memory with closed daily/weekly
OHLCV context. Existing `jev` and `jev-memory` prompts remain unchanged. This is a tested
capability, **not a proven profitable strategy or a four-year-cycle detector**.

```bash
.venv/bin/python -m src.replay --csv candles.csv --journal user_data/ai/context-run-001.sqlite \
  --policy jev-context --context-csv daily.csv --max-model-calls 20
```

`daily.csv` uses columns `symbol,opened_at,open,high,low,close,volume` in that order.
Timestamps are UTC Unix seconds at midnight; each row represents one complete daily candle.
The file must be contiguous, finite, single-symbol and match the intraday symbol, with at
most 10,000 rows / 4 MiB. Gaps, duplicates and wrong intervals fail explicitly. Verify source
provenance before real research: this parser does not certify that data came from an exchange.
`src.evaluation.daily.convert_daily` now verifies official daily monthly archives/checksums;
`reconcile` cross-checks complete intraday days against their daily OHLCV before evaluation.

At each decision only already-closed days and complete Monday-to-Monday UTC weeks are exposed.
Payloads contain up to 30 daily / 12 weekly candles. Descriptors use the last 20 days / 8 weeks:
period return, its direction and mean high-low range divided by open. These are descriptions,
not forecasts. Incomplete sample or stale last-close date produces `unknown` with no descriptor.
Expect at least eight full earlier weeks for weekly descriptors; a partial first week is omitted.
Supplying future rows never makes their prices available early. Historical arrival/revision
latency and model pretraining contamination remain unresolved.

The context source hash is recorded in the manifest and bound to recovery. Resume requires
identical daily bytes as well as the existing replay inputs/settings/policy. Full-file hash stays
outside model input; earlier requests remain identical when only future prices change. Dated
`CONTEXT_READ` records and durable requests preserve the exact supplied evidence. The cockpit
recognizes context+memory runs and prefers memory-only as the comparison overlay.

Implementation tests used recorded providers. The subsequent [actual context study](docs/research/CONTEXT_SCREEN_V1.md)
completed 173 paid requests for USD 0.035785470: all 88 context decisions waited; each
memory-only account lost approximately 0.50%. Cash matched context trading performance
without inference spending. All three periods declined; no profitable entry or rising-market
ability was demonstrated. The private cockpit now retains 38 actual replay/reference records, including the failed screen below.
Synthetic QA runs are not published.
New source versions reject old unfinished checkpoints by design; use the original revision
for those runs. Completed reports remain readable. See [context QA](docs/reviews/2026-09-30_MARKET_CONTEXT_QA.md).

To rebuild the three context comparisons without model calls, use `python -m src.evaluation
--with-context` with the three window directories and new JSON/HTML output paths; see the
[study report](docs/research/CONTEXT_SCREEN_V1.md) for the complete command and provenance.
The default evaluation mode still validates the earlier frozen-versus-memory study.


## Opportunity screen and failure recovery

The [four-window opportunity screen](docs/research/OPPORTUNITY_SCREEN_V1.md) was fixed before
acquisition. February baseline and memory replays completed without policy errors; context
had one connection failure. May/August/November trials were not started. The cockpit preserves
February with an **Incomplete test** warning; it is not a valid paired-performance conclusion.

Thirty-seven successful requests cost USD 0.007903602; one uncertain request retains its
USD 0.003 reservation. Accounted monthly total is USD 0.079878438, leaving USD 2.920121562.
The reservation remains unresolved; it has not been reset or treated as confirmed actual cost.
No automatic retry. The failure exposed one later distinct call under the old policy; the new
response-store gate prevents that continuation and survives reopening/checkpoint recovery.
Old study results remain unchanged. See [review and QA](docs/reviews/2026-09-30_OPPORTUNITY_SCREEN_QA.md).
