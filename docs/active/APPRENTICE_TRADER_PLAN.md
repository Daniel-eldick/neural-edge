# NeuralEdge — apprentice trader reference and implementation plan

Date: 2026-09-20
Status: IMPLEMENTATION AUTHORIZED on 2026-09-23; first offline foundation implemented.
Progress is tracked by milestone evidence below, not an estimated overall percentage.
Owner: Daniel. Intended reader: the next implementing agent/CTO.

## 1. Purpose and decision boundary

Build a research system that behaves like a selective junior trader: study a sourced curriculum, observe a market sequentially, enter only when a setup warrants it, manage positions, record decisions, and learn from completed experience. Waiting is a valid action; there is no trade quota.

The research question is whether staged learning improves unseen, cost-adjusted trading performance over a frozen agent and simple strategies. Profitability is unproven. A working program, a persuasive journal, and one profitable period are different achievements. No dependable income deadline is justified.

This file is the single active project reference. Other status pages are navigation pointers. The April setup plan is preserved as historical evidence, not an execution queue. Do not resume its sensory-system tasks automatically. The September 20 documentation handoff is followed by the September 23 implementation increment described below.

## 2. Agreed requirements

| Dimension | User decision |
| --- | --- |
| Market | Major cryptocurrencies |
| Sequence | Intraday first; swing later |
| Apprentices | 5-minute intraday trader and separate 1-minute scalping apprentice |
| Direction | Long-only initially |
| Inputs | Charts and volume only; numerical OHLCV and derived indicators allowed |
| Curriculum | Assistant selects and ranks material |
| Supervision | Trader + teacher + risk governor |
| Positions | At most five simultaneous positions, shared across apprentices |
| Per-trade risk | At most 0.5% of account equity |
| Aggregate open risk | At most 2.5% of account equity |
| Holding time | Agent chooses exits, maximum 24 hours for intraday |
| Drawdown | Halt for review at 10% from portfolio equity high-water mark |
| Learning | Staged: memory, then strategy-selection weights, then rules |
| Historical screening | Net profit, annualized Sharpe > 1, maximum drawdown < 10% |
| Operating goal | Background operation, eventually minimal weekly review |
| Current authorization | Implementation and local verification; AI inference capped at USD 3/month (2026-09-30); no deployment or real trading |

The proposed 1.5% aggregate cap was NOT accepted; preserve 2.5%.
The recommendation to defer scalping was NOT accepted as a scope deletion. Retain it as a separate milestone requiring better execution evidence.
Live capital, shorting, leverage, paid services beyond the USD 3/month AI allowance, and deployment are not authorized.

## 3. Repository review: actual state

Review baseline: develop, tree 8ad20fc05ac9b2b281e5d3343231205299114f51 (2026-09-20).
This was a static inspection; historical test reports are not fresh verification.

