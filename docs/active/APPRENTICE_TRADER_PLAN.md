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
| Current authorization | Implementation and local verification; AI inference capped at USD 3/month (2026-09-30); private Vercel cockpit preview authorized; no unattended worker or real trading |

The proposed 1.5% aggregate cap was NOT accepted; preserve 2.5%.
The recommendation to defer scalping was NOT accepted as a scope deletion. Retain it as a separate milestone requiring better execution evidence.
Live capital, shorting, leverage, new paid services beyond the USD 3/month AI allowance, and unattended workers are not authorized. Daniel authorized hosting the saved-results cockpit on his existing Vercel account on 2026-09-30; this does not authorize production/main promotion or trading services.

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
boundary. Separate original runtime cards are now wired to opt-in memory, available only
from 2026-09-30 UTC. The evidence teacher is deterministic; no competency or learning pass.
Further curriculum work remains assigned to the assistant:
- Start with market mechanics, order types, costs, position sizing and probability.
- Then operational definitions of a small number of setups (e.g. trend pullback or breakout).
- Finally regime awareness, abstention and evidence review.
- Prefer exchange mechanics documentation and rigorous research; books/courses are hypotheses to test.
- Record author, publication date, license/access, extracted claim and falsifiable rule.
- Do not ingest pirated material or let later historical examples leak into earlier replay.
- No paid course is selected or purchased by this plan.

### 2026-09-30 requirement: recurring patterns and market context

Daniel explicitly wants the apprentice to recognize recurring market patterns, including
possible multi-year Bitcoin cycles. Record the proposed bull-market interpretation as a
hypothesis, not a confirmed regime or a required trading bias. **Status: accepted product
requirement; daily/weekly context v1 implemented separately; pattern retrieval and
market-cycle evaluation pending.**

Frozen Jev still sees 21 closed base-interval bars (105 minutes at 5m); memory-only adds
recent same-run trade facts. A separate opt-in `jev-context` now supplies closed daily/weekly
OHLCV history. Its first [comparison screen](../research/CONTEXT_SCREEN_V1.md) is complete:
always waiting avoided memory-only losses in three falling periods but matched cash. It does not retrieve chart
analogues or substantiate a four-year-cycle interpretation.

Direction (daily/weekly arithmetic context implemented in the increment below; remaining
pattern-library and performance work still require separate specification):
- Add timestamped daily/weekly price-volume context alongside the intraday decision window.
  Keep the agreed OHLCV-only inputs. Higher-timeframe candles must be completely closed at
  the decision cutoff; insufficient history yields an explicit unknown state.
- Define versioned trend, range and volatility descriptors using trailing data only. Normalize
  using prior observations, not the whole dataset. A calendar interval alone cannot declare
  a bull market. Similarity is not a calibrated probability or a trading permission.
- Retrieve bounded earlier pattern examples, including failures and nonmatches, with their
  dates, evidence and disconfirming conditions. Separate pattern shape from subsequent outcome;
  retrieve an outcome only after its full evaluation horizon has elapsed. No overlapping
  future labels, later peaks/troughs or unrestricted full-history search in model input.
- Keep current independent runs isolated. Any future historical pattern library requires a
  separately versioned training boundary and immutable provenance; it must not import prior
  holdout outcomes into a later comparison. No new cross-run import is silently enabled.
- First complete the predeclared memory-on/frozen comparison. Add context as a separate
  controlled variant, with identical dates, data and execution costs; compare to cash and
  buy-and-hold as well as the simple strategy. Include rising, falling and sideways windows
  so rising-market exposure cannot masquerade as learning. Select rules and sample requirements
  before examining evaluation results, preserve all trials, and ensure full candidate coverage.
- A future cockpit view should show the dated market-state hypothesis, earlier analogues,
  counterexamples and invalidation conditions. Follow UX design before this user-facing work;
  no invented confidence percentage or growth score. Risk limits stay independent.