| Area | Observed | Implication |
| --- | --- | --- |
| src/strategies/alpha_strategy.py | Long-only 5m RSI/EMA/volume baseline; fixed ROI ladder and -10% price stop | Keep as comparison strategy, not apprentice implementation |
| src/core/risk.py | PositionSizer allocates equity × base fraction × conviction multiplier; no stop distance input | Not stop-based account-risk sizing; cannot represent agreed 0.5% risk |
| Risk integration | Strategy does not reference PositionSizer or CircuitBreaker | Helper tests do not prove execution enforces portfolio risk |
| Risk constants | Legacy 1% base fraction and 1x/3x/10x multipliers | Do not mistake these for approved apprentice limits |
| config.json | Spot, dry_run true, three positions, $1,000 paper wallet, BTC/ETH/SOL, Binance | Existing defaults conflict with five shared positions; unchanged in this PR |
| src/core/api_client.py | HTTP client with cache and rate limiting | Reusable selectively; cache growth already documented |
| src/sensory/*.py | Dataclasses and NotImplementedError functions | Deferred; news/on-chain/macro excluded from initial inputs |
| src/signals, src/autoresearch, src/adapters | Only package initializers | No evaluator, learning loop or adapter implementation |
| tests | Baseline/helper tests and expected failures for sensory stubs | Preserve; do not count xfails as implemented features |
| Old plan | Reports 58 passed / 17 xfailed and one trade, -0.14%, June–August 2024 | Historical author-reported results, not proof of edge or freshly reproduced |
| Tooling | Python >=3.11, broad Freqtrade dependency range; inherited framework text | Pin compatible versions during authorized setup; verify commands then |
| Operations | No tracked Docker Compose file or CI workflow in reviewed tree | Earlier deployment/preview claims are not established |

A strategy's 10% price stop is not a 10% portfolio drawdown rule. The risk helper's class constants are also not a security boundary merely because one mapping is read-only.

## 4. Proposed architecture and engine decision

These are implementation proposals, not new user-approved requirements.

- Market replay builds one timestamped observation containing only data available at that instant.
- Trader returns a validated proposal: WAIT, ENTER_LONG, HOLD, MODIFY_EXIT or EXIT.
- Deterministic risk governor approves, resizes or rejects it before the execution simulator.
- Account ledger tracks cash, reserved cash, pending orders, fills, positions and marked-to-market equity.
- Journal persists observations, proposals, vetoes, fills, outcomes and model/version provenance.
- Teacher reviews completed experience on a defined schedule, producing candidate lessons rather than unquestionable truth.
- Promotion evaluator compares candidate versions with baselines under frozen evaluation rules.

Freqtrade is the provisional baseline/paper execution engine because it is already integrated. Its batch indicator pipeline is not automatically a causal, stateful agent environment. First prove chronological callbacks, cross-pair ordering and memory isolation with a small integration experiment before committing to the bridge. An independent replay loop may be necessary. If this requires invasive engine changes, evaluate NautilusTrader rather than forcing the abstraction.

Freqtrade standard candle backtests assume requested-price fills within candle high/low and no slippage. Fees alone are insufficient. Add conservative execution scenarios and compare paper fills with assumptions. NautilusTrader is a candidate for finer replay, not a promise of accurate results without good data.

One-minute scalping requires trade/quote data or explicitly limited simulation claims. A 1m chart cadence does not describe the price path, queue position, partial fills or spread. The apprentices may see only candles/volume while the simulator uses finer data to model execution.

Model selection remains open:
- Start with one model provider behind a narrow interface; record exact version and cost.
- Strong LLM for trader/teacher experiments; separate prompts, state and permissions.
- Daniel reaffirmed on 2026-09-29 that Jev belongs in the intended new brain. Integrate it
  behind a decision-support interface and benchmark it before granting decision influence.
  API connectivity is verified under the USD 3/month allowance (2026-09-30).
  An opt-in experimental breakout filter now calls it during offline replay. One synthetic
  end-to-end check and first historical pilot completed. The pilot had incomplete coverage;
  its decision quality on real markets remains unvalidated.
- Do not interpret classification confidence as probability of profitable return without calibration.
- Chart images are an optional controlled experiment; numerical input is the proposed baseline.
- No claim that chart recognition reveals actual participant psychology.

## 5. Causal replay and data contract

Proposed starting universe: BTC/ETH/SOL spot for continuity; expand using eligibility known at the historical date, not today's survivors. Proposed paper balance: existing $1,000, plus capital-sensitivity runs. Binance data is a candidate, not a selected live venue. Confirm data access, terms, quality and costs before implementation.

At timestamp t:
1. Reveal only candles that have closed and whose data would have arrived by t.
2. Calculate indicators from this prefix, including only completed higher-timeframe bars.
3. Expose portfolio and matured journal entries as of t.
4. Record decision time and processing latency; do not fill a close-derived decision earlier than it could be submitted.
5. Advance execution, charge costs, then release outcomes only when observable.

Maintain deterministic ordering across pairs and apprentices. Reserve portfolio risk atomically for simultaneous pending entries. Journal keys prevent duplicate actions after retries.
Handle missing candles, stale feeds, delistings, timezone alignment and exchange filters explicitly. Store immutable data manifests and hashes.

Separate chronological training, validation and a sealed final holdout, with gaps appropriate to overlapping labels/24-hour positions. Select dates before experiments; use multiple market regimes where reliable data exists. Do not repeatedly tune on final-test feedback.

Two different evaluations:
- Frozen policy on unseen data measures transfer.
- Predeclared online-learning protocol on unseen data measures adaptation; it may use only outcomes already matured within that replay. No retrospective revisions of earlier trades.

Reset memory between independent runs; within a run it advances causally. Teachers and retrieved material cannot access future outcomes. LLM pretraining may contain historical events; historical replay alone cannot eliminate this contamination. Forward paper trading is essential.

## 6. Risk and order-management specification

Risk governor must be code, not an LLM vote. The teacher cannot alter its limits.

Proposed sizing:
quantity <= equity × 0.005 / (entry price - stop price + estimated per-unit round-trip costs).
Also cap by available spot cash, lot sizes, reserved cash and remaining portfolio risk.
This is planned loss under execution assumptions, not a guaranteed loss ceiling.
Reject nonfinite values, invalid stop distance, negative prices and missing protective exits.

- Sum conservative remaining loss-to-stop plus cost allowances across open positions and pending entries; never allow a new proposal above 2.5%.
- Five positions total across both apprentices; proposed default: one owner per symbol to prevent conflicting orders.
- Correlation exposure is reported explicitly; correlation policy is an unresolved engineering proposal, not permission to lower the agreed cap silently.
- Stop changes cannot increase risk beyond either cap. Never let the agent remove protection to improve simulated scores.
- Stops/take-profit orders execute independently of model availability.
- Mark equity including unrealized P&L and fees; persist peak and halt state across restart.
- At drawdown >=10%, reject new entries, cancel pending entries, alert, and continue protective exits. Proposed controlled liquidation policy must be finalized before operations; do not simply kill the process with positions unmanaged.
- No automatic reset of the breaker or hidden equity reset.
- Enforce 24-hour maximum holding independently of the agent.
- No leverage/borrowing; “scalping” does not waive any shared limit.

## 7. Learning, memory and curriculum

An LLM journal does not automatically retrain model weights. Define three permissions:
1. Memory: retrieve timestamped prior cases; distinguish observations from tentative explanations.
2. Weights: adjust bounded strategy-selection weights, not foundation-model parameters.
3. Rules: propose versioned setup/exit changes in an isolated research branch; no runtime source rewriting.

Each transition requires evidence against the previous frozen version, adequate sample size and a human-reviewed promotion. Keep rollback snapshots. Autonomous proposal generation is allowed by the intended design; unrestricted deployment is not.

Journal every opportunity considered, including abstentions and vetoes, not only winners.
Record setup, invalidation, expected horizon, risk, rationale, context, model inputs/output, cost, fills and outcome. Do not reward trade count or teacher approval. Separate rule compliance from empirical net performance.
Teacher lessons need supporting examples, counterexamples and uncertainty; one lucky win does not graduate a rule.

The first [foundation curriculum](../curriculum/FOUNDATIONS.md) was assembled on 2026-09-30
with five verified primary sources, six original lesson/exercise cards and a temporal-use
boundary. It is documentation only: no model ingestion, automated teacher or learning pass.
Further curriculum work remains assigned to the assistant:
- Start with market mechanics, order types, costs, position sizing and probability.
- Then operational definitions of a small number of setups (e.g. trend pullback or breakout).
- Finally regime awareness, abstention and evidence review.
- Prefer exchange mechanics documentation and rigorous research; books/courses are hypotheses to test.
- Record author, publication date, license/access, extracted claim and falsifiable rule.
- Do not ingest pirated material or let later historical examples leak into earlier replay.
- No paid course is selected or purchased by this plan.

## 8. Evaluation and advancement

User screening requirements: positive net profit, annualized Sharpe >1, drawdown <10%.
Proposed reporting convention: daily marked-to-market returns, stated risk-free assumption and sqrt(365) annualization for crypto; report sample length and uncertainty. Do not annualize per-trade returns as daily returns.

Report separately:
- Trading P&L after fees, spread, slippage and missed/partial fills.
- Operating P&L after inference, data and hosting costs.
- Drawdown, turnover, exposure, number of trades, loss tails and regime performance.
- Comparison with cash, buy-and-hold, the existing AlphaStrategy, a simple predeclared strategy and the same agent with memory/teacher disabled.

Track every experiment, including failures; adjust interpretation for repeated selection and correlated returns. Sharpe >1 alone is not statistical evidence. Freeze minimum evidence/sample rules before evaluation; do not invent a universal minimum trade count.
For waiting decisions, track opportunity coverage so “never trade” cannot claim success solely via low drawdown.

Promote only if improvement persists across untouched windows, reasonable parameter perturbations and execution-cost stress. If the adaptive system does not outperform its frozen version after costs, stop expanding it and report that result.
Paper trading cannot prove live profitability; live activation requires a separate explicit decision.

## 9. Work sequence and acceptance tests

Implementation authorized on 2026-09-23. The first increment implements a standalone causal replay boundary and stop-based risk/accounting, without changing the legacy Freqtrade strategy. P0 engine integration and dependency reproducibility remain explicit validation tasks.

First-increment acceptance: immutable prefix-only observations, signals filled no earlier than next candle open, gap-aware stops, stop-first ambiguous candles, fee/slippage accounting, shared five-position/2.5% risk caps, 0.5% sizing, 24h exits, latched drawdown halt, append-only run journal and a runnable CSV command. Tests use hand-calculated and adversarial fixtures; no synthetic fixture is performance evidence. Model/teacher integration follows once this boundary is verified.

| Milestone | Work | Acceptance evidence |
| --- | --- | --- |
| P0: setup validation | Reproduce baseline, pin environment, choose data/venue/model and budget; prove Freqtrade bridge | Test report including xfails; causal toy replay; documented engine decision |
| P1: replay/accounting | Dataset manifest, event clock, ledger, costs, fixed baselines | No future data reachable; hand-calculated fills/P&L; reproducible event order |
| P2: risk | Stop-based sizing, shared reservations, persistent breaker, 24h exits | Boundary tests at 0.5%, 2.5%, fifth/sixth positions and 10%; restart and simultaneous-entry cases |
| P3: apprentice | Structured decisions, abstention, journal, teacher and memory | Invalid output veto; model failure keeps exits alive; no future retrieval; duplicate retry safe |
| P4: learning evaluation | Staged permissions, frozen controls, chronological comparisons | Same-data controlled comparisons; isolated holdout; all candidate versions logged |
| P5: paper operations | Persistent worker, cost limits, alerts, recovery and reports | Forced restart restores exact state; reconciliation handles uncertain fills; budget exhaustion blocks new entries |
| P6: scalping track | Separate 1m apprentice, finer execution dataset, shared ledger | Cost/latency/partial-fill stress; joint portfolio tests; otherwise label results exploratory |
| P7: later swing | Separate proposal after intraday evaluation | New horizon and validation protocol reviewed before changes |

Critical tests also include: stops and targets touched inside the same candle; adverse gaps; teacher hindsight injection; stale higher-timeframe values; warmup leakage; corrupted checkpoints; symbol collisions; stop widening; tiny stops implying unaffordable notional; NaN prices; pending orders exceeding risk; provider timeouts and malformed responses.

Implemented file area: src/replay/. Future areas: src/agents/, src/memory/, src/evaluation/, src/execution/, corresponding tests, versioned experiment manifests and deployment config. Keep src/core/ and the existing baseline strategy.

### Offline replay usage

From the repository root:

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/python -m src.replay --csv candles.csv --journal run-001.sqlite
.venv/bin/ruff check .
.venv/bin/mypy .
.venv/bin/pytest -x --timeout=30
```

CSV header: `symbol,opened_at,open,high,low,close,volume`. Timestamps are integer UTC Unix seconds at candle **open**. All symbols must have one candle at every timestamp, at a uniform 300-second interval (or `--interval 60`). Duplicates, gaps and inconsistent symbol coverage are rejected. Supply only fully closed candles. Rows may be unsorted. No data download or exchange connection occurs.

Defaults: $1,000 simulated spot cash, 0.1% fee per side, 0.1% adverse slippage per fill. Override with `--balance`, `--fee`, `--slippage`. These are experiment assumptions, not venue quotes. Fresh runs require a new journal path. SQLite `events` stores ordered JSON payloads including input hash, settings, decisions, vetoes, fills, equity, complete UTC daily returns and result. Query with `SELECT payload FROM events ORDER BY sequence`.

Add `--stop-after 500` to pause after 500 additional candle batches; the CLI returns
`completed: false` without fabricating a final RESULT. Run the same command with `--resume`
and without `--stop-after` to finish. An interrupted run also resumes from the last committed
batch. Input data, settings, replay source, policy class source and policy version must match;
completed runs cannot resume. Preserve the journal and its persistent `.lock` sidecar, which
must not be deleted while any writer is open. Single-writer recovery uses local macOS/Linux
advisory locking. Non-checkpoint policies may still run fresh, but cannot pause or resume.

The comparison policy enters when a close exceeds the previous 20-bar high, proposes a 2% price stop and 4% target, and otherwise waits. It is a plumbing control, not a selected profitable strategy. `Policy.decide(Observation)` is the adapter boundary for a later apprentice. Observations contain immutable closed-candle prefixes and current portfolio state; local policy code is trusted, not sandboxed.

Execution ordering is open mark → gap/age exits → requested exits → risk-checked entries → intrabar protective exits → close mark → new decisions. Simultaneous entries are admitted sequentially in symbol order with updated cash/equity. Close-derived signals fill at the next open with costs; there is no same-close fill. Both stop and target touched means stop first. Protective gaps fill at the open. Final pending proposals expire; remaining positions stay marked to market and are reported explicitly.

Limits of this increment:

- Risk caps govern entry admission. Existing market exposure can exceed planned risk after price changes or gaps. Stops do not guarantee a maximum loss. The drawdown halt is latched for the run, blocks entries, and keeps protective exits active.
- Drawdown is sampled at opens/closes and executions; unknown intrabar portfolio paths are not reconstructed. Results can understate true drawdown. End equity includes unrealized positions and does not deduct hypothetical future liquidation fees.
- One position per symbol, long-only, no borrowing. No exchange lot sizes, minimum notionals, spread/queue/partial-fill models, measured decision latency or chart rendering yet. Zero additional decision latency is assumed.
- SQLite atomically checkpoints account, pending decisions, policy state, daily moments and risk halt with each candle batch. Replay refuses instance reuse and accidental journal overwrite. Recovery is offline only; external calls/orders still require deduplication/reconciliation. No unattended operation.
- Opt-in Jev candidate filtering supports budgeted provider calls with durable response records. No teacher, learned memory, curriculum retrieval, exit modification or separate scalping agent yet. A 60-second replay is exploratory and cannot validate scalping profitability.
- `daily_sharpe` uses complete UTC-day equity returns, zero risk-free rate and sqrt(365) annualization with sample standard deviation. It is null below 30 complete days or for zero variance, with an explicit reason. Partial days are excluded. There is no pass/fail profitability screen in this increment.
- Freqtrade remains a separate baseline. This independent replay avoids requiring stateful agent decisions inside its vectorized strategy pipeline; a paper-execution bridge is still unverified.
- Python 3.12 was used for local verification. NumPy is capped below 2.5 so its stubs parse with the project's Python 3.11 type-check target. Full dependency locking and Python 3.11 runtime verification remain P0 tasks.

P1/P2 are partial: simulation, admission enforcement and offline restart recovery exist;
realistic exchange execution remains unfinished. P3 includes a Jev breakout filter with durable
recorded responses; broader trader/teacher decisions remain pending. The first historical pilot
is recorded in `docs/research/BTC_WEEK_2024_06_PILOT.md`, with 11 unevaluated candidates after
the 100-attempt cap. Next work: predeclared full-coverage multi-window comparisons and a
teacher/memory adapter with causal retrieval tests.

## 10. Background operation and cost control

Persist a complete checkpoint, not only a text summary. Reconcile pending/filled orders on restart; never assume a timed-out submission failed. Halt new entries on stale data, bad state, invalid decisions, cost exhaustion or risk breach while maintaining existing protection.

Estimate inference volume before model selection: one year contains 105,120 five-minute steps or 525,600 one-minute steps per symbol, before teacher calls. Five symbols multiply these counts by five. Consider cheap deterministic screening/batching, but measure whether it suppresses opportunities. Record cost per simulated day and per paper day; require a hard approved spending ceiling.

Weekly review is an eventual operating goal after stabilization, not a guarantee. Reports should include performance versus controls, costs, risk violations, candidate changes, data gaps and failures. Urgent faults must alert separately. Hosting, channel, budget and unattended execution need explicit setup authorization.

## 11. Remaining decisions and handoff

No additional conceptual questionnaire is needed. Before spending or launching, resolve:
- Simulated capital and intended eventual capital (not yet selected by the user).
- Venue/data availability and permitted use.
- TypeSafe credentials and a USD 3/month AI ceiling are now supplied (2026-09-30).
  Other provider credentials, host and alert destination remain unresolved.
- Whether to stage the scalping milestone later; it remains requested scope.
- Exact evaluation dates, evidence thresholds and emergency liquidation policy.

First action for the next agent: reproduce the checks and continue the explicitly unfinished milestones above. Implementation is authorized; the April task list remains superseded. Resolve credentials and spending limits before paid model integration.

## 12. Documentation organization and verification

Root README is the entry point. AGENTS.md and CLAUDE.md route agents here. docs/README.md is the documentation index. Legacy status paths remain small pointers to avoid broken entry points. April setup history is preserved under docs/archive/ with a superseded label; its old path redirects there. Its percentages and checkmarks describe the old scope only.

Inherited framework rules/guides may mention unrelated products or tools. Root agent guidance resolves current project commands and scope; broad framework migration is deferred. Existing source, tests, config and hook scripts are preserved.

The initial documentation handoff used link/path and scope checks. Implementation verification uses lint, strict typing and the test suite, including hand-calculated accounting and adversarial simulation cases. Synthetic fixtures are correctness checks, not trading performance evidence. No deployment or exchange trading process is launched.

## 13. Sources and limitations

- [Freqtrade backtesting assumptions](https://www.freqtrade.io/en/stable/backtesting/#assumptions-made-by-backtesting): standard fill assumptions and candle limitations.
- [Freqtrade lookahead analysis](https://www.freqtrade.io/en/stable/lookahead-analysis/): useful diagnostic, not a complete proof of causality.
- [Freqtrade callbacks](https://www.freqtrade.io/en/stable/strategy-callbacks/): integration surface to validate against the pinned version.
- [NautilusTrader](https://github.com/nautechsystems/nautilus_trader): candidate event-driven alternative.
- [TypeSafe Jev introduction](https://typesafe.ai/blog/introducing-system-one-models-and-jev): vendor capability claims; not trading validation.
- [TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html): chronological splitting concept, not a complete financial evaluation protocol.

Source links support platform context. They do not establish that the apprentice will earn money. Curriculum selection and engine integration remain future work.

## Progress log

### 2026-09-30 PM continuation: foundation teaching material

**Status: COMPLETE for the initial source pack; teacher/memory implementation remains pending.**
Documentation-only increment under existing authorization; no strategy change, paid call,
dataset use, deployment or new service. Plan: verify sources → create original lessons and
tests-of-understanding → document availability/anti-leakage limits → synchronize status.

Created `docs/curriculum/FOUNDATIONS.md` with exchange constraints, costs, account risk,
causal information, operational setup definitions and evidence/overfitting. Five primary
sources were opened and checked; publication dates are recorded where established and
unknowns remain explicit. Sources are linked rather than bulk-copied; access is not treated
as a redistribution license. Original arithmetic exercises have independently checked answers.

The source pack is not silently backdated into 2024 research. It separates source-supported
mechanics from project hypotheses and retains the approved 0.5%/2.5% risk limits even when
source examples differ. Its proposed teacher handoff includes available-at time, counterexamples,
version provenance and separate quiz answer keys. These are requirements for implementation,
not claims that retrieval controls or autonomous learning already exist.

PM order: (1) causal teacher/memory foundation with recorded-response tests; (2) predeclared
full-coverage frozen-versus-learning comparisons; (3) forward paper operation and cockpit
controls/hosting. Daniel need not supply material or increase budget now. Hosting account
access and concrete promotion decisions can be requested when those deliverables are ready.

### 2026-09-30 continuation: first fixed historical comparison

**Status: IMPLEMENTED. Tier: Standard — local dataset import/reporting using existing paid
inference and durable replay boundaries.** Continuation authorized by Daniel. No deployment,
worker or real trades. No parameter/prompt tuning from this pilot.

**1. Purpose:** run the frozen breakout baseline and Jev filter on identical real historical
data, publish actual results to the local cockpit, and expose any insufficient coverage.

**2. Predeclared protocol (before viewing outcomes):** BTC/USDT spot, five-minute candles,
2024-06-01 00:00 UTC inclusive to 2024-06-08 00:00 UTC exclusive; $1,000 simulated cash;
0.1% fee per side and 0.1% adverse slippage per fill, current unchanged risk governor,
2% stop/4% target and 20-bar breakout. Both policies start empty with the same 21-bar warmup.
This period overlaps old baseline research and is explicitly development data, not sealed
validation or holdout. Frozen implementation starts at `0c84bc1`; only importer/reporting
changes are allowed before these runs. No learning/teacher is enabled. Baseline has no AI;
Jev uses `jev-1.13.0`, max 100 attempts (maximum $0.30 reservation, inside USD 3/month).
If API/limit errors occur, label comparison degraded and do not claim full Jev evaluation.
Do not extend the window or change parameters to improve outcomes. Report open positions
without fictional liquidation, daily sample length and unavailable Sharpe below 30 days.
Trading P&L includes fees/slippage. Report AI spending separately in USD (trading unit USDT),
reconcile all this run's successful calls to the budget delta and disclose unresolved calls.
Cash reference is zero return; buy-and-hold/other regimes remain later predeclared studies.

Source: existing Binance monthly ZIP, verified against its official SHA-256 CHECKSUM before
use. [Official format/checksum documentation](https://github.com/binance/binance-public-data)
defines spot klines and the 2025 switch from millisecond to microsecond timestamps. Import
only the selected period; validate exact contiguous 5m coverage, OHLCV and close times. No
interpolation, padding or future candles. Preserve raw data; new CSV + provenance manifest.

UX: existing saved-results page gains comparable-run summary rows and explicit model-cost/error
counts. Reader sees performance, sample/coverage limits and source evidence in one place.
No new controls or simulated live status. Missing provenance prevents automatic comparison.

**3. Tasks (5; re-plan above 7):**
- [x] Test-first checksum-verified Binance import; missing/duplicate/misaligned bars reject.
- [x] Test-first matched-input comparison with costs/error visibility; unmatched runs separate.
- [x] Verify source and freeze CSV/provenance; run baseline and bounded Jev once each.
- [x] Reconcile responses/spending; generate cockpit and concise permanent experiment record.
- [x] Full lint/type/tests; commit and update existing draft PR with actual results/limits.

**4. Files:** `src/replay/dataset.py`, `src/cockpit/report.py`/template, focused tests,
README/status/this plan and a saved experiment report. Generated data/journals stay ignored.
Existing risk code, Jev prompt, budget and response persistence remain unchanged.

**5. Verification/failures:** checksum/format fixtures (ms/us), full coverage and read-only
source preservation; cockpit matches only same input hash, dates and execution settings.
Legacy unknown cost stays unavailable; policy errors are visible. Real runs execute serially,
within the existing budget guard; no retry of ambiguous calls. A stopped run can resume.
Importer reads at most 64 MiB uncompressed, writes only new paths, and records content hashes.
Existing project test suite is the regression gate; visual browser restriction remains respected.

**6. Rollback/limits:** no destructive migration or new service; preserve all experiment files.
One asset/week has insufficient evidence for profitability or learning; pretraining contamination,
coarse candle execution, zero modeled decision latency and open-position marks remain limitations.
Output after AI cost is not mislabeled in USDT without an explicit FX assumption. Research may
show no advantage; report it without adjusting the test or interpreting abstention as learning.

**Actual evidence:** [pilot report](../research/BTC_WEEK_2024_06_PILOT.md). Baseline +0.062385%
marked return (7 closed / 1 open); capped Jev +0.178587% (2 closed / 0 open), with 98 WAIT,
2 ENTER and 11 unevaluated candidates after the cap. No provider failures or unresolved
reservations. All 100 response costs reconcile to the USD 0.009907590 budget increase.
No cap/window/prompt change or rerun after viewing outcomes. Seven full days is below the
Sharpe reporting threshold. Cockpit prominently labels the degraded comparison; no promotion.
Verification: ruff clean; strict mypy clean across 51 files; **151 passed / 17 pre-existing
expected failures**. Generated HTML content and documentation links checked. Visual browser
verification remains pending. Results/implementation published to the existing draft PR.

### 2026-09-30 continuation: Jev replay decisions with durable responses

**Status: IMPLEMENTED. Tier: Full (durable external side effects).** Daniel authorized
continued implementation; no further input is needed. Uses the existing plan skill and
approved USD 3/month guard. One bounded synthetic integration check may use a real model;
it is plumbing evidence only. No market evaluation, hosting or worker is started.

**1. Purpose:** connect Jev to a narrow, observable simulated trading decision without
duplicate paid calls on replay recovery. This is an experimental candidate filter, not the
teacher, learned memory or complete autonomous trader.

**2. Design:** opt-in `--policy jev` keeps the default fixed baseline unchanged. The same
20-bar breakout creates a candidate; Jev chooses ENTER or WAIT using only the last 21 closed
OHLCV bars, current portfolio and a fixed prompt. Stop/target remain fixed at 2%/4%; sizing,
cash, position and drawdown limits remain deterministic. Existing positions retain independent
protective exits. No call during warmup, no candidate, halt or full portfolio. Default 20 model
attempts per run, configurable 1–100, plus the shared USD 3/month cap. Limits count attempts,
not just successes. Exhaustion and provider errors are visible POLICY_ERROR events.

A per-run SQLite response file commits a request identity and pending marker BEFORE network
I/O in a separate transaction from candle events. A successful validated response is saved
before it can influence a proposal. Retrying the exact request reuses the saved response;
pending/failed rows never resubmit. A crash after provider success but before saving may lose
that answer and force abstention; this deliberate cost is preferable to duplicate spending.
The cache identity is bound into policy checkpoints. Missing/replaced/corrupt stores fail closed.
Prompt/model/source/attempt-limit identity is bound to recovery. Successful MODEL_CHOICE
events record model, chosen option, confidence, token count, accounted cost and receipt key;
these are model preferences, not calibrated profit probabilities or generated explanations.

**3. Tasks/tests (6-task scope; re-plan above 9):**

| # | Task | Failing acceptance test | Status |
| --- | --- | --- | --- |
| 0 | Response/policy contract tests | duplicate and uncertain attempts, causal input, fail-closed behavior | [x] |
| 1 | Durable per-run responses | crash/reopen reuse; mismatch/corruption/pending/limit rejection before network | [x] |
| 2 | Jev candidate policy | only closed prefix submitted; ENTER/WAIT mapping; no risk override; unchanged protective exits | [x] |
| 3 | Opt-in CLI and restart binding | resumed Jev replay reuses saved calls and rejects missing/replaced response store | [x] |
| 4 | Evidence in existing cockpit | model choice and actual known inference cost visible in decision records | [x] |
| 5 | Verify and publish | full lint/type/test gate; bounded synthetic integration; docs and draft PR updated | [x] |

**4. Files/blast radius:** new `src/agents/responses.py` and `src/agents/policy.py`, replay
CLI selection, cockpit record formatting, focused tests and documentation. No modification
to risk arithmetic or budget settlement rules. SQLite schema is local, not Supabase/RLS.

**5. Verification:** test-first pytest fixtures with mocked HTTP and real SQLite transactions;
restart after a recorded response but before candle commit, pending ambiguity, request mismatch,
corruption and run limits. Verify model failures keep stops active and requests contain no future
candles. CLI integration uses recorded HTTP; a separate single synthetic live request can check
credentials through the guarded connector. Regression gate remains ruff, strict mypy and pytest.
No browser workaround; visual review stays pending. UI uses existing decision rows, no new flow.

**6. Failure/scalability:** primary-key request lookup, <=100 attempts per run, bounded 21-bar
payload, one SQLite connection, no in-memory response history. Pending claim uses BEGIN
IMMEDIATE; simultaneous same-request calls cannot both claim. Replay journal owns single-writer
execution. Network I/O never holds the response DB transaction. SQLite FULL durability.
No retry after uncertain network/commit failure. Worst-case network latency remains the connector's
bounded request timeout per eligible candidate; this is offline simulation, not real-time execution.
Independent response and candle commits deliberately provide at-most-once attempt, not atomic
exactly-once provider execution. Local disk access/transactions verified directly, not cloud MCPs.

**7. Security/rollback:** store observations and sanitized validated responses only; never
credentials, headers or raw exception text. Safe errors report why a candidate was vetoed.
Response file permissions 0600; keep it with the journal and preserve it on rollback. Switch
new runs back to baseline to disable model decisions; do not rewrite in-progress contracts.
No auth/service/dependency changes. Existing framework landmines are mostly unrelated web
patterns; applicable checks are state validation, error visibility, bounded work and causal data.

**8. Limits:** changed code intentionally refuses old recovery contracts; start a new experiment
or use the original revision. Local files/code are trusted, not tamper-proof. A lost store cannot
be recreated to resume. Known successful inference costs exclude unresolved reservations; the
shared budget ledger is the authoritative spending cap. No profitability, learning, exit-selection,
scalping execution or decision-latency claim follows from this integration.

**Evidence:** the initial tests failed because the response/policy modules were missing; CLI
test failed before wiring the command. Integration tests cover ENTER/WAIT, next-open risk-checked
fills, prefix-only requests, exits during provider failure, recorded-answer recovery after candle
rollback and commit failure after provider success. A single real call on explicitly synthetic
OHLCV returned WAIT from `jev-1.13.0`, with 1,885 input tokens and $0.000079170 cost. Total
accounted monthly spending is $0.000093324, with no unresolved reservations. The synthetic
journal stays under ignored `user_data/ai/` and is excluded from market-results reporting.
Final gate: ruff clean, strict mypy clean across 49 source files, **139 passed / 17 pre-existing
expected failures**. Published to the existing draft feature PR; no merge or deployment.

### 2026-09-30 continuation: replay recovery and daily measurement

Daniel authorized continued implementation without further input. **Status: IMPLEMENTED.
Tier: Full — persistent account state and risk protection.** No real trades, paid inference,
unseen-market experiment, deployment or unattended worker in this increment.

**1. Purpose:** resume an interrupted offline experiment without resetting its money, pending
decisions, positions, risk halt or daily performance record. Measure results consistently
before adding an adaptive trader.

**2. Design:** keep the existing replay API and candle execution order. Add opt-in `--resume`
and `--stop-after` (candle batches) to the baseline CLI. A checkpoint-capable policy provides
a version ID plus JSON state save/restore methods. Checkpoints bind exact normalized candle
data, settings, policy ID and policy class source hash; mismatches fail before decisions.
Journal events and the matching account/policy checkpoint commit atomically per candle batch.
An OS advisory file lock permits one replay writer; completed journals cannot resume.
Checkpoints are checksummed JSON, never pickle. Restarts reconstruct causal lookback from the
verified dataset, then continue with the pending proposals from the last committed close.
Crashes during a batch leave that batch uncommitted; its simulated fills/decisions are replayed.
This does not promise exactly-once external model calls or real exchange orders.

Daily convention: daily UTC marked-to-market simple returns, zero risk-free rate,
`sqrt(365) * mean / sample_std(ddof=1)`. Count only full midnight-to-midnight intervals;
exclude leading/trailing partial days and include zero-return days. At least 30 complete
days are required to display descriptive Sharpe; zero variance produces an explicit unavailable
reason, never a fabricated zero/infinite score. This is a reporting threshold, not a profitability
or strategy-promotion gate. Preserve the streaming daily accumulator in every checkpoint.

**3. Tasks / tests (8-task scope; re-plan above 12):**

| # | Task | Failing acceptance test | Status |
| --- | --- | --- | --- |
| 1 | Daily-metric contract tests | hand-calculated returns, partial UTC days, zero variance, finite input and sample count | [x] |
| 2 | Streaming daily metrics | exact full-day returns and serializable accumulator parity | [x] |
| 3 | Recovery contract tests | interrupted/resumed result and event parity; pending entries, risk halt and policy state retained | [x] |
| 4 | Atomic journal/checkpoint and exclusive writer | rollback leaves prior checkpoint/events intact; corruption/concurrent writer/completed resume rejected | [x] |
| 5 | Bind replay state to data/settings/policy | changed data, cost settings or policy identity fail before policy calls | [x] |
| 6 | CLI resume and bounded pause | CLI pause → fresh process resume = uninterrupted result; missing journal does not create a file | [x] |
| 7 | Report daily metrics in cockpit | actual sample count/reason shown; old archives remain honestly unavailable | [x] |
| 8 | Regression gate, documentation and feature PR | ruff/mypy/pytest pass; no API calls, safety/config changes or fake performance claims | [x] |

**4. Files / blast radius:** `src/replay/{engine,journal,__main__,performance}.py`,
`src/cockpit/{report.py,template.html}`, focused replay/performance/cockpit tests, README and status pointers.
Risk is high for replay accounting and checkpoint restoration; existing hand-calculated risk,
gap, fee, max-age, malformed policy and halt tests must remain green.

**5. Test plan:** test-first pure statistical fixtures and restart integration against independent
uninterrupted runs. Inject a crash after event insertion before checkpoint commit; assert no
duplicate/missing fills. Tamper with state checksum, dataset, settings and policy. Verify halt
and peak persist even when prices recover. Test 0-trade days, 29/30-day boundaries, partial
days, inconsistent timestamps and serialized daily-state restoration. CLI integration is the
Python E2E; cockpit assertions check actual rendered metrics without calling an external browser.

**6. Failure/scalability:** checkpoints overwrite one small state row, not full history. Buffered
lookback and daily running moments are bounded. Dataset remains the existing in-memory replay
input; no extra remote calls or DB service. SQLite transactions use FULL durability and rollback
on exceptions; file lock held across replay lifetime. Disk/full/corrupt input fails explicitly.
Future network policy calls may repeat after an uncommitted batch and need durable response
deduplication before they are enabled. Closed experiments never reopen for learning.

**7. Security / rollback:** read JSON only; validate types, finiteness, counts, pending actions,
position shape and accounting against the last closed candle. Preserve all source journals.
Legacy completed journals remain readable; resumability requires the new checkpoint schema.
Rollback code leaves journals/checkpoints intact for forward-compatible recovery; no resets.
No new authentication, hosting or paid dependencies. Secrets never enter checkpoint state.

**8. Enforcement limits:** this protects offline simulated accounting, not external side effects.
Policy implementations remain trusted local code and must explicitly serialize all their state.
Checksums detect corruption, not an authorized attacker rewriting both data and checksums.
Intrabar drawdown and execution realism remain limited. Daily Sharpe cannot establish learned
edge; teacher/memory, controls, comparison studies and forward paper trading remain unfinished.

**Verification evidence (2026-09-30):** 124 tests passed and 17 pre-existing sensory tests
remain expected failures; ruff and strict mypy (45 files) passed. Focused tests first failed
on missing recovery/daily support. Review added a failing multi-symbol ordering case: JSON
restoration reordered positions, changing exit event order. Canonical symbol ordering now
preserves both accounting and exact event parity. CLI tests resume in a fresh process;
injected fill interruption rolls back without duplicate execution. Daily results are checked
against independently calculated sample statistics, including overflow and unavailable scores.
No external inference, real-market experiment, hosting or trading was run in this increment.
The local cockpit is regenerated from the two existing April archives only; daily statistics
for those old archives remain honestly unreported. Browser visual verification is still pending.

### 2026-09-30: Jev access and USD 3/month AI budget

Daniel saved the TypeSafe token locally and approved USD 3 per month for AI inference.
He prefers an online cockpit with free hosting. The token was accepted by TypeSafe's
read-only `/v1/models` endpoint (HTTP 200); it was not printed or committed.

**Increment: budgeted Jev connector — implemented and verified (2026-09-30). Tier: Full (persistent spending state).**
This is a connection and accounting boundary, not a finished trader, teacher or learning loop.
The existing offline replay and risk limits remain unchanged. No historical validation or
holdout is consumed. No deployment or unattended process is started.

1. **Purpose:** prevent local AI inference from exceeding the approved monthly allowance.
2. **Design:** one shared SQLite ledger at `user_data/ai/budget.sqlite`, UTC calendar months,
   integer nano-USD accounting, USD 3 cap. Initialize explicitly once; an absent/corrupt ledger
   subsequently fails closed. Each call reserves USD 0.003 in a committed `BEGIN IMMEDIATE`
   transaction before network I/O. Concurrent processes share that ledger. Successful calls
   settle to reported input tokens × USD 0.042/million. Failed/ambiguous calls keep the full
   reservation, with no automatic retries or redirects. Pin `jev-1.13.0`; pricing verified
   2026-09-30 and expires for new calls after 2026-10-31 until reviewed. Published maximum
   context is 64k tokens, so USD 0.003 covers 65,536 tokens at the verified rate. Output is free.
   Unexpected model/usage or invalid answers fail closed. Spending through other applications
   is outside this ledger; future trader/teacher providers must join the same guard before use.
3. **Tasks / tests:**
   - [x] Write failing tests for cap boundaries, concurrency, restart, UTC rollover, missing
     ledger, retained timeout reservations, strict response validation and secret redaction.
   - [x] Implement durable shared accounting and a narrow Jev Choice connector using the
     existing `requests` and `python-dotenv` dependencies.
   - [x] Add explicit budget initialization/status/connection-check CLI; run one harmless live
     inference after the tests pass, recording model, input tokens and accounted cost only.
   - [x] Update docs and rerun the full quality gate. Publish this increment to the existing feature PR.
   Scope guard: four tasks; re-plan above six. No trading policy adapter in this increment.
4. **Files:** `src/agents/budget.py`, `src/agents/jev.py`, package initializer,
   `tests/test_ai_budget.py`, `tests/test_jev.py`, `.env.example`, `.gitignore`, README,
   AGENTS and this plan. Sensitive ledger is ignored; `.env.local` stays ignored and private.
5. **Verification:** hand-calculated costs, contention at the last reservation, second process
   seeing previous spending, no network request after cap/expired pricing, corrupt responses
   do not escape as decisions, no key/request headers in errors, CLI smoke uses no market data.
   Integration tests use recorded-response fixtures. Full ruff/mypy/pytest gate required.
6. **Failure/scalability:** transaction lock only around reservations/settlement; network I/O
   outside locks; fixed request/response bounds and finite timeouts; no retries. SQLite failure
   blocks calls. Small inference workload at USD 3/month bounds ledger growth; no DB service,
   schema-wide migration, N+1 remote calls or connection pool required.
7. **Security/rollback:** token read only from process environment or local `.env.local`, sent
   only to the fixed HTTPS TypeSafe endpoint; transport exceptions are sanitized. Rollback
   disables connector code but preserves ledger and reservations. Budget cap cannot be raised
   by runtime flags. Normal code/ledger editing is trusted; this is not account-level billing
   enforcement. Paid work in other tools is not covered.
8. **Limits:** invoice/tax adjustments and provider price changes are not under local control;
   expiry forces periodic price review. Historical model confidence is not trading calibration.
   Jev integration into the replay policy, teacher/memory and authenticated online cockpit
   remain next milestones. Accepted temporary limitation: unresolved requests consume the
   full reservation, which may stop calls early but must never cause optimistic overspending.

Source: [TypeSafe model pricing and context limits](https://docs.typesafe.ai/models).

Evidence: 15 new tests first failed because the connector package did not exist, then passed
with implementation. Full gate: ruff clean; mypy clean across 42 files; **97 passed / 17
pre-existing expected failures**. A single harmless real inference returned `paper` from
`jev-1.13.0`, with 337 input tokens and USD 0.000014154 accounted cost. No unresolved cost
reservation remains. The request contained a paper-mode connection-check sentence, not market
history or private trading evidence. Only sanitized metadata was displayed. This verifies
connectivity and billing plumbing; it does not connect Jev to the trading loop.

### 2026-09-29 continuation: one cockpit and measured learning

Daniel authorized updating the local checkout and continuing implementation, with one cockpit
for performance and agent control. GitHub PR #2 (`ca96c01`) is the current implementation
baseline; it includes PR #1's handoff. Both PRs remain open. The previous local
`codex/risk-execution-integration` branch and its uncommitted work were preserved in a named
Git stash before switching to `codex/apprentice-cockpit`. Do not apply that older architecture
over this plan. No GitHub merge was performed.

**Current increment: results cockpit — IMPLEMENTED; browser visual verification pending.** Standard tier: offline,
read-only presentation of saved results, no server-side controls, authentication, paid calls,
trading or database writes. This implements the report surface of the authorized direction;
it does not claim completion of paper operations or the AI brain.

**UX brief:** Daniel should open one page and immediately see whether an agent is connected,
what actually ran, how it performed, and whether learning has been measured. Desktop-first,
responsive for future phone access; local versus hosted preference is being confirmed.
Journey: open cockpit → inspect saved run → inspect performance and decision record.
Empty state says no runs; incomplete/error runs are never presented as successful results.
This is a dated snapshot, not a live monitor. Reading it offline requires no external assets.

```text
NEURALEDGE                             Saved-results snapshot / generated time
Agent: not connected   Jev: not connected   Learning: not evaluated
Results | What comes next
Saved run [policy / source / historical interval]
Net return | Ending equity | Max drawdown | Closed trades | Open positions
Recorded equity chart (only when actual equity samples exist)
Decision / trade record + explicit sample and cost limitations
```

Heuristics: visibility via snapshot date and explicit connection state; forgiveness via
read-only operation; minimalism via one page; consistent metric definitions per source;
responsive layout; actionable import errors; results immediately visible; plain-language
labels. No existing UI/components to reuse. Controls and hosting remain a later increment,
not decorative buttons that imply functioning operations.

**Implementation and tests:**

| Task | Acceptance / failing test | Status |
| --- | --- | --- |
| Import saved Freqtrade ZIP results and replay SQLite journals read-only | Hand-calculated return/win rate; unfinished journal rejected; files unchanged | [x] |
| Render local cockpit with genuine results and evidence limits | HTML escapes journal text; unknown metrics absent; no credentials/config embedded; no invented equity curve | [x] |
| Provide one-command generation and actual saved baseline results | CLI created offline HTML containing both existing April result archives; file panel requested | [x] |
| Verify inherited environment and synchronize status entry points | ruff/mypy/pytest pass; status pointers corrected; visual check blocked by browser file-URL policy | [~] |

Scope: four tasks; re-plan if more than six. Files: `src/cockpit/` (new read-only reporting),
`tests/test_cockpit.py`, README and this reference. Correct the existing TA-Lib typing
incompatibility only if needed to reproduce the inherited gate; baseline strategy behavior
must remain identical. No source dependency added.

Failure modes: missing/corrupt/incomplete results fail explicitly; no zero-score fallback.
SQLite is opened with `mode=ro`, bounded-size JSON archive members are read without extraction,
and user-controlled text is HTML-escaped. Output excludes saved configuration/API credentials.
Repeated runs are not interpreted as learning; Freqtrade trade exits cannot supply an honest
mark-to-market equity curve. Large replay histories use bounded chart/detail samples with
sampling disclosed. Source archives/journals remain unchanged. Rollback removes the report
package/generated HTML and leaves trading evidence intact. No DB service/RLS applies.

**Next implementation sequence:** finish checkpoint/recovery and daily evaluation; integrate
trader and Jev behind recorded-response tests; add teacher and timestamped memory; compare
learning-enabled versus frozen runs after trading and AI costs; add cockpit run/pause controls
and hosted access once persistent state and authentication are ready. Proposed lessons can be
generated daily; promotion requires measured evidence and human review. Improvement is a
hypothesis, not a promised daily increase in profit. TypeSafe access, spending ceiling, host,
and alerts must be resolved before paid inference or unattended deployment.

Verification: the new cockpit tests first failed on the absent module, then passed after
implementation. Full gate: ruff clean; mypy clean (37 files); 82 passed / 17 pre-existing
expected failures. Four targeted TA-Lib `attr-defined` suppressions restore compatibility
with the installed dynamic abstract API without altering indicator behavior. The lower
test count than the preserved older branch reflects different work, not deletion of its
evidence. This branch builds on the 75-pass/17-xfail GitHub apprentice baseline.

Generated artifact: `user_data/cockpit/index.html` (ignored local output). The Codex file
panel open request was queued; an automated browser visit to the file URL was rejected by
browser security policy. No alternate browser/server workaround was attempted. Visual
verification remains outstanding; HTML/content correctness is covered by automated tests.
The cockpit is a first reporting increment, not the requested finished operational cockpit.

2026-09-20: Repository statically reviewed; user decisions consolidated; stale plan superseded; documentation handoff prepared. Apprentice implementation remains not started.

2026-09-23: User authorized implementation. Added offline causal replay, immutable observations, next-open fills, stop-based sizing, five-position admission, fee/slippage accounting, gap/age exits, latched drawdown halt, exclusive SQLite journal and CSV CLI. Verification: ruff passed; strict mypy passed across 33 files; pytest **75 passed, 17 expected failures** (pre-existing sensory stubs), including 17 new replay tests and a CLI-to-journal integration test. No real historical performance experiment or model call was run. NumPy compatibility cap added; four obsolete TA-Lib type suppressions removed without changing baseline behavior. P0/P1/P2 remain partial; next steps and limitations are recorded above.