Research context checked on 2026-09-30: [Coinbase's March 13, 2024 analysis](https://www.coinbase.com/en-de/institutional/research-insights/research/monthly-outlook/monthly-outlook-mar-2024)
cautions that few prior halvings and changing market structure limit generalization.
[Fidelity's February 24, 2026 analysis](https://fidelitydigitalassets.com/research-and-insights/bitcoins-four-year-cycle-over)
examines divergence from past cycles. Neither establishes today's market regime or validates
our pattern model. These are design references, not runtime lessons to backdate into a replay.
No present bull-market classification was calculated in this review.

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
- Opt-in Jev candidate filtering supports budgeted provider calls with durable response records. Opt-in causal same-run memory and a deterministic evidence teacher are implemented. No generative teacher, measured learning improvement, exit modification or separate scalping agent yet. A 60-second replay is exploratory and cannot validate scalping profitability.
- `daily_sharpe` uses complete UTC-day equity returns, zero risk-free rate and sqrt(365) annualization with sample standard deviation. It is null below 30 complete days or for zero variance, with an explicit reason. Partial days are excluded. There is no pass/fail profitability screen in this increment.
- Freqtrade remains a separate baseline. This independent replay avoids requiring stateful agent decisions inside its vectorized strategy pipeline; a paper-execution bridge is still unverified.
- Python 3.12 was used for local verification. NumPy is capped below 2.5 so its stubs parse with the project's Python 3.11 type-check target. Full dependency locking and Python 3.11 runtime verification remain P0 tasks.

P1/P2 are partial: simulation, admission enforcement and offline restart recovery exist;
realistic exchange execution remains unfinished. P3 includes a Jev breakout filter with durable
recorded responses and opt-in causal memory; broader trader/generative teacher decisions remain pending. The first historical pilot
is recorded in `docs/research/BTC_WEEK_2024_06_PILOT.md`, with 11 unevaluated candidates after
the 100-attempt cap. Teacher/memory recovery and causal tests now pass. The first
[three-window memory screen](../research/MEMORY_SCREEN_V1.md) is complete with full coverage
but inconclusive learning evidence. Causal daily/weekly context v1 is now implemented and
correctness-tested. Its first real context screen matched cash by abstaining throughout.
Next: broader market coverage and missed-opportunity evaluation under a fresh protocol,
recurring-pattern design, then forward paper.

## 10. Background operation and cost control

Persist a complete checkpoint, not only a text summary. Reconcile pending/filled orders on restart; never assume a timed-out submission failed. Halt new entries on stale data, bad state, invalid decisions, cost exhaustion or risk breach while maintaining existing protection.

Estimate inference volume before model selection: one year contains 105,120 five-minute steps or 525,600 one-minute steps per symbol, before teacher calls. Five symbols multiply these counts by five. Consider cheap deterministic screening/batching, but measure whether it suppresses opportunities. Record cost per simulated day and per paper day; require a hard approved spending ceiling.

Weekly review is an eventual operating goal after stabilization, not a guarantee. Reports should include performance versus controls, costs, risk violations, candidate changes, data gaps and failures. Urgent faults must alert separately. Hosting, channel, budget and unattended execution need explicit setup authorization.

## 11. Remaining decisions and handoff

No additional conceptual questionnaire is needed. Before spending or launching, resolve:
- Simulated capital and intended eventual capital (not yet selected by the user).
- Venue/data availability and permitted use.
- TypeSafe credentials and a USD 3/month AI ceiling are now supplied (2026-09-30).
  Other provider credentials, a persistent worker host and alert destination remain unresolved.
  The static cockpit uses Daniel's existing Vercel account; it does not host the worker.
- Whether to stage the scalping milestone later; it remains requested scope.
- Exact evaluation dates, evidence thresholds and emergency liquidation policy.

First action for the next agent: reproduce the checks and continue the explicitly unfinished milestones above. Implementation is authorized; the April task list remains superseded. Resolve credentials and spending limits before paid model integration.

### 2026-09-30: private Vercel results preview — deployed and access-verified

Daniel asked to use his Vercel and then instructed continuation. Scope: host the existing
saved-results HTML behind Vercel Authentication, using the existing account without a plan
upgrade. The CLI verified account `daniel-eldick`, scope `daniel-eldicks-projects` (Pro).
No existing project matched NeuralEdge. This is hosting of a static report, not paper
operations, automatic result syncing, new AI calls or a background trading worker.

Implementation/verification plan:
1. Create a dedicated `neural-edge-cockpit` project with standard Vercel Authentication;
   verify protection before uploading any report.
2. Stage only generated `index.html` and static hosting configuration in an isolated ignored
   directory. No repository upload, Git integration, database, API key or environment file.
3. Deploy a preview (never `--prod`), verify readiness and anonymous access denial, then
   compare authenticated HTML to the local report and inspect hosted layout where possible.
4. Record URL, protection and refresh instructions; keep the snapshot date and degraded
   Jev pilot warning visible. Update docs/PR; do not merge or promote main.

Evidence: preview `dpl_CeJjyUx4jXphuxPY13Wfcgm9F48q` is READY with `target: null`
(preview), no aliases, and standard Vercel Authentication enabled. Anonymous requests return
HTTP 302 to login with no report content; authenticated requests return HTTP 200 and the exact
local HTML when the documented toolbar-suppression header is supplied. The report SHA256 is
`8e93816158fdc01418fde0ee8da53f39a5ee5c8e9940b2f92b34522ab4357503`.
Response headers enforce private/no-store, no-index, no-sniff and a restrictive CSP. The
in-app browser reached Vercel login; authenticated visual review awaits Daniel's browser login.
See [access and refresh instructions](../guides/COCKPIT_HOSTING.md).

Deployment incident: CLI 59.3.0 treated the first `--target preview` upload as production and
created `neural-edge-cockpit.vercel.app`. Its alias was removed immediately, verified HTTP 404,
and the initial deployment was deleted after the replacement preview was READY. The alias
may have exposed the generated report briefly; access during that interval was not audited.
The upload contained only the static report/config, never tokens or databases. Future deploys
must verify returned target/aliases, not trust the requested flag. Subsequent testing showed
`--skip-domain` is rejected for previews; new projects must first validate hosting behavior
with an empty non-sensitive page before uploading results.
No Git branch was merged or promoted. Existing Pro account used without upgrade or add-on.

Rollback: delete the preview/project via the Vercel dashboard if needed; local journals and
budget accounting remain authoritative. Each refresh is a new explicit report generation
and preview deploy. No promise of live controls or automatic learning in this increment.

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


### 2026-09-30: opportunity screen v1 — protocol fixed before acquisition (0/4)

Bounded continuation of Daniel's “keep going”: evaluate the cost of abstention using unchanged
context+memory and memory-only Jev. Study ID `opportunity-screen-v1`. This extends the previous
falling-period screen; it does not authorize tuning, model training, automated operation or promotion.

**Predeclared data:** BTC/USDT 5m, four UTC start-inclusive/end-exclusive windows:
2024-02-10→2024-02-12, 2024-05-10→2024-05-12, 2024-08-10→2024-08-12,
2024-11-10→2024-11-12. Fixed dates once per calendar quarter, chosen before downloading or
viewing their prices. No claim these will rise. Two-day windows bound inference work; 576 bars
with first21 warmup. Daily history starts 2023-12-01, 2024-03-01, 2024-06-01 and 2024-09-01,
respectively, and ends at the associated test end. Official monthly 5m and 1d archives plus
checksums; validate full months, continuity and every replay day's OHLCV reconciliation.

**Frozen execution:** runtime and evaluation at `44287a5`; one baseline, memory-only and
context+memory run per window, in that order and chronological window order. Model, prompts,
cutoffs, rules and costs unchanged. Separate 1000-USDT accounts, .001 fee/side and .001 adverse
slippage, 2% stop/4% target, existing 0.5% trade risk/2.5% aggregate/24h exit constraints.
Memory starts empty; 2026 teaching material unavailable. Only source closed before each decision
is exposed; response stores retain exact requests. No shared cross-window memory or compounding.
Raw prior20 breakout candidate bound must be <=100 before either paid variant runs; otherwise
skip the paid pair and report the window infeasible. No replacement dates, shortened windows,
higher call limits, retries, reruns, prompt changes or tuning. Stop remaining paid runs on provider
failure, policy errors, incomplete replay or evidence inconsistency; preserve partial evidence.

**Budget:** four windows × two variants × 100 calls × USD .003 reservation = USD 2.40 maximum
reservations, within current USD 2.931025164 remaining. Existing shared USD3/month ledger is
mandatory and unchanged. Require no pending reservations before starting and reconcile exact
nano-USD receipts against ledger delta afterward. No paid infrastructure changes.

**Analysis fixed in advance:** report all attempted windows, net return after trading costs,
sampled drawdown, closed/open trades, decisions, reviewed cases, memory-exposed choices and
AI costs. Compare context versus memory (percentage points), baseline, cash and buy-and-hold.
Explicit opportunity gaps = context return minus baseline and context return minus buy-and-hold;
negative means lagging that reference. Buy-and-hold uses greater full-allocation exposure without
agent stops/holding limits: its gap is descriptive, not attainable foregone profit. Report realized
window direction without replacing unfavorable or inconclusive samples. No significance, learned
edge, cycle recognition or promotion claim from eight days. Prompt/content confounding, model
pretraining and historical-feed revisions remain unresolved. Do not pool returns as a portfolio.

**Acceptance and deliverables:** (1) committed protocol before acquisition; (2) checksummed data,
full candidate coverage and no errors for eligible runs; (3) exact receipt/budget/source/artifact
reconciliation and complete research report; (4) publish all earlier plus new evidence in the
private cockpit, verify authenticated HTML bytes, mobile/desktop interactions and anonymous
protection, update docs and the existing draft PR. Full source quality gate before commits;
no new source/test changes planned. Preserve completed evidence and journal hashes.

### 2026-09-30: context comparison screen v1 — complete / all-context abstention

#### 1. What / why
Bounded continuation authorized by Daniel's “can you keep going?” after the proposed fresh
context-versus-memory comparison. Full tier for historical integrity; existing USD 3/month
inference limit and private static-preview authorization apply. No trading-policy tuning.

#### 2. Fixed design
Study ID `context-screen-v1`. BTC/USDT 5m, UTC start-inclusive/end-exclusive windows:
**2022-02-10 to 2022-02-13**, **2022-06-10 to 2022-06-13**, **2022-10-10 to 2022-10-13**.
Same calendar dates in separated periods; no retrospective regime selection or claim of full
bull/bear/sideways coverage. Each has 864 bars, first21 warmup, 1000USDT, .001 fee/side and
.001 adverse slippage/fill. Existing risk, 2% stop, 4% target and 24h holding unchanged.
Model, prompts, context descriptors and decision/risk/replay sources fixed at `19ed060`.
Only dataset/evaluation/reporting helpers may change. Memory begins empty in each run;
2026 curriculum remains unavailable. Contemporary model pretraining cannot be ruled out.

One run per window, in order: baseline, memory-only Jev, context+memory Jev. Same data/settings,
no repeat draws, retries, prompt edits, higher call limits, replacement dates or longer/shorter
windows. Raw prior20 breakout bound ignoring position/halt gates must be <=100 for both paid
variants; otherwise skip that window's paid pair and report infeasible coverage. Stop remaining
paid runs on any provider failure, policy error, incomplete replay or invalid evidence.
No positive-result promotion from this small exploratory study.

Daily context: checksum-verified official Binance 1d monthly spot archives. History starts
2021-12-01 for February, 2022-04-01 for June, 2022-08-01 for October; ends at each test's
exclusive end. Read exactly those three monthly daily archives per window. Verify contiguous
UTC days and full context availability at first candidate cutoff. Reconcile OHLCV of each
full replay day against aggregated 288 intraday bars (relative tolerance 1e-9, absolute 1e-8).
No repair or substitution. Archive file publication is later than candle close; these are
reconstructed historical bars, not proof of original arrival/revision timestamps.

Cash and full-allocation buy/hold from common bar21 open remain analytical references, with
entry costs and final mark, no hypothetical liquidation. They are not risk-governed agents.
Primary descriptive outcome: context-minus-memory return in percentage points per window;
also drawdown, open/closed trades, candidate coverage, context availability, receipts/cost.
Changed instructions and stochastic output prevent isolating context content causally.
No pooled account, annualized study score, statistical significance or market-cycle claim.

Require zero pending reservations and >=$1.80 worst-case headroom (600×$0.003) before calls.
Existing shared ledger is authoritative; reconcile exact successful costs and unresolved
reservations afterwards. No budget reset, additional provider or subscription.

#### 3. Tasks (six; reassess above nine)
- [x] 0. Failing tests: daily ZIP/checksum/range/gap/mismatch, context evidence receipt equality,
  context-source binding and report mode while preserving memory-screen behavior.
- [x] 1. Implement strict daily importer, overlap reconciliation and read-only context evaluation.
- [x] 2. Acquire fixed data once; record hashes/preflight; no paid calls unless eligibility passes.
- [x] 3. Execute fixed eligible trials once; retain all evidence and reconcile costs/source hashes.
- [x] 4. Save report and publish actual results to private cockpit, preserving earlier evidence.
- [x] 5. Review/Full QA, integrity checks, docs and existing draft PR update.

#### 4. Files / blast radius
New `src/evaluation/daily.py`, context-study tests; extend `src/evaluation/{screen,__main__}.py`
with explicit context-study mode, preserving the old default and its evidence checks. No new
policy, risk, replay or UI design. Reuse dated cockpit groups and context labels/overlay.
Datasets/journals/receipts live ignored under `user_data/research/context-screen-v1/`; final
research/review docs in docs, current status links updated. No new dependency.

#### 5. Verification
Tests first; recorded providers for helper integration; full ruff/mypy/pytest before publishing.
Validate context receipts against reconstructed exact point-in-time daily/weekly snapshots,
not just timestamp claims. Verify source hash in manifest and checkpoint; reject context in
memory-only inputs. Existing memory-screen regressions must pass. Original completed artifact
hashes remain unchanged. Browser check actual protected snapshot on desktop/tablet/phone,
authentication redirect and hosted/local byte comparison. No hosted DB/tenant migrations.

#### 6. Scale / failure
Twelve bounded source ZIPs, sequential paid calls under existing attempts/timeouts/ledger.
Daily import max12 archives, 4MiB each and 10,000 selected days. No automatic study growth at
10x load. Corrupt/missing source or reconciliation mismatch blocks paid trials; keep failure
record. No silent fallback and no retries for uncertain provider responses.

#### 7. Security / rollback
Existing ignored credentials and protected budget only. No source uploads, live orders,
worker or main promotion. Deploy static HTML/config from isolated staging. Preserve all
prior/results artifacts; rollback preview only, never erase experimental evidence.

#### 8. Limits
Three short periods, one asset, coarse fills, prompt confounding, contemporary model knowledge
and revised archives prevent broad learning/cycle claims. No pattern-example library. These
windows become consumed development evidence. Future selection/promotion needs a larger
predeclared protocol and forward paper data. Missing landmine registry stays a warning.


#### Completion evidence — 2026-09-30

This increment 6/6 tasks (100%), not overall product completion. Fixed protocol `c0ad832`
preceded twelve source downloads; daily/intraday values reconciled. Raw call bounds 36/25/27;
all nine runs completed with zero errors and full coverage. All decision/risk/replay/context
source hashes stayed unchanged. No reruns, tuning, replacement periods or expanded limits.

Context mode declined all 88 candidates and returned 0% in every period, versus approximately
−0.499791% for memory-only in each. Cash also returned 0% with no inference cost. All three
realized reference periods fell; no rising-market or learned-edge claim. **Do not promote.**
Study used 173 successful requests, USD 0.035785470, exactly reconciled. Monthly accounted
USD 0.068974836, remaining USD 2.931025164; no unresolved reservations. Original and new
completed journal/receipt hashes unchanged. [Full results](../research/CONTEXT_SCREEN_V1.md).

Ruff/mypy clean (66 files); full tests 228 passed, 17 existing expected failures. Independent
review found no blocker. [Full QA](../reviews/2026-09-30_CONTEXT_SCREEN_QA.md) records browser
and protected-preview checks. Cockpit retains 33 replay/reference records in seven comparison
groups; October context selected by fixed input order. No worker, live order or main promotion.

### 2026-09-30: causal daily/weekly context v1 — complete / correctness-tested (6/6)

#### 1. What and why / authorization
Daniel's “can you keep going?” follows the explicit next step of daily/weekly context.
Implement this bounded opt-in capability under existing authorization. Full tier because
historical causality and checkpoint identity are correctness boundaries. No new paid study,
worker, automatic promotion, risk change or daily learning claim in this increment.

#### 2. Design
Add `--policy jev-context --context-csv daily.csv`, a separate variant extending the existing
memory policy. Frozen Jev and memory-only prompts stay unchanged. Daily input uses the same
OHLCV CSV columns, one symbol, UTC-midnight opens, one row per day, contiguous and finite;
reject empty, missing, duplicate, misaligned or excessive input (max 10,000 rows / 4 MiB).
CLI validates the context symbol against the intraday dataset before creating a journal.
This is explicitly daily input, not an arbitrary 5m file reinterpreted as daily candles.

Read the file once; record its SHA-256 in the run manifest and bind its bytes plus feature
source to checkpoint identity. Full-file provenance stays outside model input: a future suffix
must not alter any earlier request. Local code remains trusted; historical publication/revision
latency and model pretraining are not proven by timestamp filtering.

At decision time, select only daily candles with open + 86400 <= now. Aggregate weekly candles
from exactly seven contiguous daily rows starting Monday 00:00 UTC; omit partial weeks. Weekly
open is first open, high/low extrema, close last close, volume sum. Both frames use bisect
against close times and bounded trailing slices (30 daily / 12 weekly rows). No incomplete
current bar. Availability timestamps are the end of each candle.

Descriptors are arithmetic, not a bull-market classifier: trailing 20-day or 8-week return
(last close / first open - 1), direction up/down/flat by its sign, and mean (high-low)/open.
The descriptive window must be complete and current: last daily close at latest UTC midnight;
last weekly close at latest Monday midnight. Otherwise status `unknown` with reason
`insufficient_history` or `stale_history`, and no direction/return/range value. Raw visible
closed candles remain explicitly dated; the model is told unknown does not imply a trend.
This adds context, not a pattern library, cycle claim, confidence estimate or new entry rule.

Record `CONTEXT_READ` at each actual candidate with cutoff, frame status/last-close dates and
prefix digest. Exact context is already saved in durable response requests. It is stateless
relative to the immutable context CSV, so resume reconstructs identically; changing any source
byte rejects resume before another model call. Existing journal transactions/response receipts
handle rollback/deduplication; preserve memory integrity behavior.

UI scope is labels and existing evidence rows only: identify “Jev with context + memory”, report
memory enabled, show dated context status in expandable records, and prefer memory-only as the
comparison overlay. Reuse the established cockpit UX brief; no new flow, panel or control.
Latest real cockpit remains the completed study; do not publish synthetic development fixtures.

#### 3. Tasks (six; reassess above nine)
- [x] 0. Write failing causal boundary, exact aggregation/descriptor, invalid input, stale/unknown,
  suffix invariance, resume/change rejection, crash/deduplication and CLI integration tests.
- [x] 1. Implement bounded read-only daily history and completed-week aggregation.
- [x] 2. Wire separate context+memory policy and CLI provenance/recovery contract.
- [x] 3. Identify new variant honestly in existing cockpit records; regression-test labels/overlay.
- [x] 4. Run synthetic recorded-provider integration, full gate, code review and Full QA.
- [x] 5. Update plan/status/usage and QA evidence; commit/push the existing draft PR.

#### 4. Files / blast radius
New `src/agents/market_context.py`, `src/agents/contextual.py`, `tests/test_market_context.py`.
Modify replay CLI, existing CLI tests, cockpit report/visuals and their focused tests; update
README/status/plan/review docs. No modification to engine, existing policy/memory source,
evaluator, risk settings, budget, completed journals or comparison protocol. Replay CLI source
is part of the existing engine hash: older unfinished runs require their original revision.

#### 5. Test plan
Tests first: exact Monday close boundary and partial-week omission; 20/8 sample thresholds;
future suffix cannot change earlier context/model request; stale/unknown has null descriptors;
no cross-symbol context, missing/duplicate/nonfinite daily data, row/file bounds; changed daily
file rejects resume before calls; uninterrupted vs paused events/inputs equal; response saved
before crash reused once; provider failure leaves independent exits operating. End-to-end CLI
uses mocked HTTP and a temporary budget, including pause/resume and private-key exclusion.
No browser E2E framework required by root guidance; manual local fixture render checks existing
records/labels, no real result claim. No database/tenant services; Supabase/npm checks N/A.
Run ruff, strict mypy, full pytest. Missing landmine registry disclosed, not a fabricated pass.

#### 6. Scale / failure
One bounded CSV load, O(n) aggregation, O(log n + 42) context selection per candidate. No per-
candidate I/O or API calls beyond existing Jev requests. No mutable cache growth. At 10x load
histories remain independently bounded; multi-symbol sharing and distributed execution remain
separate designs. Malformed sources fail before trading; missing historical coverage is visible.
Provider errors keep existing risk behavior. Numeric overflow in aggregation/descriptors fails
explicitly rather than serializing infinity. No package dependency added.

#### 7. Security / rollback
Use existing budget and receipt controls only. No paid calls needed for this implementation.
No private token/data in Git or browser fixtures. Feature is opt-in; revert to `jev-memory` for
new runs, preserving prior evidence. Context mismatch on resume fails closed. Paper mandate,
0.5%/2.5%/five-position independent controls remain untouched. No hosted auth/config changes.

#### 8. Limits / next gate
Correct timestamp filtering is not proof of useful context or verified point-in-time vendor
availability. Daily inputs need verified source manifests before a real study; this loader does
not certify exchange origin. No chart-analogue retrieval or multi-year-cycle inference yet.
Future real study needs unused declared windows, enough earlier daily history, candidate
coverage preflight, frozen controls and immutable settings before viewing outcomes.


#### Completion evidence — 2026-09-30

This bounded implementation: 6/6 tasks, 100%; broader learning/trading product remains partial.
Twenty-five additional cases bring the full suite to **215 passed, 17 existing expected failures**;
ruff and mypy (64 files) clean. Exact calendar boundaries, descriptors, unknown/stale behavior,
future-suffix request invariance, changed-file recovery rejection, crash deduplication and mocked
HTTP CLI pause/resume verified. Independent review found no blocking production issue.

Local synthetic cockpit QA passed at desktop/tablet/phone sizes with context labels, dated
evidence, memory-only overlay and working controls. No synthetic fixture deployed. Real
cockpit and all fifteen completed memory-study journal/receipt hashes preserved. Budget status
unchanged: USD 0.033189366 accounted, USD 2.966810634 remaining, no unresolved reservations.
No paid calls, worker, policy promotion, risk change, main promotion or new dependency.
See [review and Full QA evidence](../reviews/2026-09-30_MARKET_CONTEXT_QA.md).

### 2026-09-30: memory comparison screen v1 — complete / protocol frozen before data

Implementation and bounded paid inference are authorized by Daniel's continuation and existing
USD 3/month limit. Using the planning skill, **Full tier** for offline evaluation integrity.
This is an initial comparison screen, not a sealed final holdout or market-cycle validation.

#### 1. What and why
Measure memory-on Jev against frozen Jev and the deterministic breakout on previously unused
project windows. Fix dates, costs, coverage and interpretation before loading those candles.
Use this to decide what to investigate next, not to claim profitable learning from a few trades.

#### 2. Design / fixed protocol
Study ID `memory-screen-v1`. BTC/USDT, 5m, three UTC windows: **2023-01-10 to 2023-01-13**,
**2023-06-10 to 2023-06-13**, **2023-10-10 to 2023-10-13**, start inclusive/end exclusive.
Dates use the same day-of-month across separated calendar periods, not chart-selected regimes.
Read one checksum-verified Binance spot monthly archive per window; never repair missing bars.
No additional warmup prefix: all variants see the same 864 candles, with 21 closed bars before
first eligibility. Initial balance 1,000 USDT; fee 0.1% per side; adverse slippage 0.1% per fill;
original risk, stop/target, max-holding and drawdown rules. Fixed model `jev-1.13.0` and prompts
from `a3de91b`; evaluation helpers may be added but decision/risk code must remain unchanged.

One run each of baseline, frozen Jev and memory Jev per eligible window; no repeated draws,
prompt tuning, window extensions, replacement dates or post-result parameter changes. Memory
starts empty in each window; no curriculum cards are historically available in 2023. Thus this
compares recent trade memory, not the full curriculum, multi-timeframe context or training.
Contemporary pretrained model knowledge cannot be excluded by prefix-only data access.

Preflight counts every raw breakout over prior 20 bars without position/halt gates. That is
an upper bound on calls for either Jev variant. If it exceeds 100, do NOT run either paid
variant on that window, shorten it, or raise the cap: report infeasible coverage. Run order is
chronological window order, baseline then frozen then memory. Preserve all failures. Stop
remaining paid runs if provider/network/schema failures occur; no failed-request retries.
Budget snapshot before start must have zero unresolved reservations and enough headroom for
600 × $0.003 = $1.80 worst-case new reservations; the shared monthly cap remains authoritative.
Any actual policy error, incomplete run or missing receipt invalidates that paired comparison.

Read-only controls: cash (0%) and full-allocation buy-and-hold from the first common tradable
open (bar index 21), with the same entry fee/slippage. Mark holdings to the final close, no
hypothetical exit cost. This reference is not a risk-governed agent: no stops or 24h limit.
Do not combine USD inference costs and USDT trading P&L under an unstated conversion rate.

Primary descriptive outcome: memory-minus-frozen net trading return per window, alongside
sampled drawdown, completed/open trades, model coverage and AI costs. No aggregate Sharpe,
p-value or promotion from three three-day windows. Missing results or too few reviewed cases
are reported as inconclusive. Even consistent positive differences are only grounds for a
separately predeclared larger study; a nonpositive result is not repaired by tuning this study.

UX: use the existing cockpit graphs and same-input comparison details. Clearly name cash and
buy-and-hold as references and keep each period separate. Show one dated window in the overview
by predeclared input order (the last eligible window), not the best-performing window. Preserve
the original pilot evidence. No new controls or status that implies an operating worker.

#### 3. Tasks and failing tests (six; reassess above nine)
- [x] 0. Write failing tests for raw-candidate bound, exact benchmark fee/slippage/warmup and
  integrity rejection (mismatched dates/hash/settings, failed/incomplete comparison).
- [x] 1. Implement small read-only evaluation helpers and reproducible report entry point.
- [x] 2. Acquire/verify the fixed windows, record source/CSV hashes and preflight bounds.
- [x] 3. Run eligible comparisons once through the existing shared ledger and durable receipts;
  reconcile usage exactly, retain errors and unfinished windows if stopping is required.
- [x] 4. Save the full report and publish the selected actual results to the private cockpit.
- [x] 5. Code review, QA, full gate, original-evidence integrity check, documentation and PR.

#### 4. Files / blast radius
Add `src/evaluation/` and `tests/test_evaluation.py`; read existing Replay, Journal, ResponseStore,
DailyPerformance and cockpit Run/render interfaces. Extend no trading policy or risk logic.
Store protocol/result report in `docs/research/`; datasets/journals/response files remain ignored
under `user_data/research/memory-screen-v1/`. Reuse the existing protected static preview.
Small presentation changes in `src/cockpit/{report.py,visuals.py,template.html}` and existing
cockpit tests prioritize frozen Jev for memory charts, date disclosure summaries, and label
learning improvement unproven. These implement the existing UX brief without new controls.

#### 5. Verification
Test-first: no helper implementation before failing tests. Exact hand-calculated reference
returns; no entry in warmup; raw bound covers the maximum eligible model schedule; reject
nonmatching/corrupt/partial evidence rather than charting it. Integration uses recorded providers
before paid runs. Full Python quality gate; independent review if fixes require it; Full QA
including private browser layout and disclosure checks. No live-order E2E or new hosted DB.

#### 6. Scale / failure
Three fixed bounded CSVs; stream existing journals read-only. Paid requests sequential through
existing timeout, max-attempt and ledger protections. At 10× load, keep per-study limits and
explicitly plan more windows; no automatic expansion. No DB connection pool or distributed
worker. Ambiguous receipts remain charged and are not retried. Any provider error stops the
remaining paid study, preserving results instead of discarding a losing/incomplete window.

#### 7. Security / rollback
No secrets in commands/logs or artifacts. Keys loaded by the existing CLI. Do not alter/reset
budget, responses, prior datasets or journals. Static hosting only, authenticated preview, no
main promotion. Rollback selects the prior cockpit snapshot while preserving all study evidence.

#### 8. Limits
Three days/window, one asset, limited trade sample, contemporary model pretraining and coarse
candle execution cannot validate a market cycle or establish learning edge. Exogenous matching
controls have different exposure/risk from the bot. No new recurring-pattern engine or daily
worker is included. Missing landmine registry stays disclosed; Supabase/npm guidance is N/A.


#### Completion evidence — 2026-09-30

**This increment: 6/6 tasks, 100%; not overall product completion.** Protocol commit `698a714`
preceded acquisition. All nine replay runs completed once, with zero policy errors or capped
candidates. Six paid variants used 223 successful requests costing USD 0.023188452, exactly
reconciled to the unchanged shared ledger. No pending reservations. Monthly total USD
0.033189366; remaining USD 2.966810634. Decision/risk/replay source hashes and original pilot
journals remained unchanged. Completed study journals and receipts also retained their hashes.

Memory minus frozen return: +0.047625, +0.083181 and 0 percentage points. Only three closed
memory trades; simple breakout beat both Jev modes in the first two windows. No edge or
learning promotion. See [full result and provenance](../research/MEMORY_SCREEN_V1.md).

[Code review and Full QA](../reviews/2026-09-30_MEMORY_SCREEN_QA.md): 190 passed, 17 existing
expected failures; ruff and mypy clean (61 files). Four integrity/reporting findings corrected
in three rounds with independent re-review. Authenticated desktop/tablet/phone checks passed;
private hosted HTML equals the local report. Eighteen saved replay/reference records retained.
No new dependency, risk-rule change, worker, live order or main promotion.

### 2026-09-30: formal QA and recurring-pattern requirement

[Full QA evidence](../reviews/2026-09-30_TEACHER_MEMORY_QA.md) now records the previously
performed Standard code review and the newly completed Full QA pass: **PASS WITH WARNINGS**.
177 tests pass; 17 pre-existing sensory xfails; strict types/lint clean. Exact tablet viewport
and authenticated desktop/mobile interactions passed. Missing landmine registry and limited
UI recovery guidance remain explicit warnings. No new model calls, source changes or merge.
Recurring-pattern and multi-timeframe context requirements are recorded in section 7 above;
the agent does not yet recognize long market cycles. Evaluation remains the next build gate.


### 2026-09-30: causal teacher and memory — complete / verified

Daniel approved starting the next teacher/memory increment and asked whether resources suffice.
Available: sourced original curriculum, causal replay, completed journals, Jev Choice API,
shared USD 3/month ledger, durable model receipts and visual cockpit. No additional paid
provider is needed for this first version. Scope is an evidence-based deterministic teacher
plus opt-in Jev memory consumption; generative teaching and demonstrated trading improvement
are separate milestones. **Tier: Full**, because memory must survive atomic replay recovery.

#### 1. What and why
Convert matured outcomes into candidate evidence cards and expose them to subsequent Jev
candidates without hindsight, cross-run contamination, retries or rule changes. No teacher
approval promotes a strategy. A losing example is retained as evidence, not erased.

#### 2. Design
`ClosedTradeTeacher` pairs recorded ENTER/EXIT events, validates times/prices/quantity and
produces cases available one whole replay interval after exit. Reviews contain descriptive
facts, supporting profitable cases, nonprofitable counterexamples and a fixed uncertainty/test
protocol. Cases are bounded (64 retained, last 6 retrieved for the current symbol); full
history stays in the immutable run journal. No raw free-text outcome explanation enters the
trader prompt. Candidate lessons cannot change stop/target/sizing/risk/score/budget.

`LearningPolicy` extends Jev with a bounded read of its own journal prefix before each decision.
It journals TEACHER_REVIEW and MEMORY_READ evidence inside the same candle transaction.
Checkpoint stores a source-bound cursor/time and memory digest; restoration reconstructs from
that journal prefix and checks the digest and engine checkpoint time. Separate runs start
empty; no cross-run import flag. Existing durable response store still prevents duplicate
paid calls. Failed calls veto entries while code-managed exits continue.

Six machine-readable original curriculum cards remain separate from quiz answers. Earliest
availability is 2026-09-30 UTC, never backdated to 2024. Fixed code and model pretraining are
contemporary external assumptions, not proof of historically clean knowledge. Only closed
trade-derived memory follows the simulated clock. No web retrieval during replay.

CLI mode `--policy jev-memory` is opt-in; `jev` is the frozen comparator. Both share the same
per-run attempt cap and USD 3/month guard. Read-only cockpit evidence recognizes the memory
policy, counts actual reviews/retrievals and shows honest readiness rather than a growth score.
No historical validation/holdout is consumed in this increment.

#### 3. Tasks (six; reassess above nine)
0. Write failing tests: causal availability, losses/counterexamples, curriculum cutoff/answer
   isolation, run separation, prefix invariance, restart parity and crash recovery.
1. Build bounded teacher and original structured curriculum; test invalid/partial cases.
2. Add opt-in Jev memory policy and journal-prefix reconstruction; test mismatched/corrupt
   checkpoint and response-store identity before external requests.
3. Add CLI mode and recorder metadata; test through complete/pause/resume CLI paths with
   recorded model fixtures. No new API model/provider or live order path.
4. Update cockpit evidence/milestone wording and docs; keep old historical pilot scores/data
   unchanged. No claim the old pilot used memory. Verify UI remains coherent.
5. Full quality gate; synthetic correctness demonstration, optional no-cost review of existing
   completed cases, update private cockpit/handoff/PR. Record remaining evaluation work.

Tasks 0–5 complete (100% of this bounded increment). Learning effectiveness remains unevaluated.

#### 4. Files and blast radius
New `src/memory/` teacher/curriculum and `src/agents/learning.py`; extend Jev policy via a
context hook, CLI opt-in, cockpit import/presentation and tests. Package metadata includes
the curriculum JSON for installed builds. Existing replay engine and
journal transaction schema are not changed. Policy/CLI source changes intentionally invalidate
older unfinished recovery contracts; preserve completed pilot files. No locked evaluator edit.

#### 5. Tests
Required assertions: future/open trades absent; review at least one interval after completion;
case availability and review timestamps respected after restart; invalid fields fail loudly;
losses and wins both retained; bounded retrieval; no quiz answers in prompts; curriculum empty
before availability; original frozen requests unchanged; new prompt uses only same-run matured
cases; interrupted and uninterrupted journal events/results match; a crash at review/response
commit neither duplicates paid calls nor lessons; replacement response store/corrupt memory
rejected; model failure preserves stops; no changes to historical evidence hashes.
Python integration tests drive actual Replay/Journal/ResponseStore with fixture providers;
no live-money E2E. Browser check applies only if presentation changes.

#### 6. Failure/scalability
Incremental sequence-index reads (one batch per decision), bounded 64-case memory, bounded
prompt/retrieval and fixed source count. Recovery scans the committed prefix once and retains
bounded state. A corrupt prefix/digest fails closed. SQLite owns a single writer; memory
records and checkpoint commit together, external receipts commit independently as before.
No additional DB service, RLS, network fanout or new dependency.

#### 7. Security and rollback
Model sees only fixed structured facts and eligible cards, never answer keys, secrets, full
CSV or future outcomes. Prompt context cannot alter risk code. Paid calls retain current cap
and expiry. Roll back to `--policy jev` for a new run; preserve journals/budget/receipts. Preview
stays authenticated; no main promotion, worker or real trading.

#### 8. Enforcement limits
Bounded memory is a rolling sample, not statistical proof; promotion remains human-reviewed.
Template-based teacher is not a new generative teacher model, parameter training or self-editing
strategy. Memory changing a prompt does not establish improved decisions. Historical model
pretraining contamination remains unresolved; forward paper and frozen comparisons are needed.
Daily unattended execution and automatic publishing are still outside this increment.


#### Completion and review evidence
- Standard code review: no unresolved blocking findings. Fresh-eyes review independently
  checked causal retrieval, restart ordering, duplicate response recovery and both fixes below.
  `.Codex/landmines.md` is absent; no landmine registry could be audited.
- Fixed during implementation: failed teacher advancement now prevents checkpoint commit and
  rolls back the whole candle; curriculum JSON is included in package data. An isolated wheel
  build verified `src/memory/curriculum.json` is present. No new dependencies.
- Required gate: `ruff check .` → `All checks passed!`; `mypy .` → no issues in 57 source files;
  `pytest -x --timeout=30` → **177 passed, 17 xfailed** (3.22s). Expected failures are the
  pre-existing deferred sensory stubs, not passing learning behavior.
- New integration evidence: delayed reviews, bounded mixed win/loss retrieval, curriculum
  cutoff/answer-key isolation, future-suffix invariance, full-versus-resumed event/prompt parity,
  altered checkpoint/store rejection, review crash rollback, durable response reuse after
  crash and integrity-error rollback. Both CLI modes pass pause/resume; both policies retain
  protective exits during provider errors. Synthetic fixtures are excluded from the cockpit.
- Original baseline and Jev pilot SQLite SHA256 values match the frozen research record.
  No new historical study or paid inference was run. The current cockpit therefore still
  shows the original memory-free pilot, with explicit memory status; new memory runs expose
  reviewed-case/read counts and the review timestamp. No fake learning score.
- Private cockpit refreshed at
  [the authenticated preview](https://neural-edge-cockpit-16pe3ge3m-daniel-eldicks-projects.vercel.app).
  Hosting details and browser verification remain in `docs/guides/COCKPIT_HOSTING.md`.
- Next bounded work: predeclare untouched windows and candidate-coverage rules, compare
  memory-on against frozen Jev and controls after costs, then forward paper evaluation.
  A generative teacher, across-run curriculum promotion, automatic daily operation and
  interactive online controls remain unfinished. No worker or real trades started.


### 2026-09-30: visual cockpit — complete / browser-verified

**Tier: Standard.** Read-only reporting and presentation; existing journal schema, trading,
provider calls, hosting authentication and runtime remain unchanged. Daniel explicitly asked
for more visuals/graphs/timestamps and a considered UX/UI rebuild. Existing hosting scope applies.

#### 1. What and why
Replace text-heavy cards with a visual research workspace. Distinguish historical simulation
time from snapshot publication time. Show genuine decision coverage and performance, never
invent live activity, teacher progress, future milestones dates or a learning score.

#### 2. Solution / UX brief
Daniel scans on desktop or phone: status → chart versus baseline → day/decision breakdown →
dated trade activity → optional precise evidence. Preserve data-driven warning and no-live badge.
```
NE / Cockpit                    Saved snapshot [UTC timestamp]
Jev / Research                  Historical window [start → end UTC]
[Return] [Biggest dip] [Trades] [AI spend]
[Performance / Account value ⇄ Return vs baseline      ] [Decision donut]
[Daily return bars with day labels] [Drawdown area     ] [Trade timeline]
[Connected — Testing — Learning pending; evidence dates where known]
[All experiments & evidence ▸]
```
Accessible CSS radio controls switch chart views; native titles label plotted values. No JS
or charting dependency. SVG grids, axes, zero lines, labels and legends distinguish series
without relying only on color. Focus styles, native disclosures, minimum 44px controls.
At mobile widths charts stack, cards form two columns, activity remains visible below.
Missing data produces an explicit empty graphic; timestamps are UTC. No artificial time filters.
Reuse report dataclasses, native details, palette tokens and deterministic escaped SVG.
Heuristics: visibility via two time domains/status/warnings; forgiveness via read-only controls;
minimalism via graphics + brief labels; consistency via shared axes/tokens; context via mobile
layouts; recovery via existing import errors; speed via default chart; learnability via legends.

#### 3. Tasks and tests (scope: four tasks; reassess above six)
1. Extend read-only import with DAILY_RETURN events, structured trade activity and recorded
   choice counts. First write tests matching hand-calculated returns, timestamps, counts,
   immutable source bytes and unavailable legacy data.
2. Build SVG visualization helpers and visual overview. Tests require only matching inputs
   overlaid, truthful absent charts, escaped labels and correct zero/negative chart behavior.
3. Redesign responsive layout and native chart switching. Verify desktop/mobile screenshots,
   no horizontal overflow, focus/keyboard/tab switching and expanded evidence.
4. Full ruff/mypy/pytest, regenerate existing journals only, private preview deployment,
   anonymous denial/authenticated content verification, handoff/PR update.

#### 4. Files / blast radius
`src/cockpit/report.py`: read-only import/render (medium); `visuals.py`: new SVG presentation
(medium); `template.html`: responsive UI (low); cockpit tests (regression). README, this plan
and hosting guide track evidence/URL. No engine/journal schema/locked evaluator changes.

#### 5. Verification / failure modes
Unit and integration tests use existing pytest; screenshot and DOM checks use bundled browser
runtime if agent-browser CLI unavailable. No new production dependency. Chart dates/amounts
must match recorded events. Daily bars use exact recorded DAILY_RETURN (never sampled curve).
Equity lines stay sampled and labeled; no unsupported intrabar drawdown series. Unknown model
choices fail rather than becoming WAIT. Activity shows last 6 recorded fills, not fabricated
execution timestamps or system wall-clock events. Record chart aggregate scope explicitly.
SVG coordinates bounded; source labels escaped; no config/credentials uploaded. Whole journal
read once; points/activity/daily samples bounded. Legacy missing data stays unavailable.
Existing landmine file has no entries; hosting-specific first-deploy behavior remains in guide.

#### 6. Rollback
Restore prior report/template and previous private preview. Local journals/budget untouched.
Account protection stays enabled. No launch of worker, teacher or paid inference.

#### Completion evidence
All four tasks completed. Full gate: ruff clean; mypy clean across 53 files; **161 passed /
17 pre-existing expected failures**. New tests first failed on absent visual fields, then
verified recorded daily values/timestamps, source immutability, comparison isolation,
flat/negative graphs, trade records, unknown-choice rejection and nonpositive drawdown axes.
The unchanged historical pilot supplies 7 daily returns, 98 WAIT / 2 ENTER / 11 unavailable
outcomes and 4 fills; these are historical market timestamps, not live activity. Full input
journal hashes still match the pilot report. Daily history retains the last 366 events and
shows at most 14; activity retains 6 fills. Close-drawdown peaks are computed before chart
sampling and explicitly exclude unrecorded intrabar paths. Overall max drawdown remains the
journal result. Same-input baseline is chosen by identity, never highest return.

Authenticated Chromium checks passed at 1440×1050, 820×1100 and 390×844: no browser errors,
no horizontal overflow (including expanded evidence), working click and keyboard chart
switching. Desktop/mobile screenshots visually inspected; axes rounded to readable intervals,
phone chart uses a narrower SVG, snapshot and market dates are separate, negative returns are
not colored as gains. No JS, dependencies, model calls, runtime changes or auth weakening.
The agent-browser CLI was unavailable; the bundled Playwright runtime handled verification.

Final preview: https://neural-edge-cockpit-6wkzon4c2-daniel-eldicks-projects.vercel.app
Deployment `dpl_2ynMHRtaXrKzjS7tdG9M1mAwk3Nn`: READY preview, no aliases. Anonymous
HTTP 302; authenticated HTTP 200, restrictive headers and exact local/hosted HTML equality.
HTML SHA256: `06f9d34460ca09f953df4d5d3523da33c45fde116757aa640cde215a0d6c7669`.
Screenshots: ignored `user_data/cockpit/visual-cockpit-{desktop,tablet,mobile}.png`;
DOM checks: `user_data/cockpit/browser-check.json`. The former previews remain rollback options.


### 2026-09-30: cockpit scan-first redesign — implemented and published

Daniel explicitly asked for less reading and a more intuitive cockpit. This authorizes the
presentation update and refresh of the existing private preview. No new runtime controls.

Verified: ruff clean; strict mypy clean (51 source files); **153 passed / 17 pre-existing
expected failures**. Regression checks protect Jev-first selection (not best-return selection),
standalone incomplete-test warnings, four headline metrics, XSS escaping, fallback and empty
states. Native closed details preserve full precision/records. Default visible text reduced
from 556 to 175 words (69%, excluding collapsed details and CSS). No trading logic changed.

Updated preview: https://neural-edge-cockpit-n7m5x9tlh-daniel-eldicks-projects.vercel.app
Deployment `dpl_AXiNNG5NAVmPh7cTDBM4KZt6hfaG`: READY, preview target, no aliases.
Anonymous HTTP 302 to login; authenticated HTTP 200, exact generated HTML SHA256
`53647360ad9f191d9492ddfe4c585079db2aed91c970950191b7646940258d6c`. Browser reaches login; layout review remains
pending authenticated browser access. The original preview remains available for rollback.
No credentials, databases, new dependencies, paid inference or worker added.

UX brief: Daniel checks progress quickly on desktop or phone. First answer: is this live,
what did the selected Jev experiment return, what needs attention, and is learning active?
Journey: open → scan status/four numbers/chart → optionally expand records. Empty state
invites importing a completed run; incomplete imports still fail loudly. Offline snapshots
remain usable and visibly dated. No loading state or fake operational buttons.

Wireframe:
```
NEURALEDGE                              Saved snapshot · date
Your agent, at a glance.                 Research only · Not live
[Return] [Biggest dip] [Closed trades] [AI cost]
[Equity chart                         ] [Build → Test → Learn]
[Incomplete evaluation warning, if applicable]
[Compact same-input comparison]
[All experiments and evidence ▸]
```

Heuristics: visibility keeps date/status and incomplete coverage visible; forgiveness uses
read-only disclosure; minimalism limits headline metrics to four; consistency reuses colors
and native details; context uses responsive two-column mobile metrics; errors retain clear
import failures; speed needs no click for key numbers; learnability uses plain labels.
Reuse existing report dataclasses, SVG chart, escaping and native details (keyboard accessible,
44px targets). No dependencies, JS, invented progress, learning score or profitability claim.

Implementation/test plan: (1) focus Jev when present, otherwise the last supplied experiment
without claiming it is chronologically latest; (2) compact metrics/chart/comparison and collapse
all technical evidence; (3) test focus selection, visible degraded standalone runs, escaped
content and empty state; (4) run full quality gate, regenerate saved report, deploy private
preview with no alias, check authentication and byte equality, update handoff/PR. Source scope:
report.py, template.html and cockpit tests. Browser layout verification requires authenticated
browser access; do not weaken protection. Rollback restores the prior presentation/preview.


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
