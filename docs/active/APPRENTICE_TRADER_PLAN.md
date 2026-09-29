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
| Current authorization | Implementation and local verification; no deployment, paid inference or real trading |

The proposed 1.5% aggregate cap was NOT accepted; preserve 2.5%.
The recommendation to defer scalping was NOT accepted as a scope deletion. Retain it as a separate milestone requiring better execution evidence.
Live capital, shorting, leverage, paid services and deployment are not authorized.

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
  API access and spending authorization are still unresolved; it is not connected yet.
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

Curriculum procurement is a future task assigned to the assistant:
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

Defaults: $1,000 simulated spot cash, 0.1% fee per side, 0.1% adverse slippage per fill. Override with `--balance`, `--fee`, `--slippage`. These are experiment assumptions, not venue quotes. Each journal path must be new. SQLite `events` stores ordered JSON payloads including input hash, settings, decisions, vetoes, fills, equity and result. Query with `SELECT payload FROM events ORDER BY sequence`.

The comparison policy enters when a close exceeds the previous 20-bar high, proposes a 2% price stop and 4% target, and otherwise waits. It is a plumbing control, not a selected profitable strategy. `Policy.decide(Observation)` is the adapter boundary for a later apprentice. Observations contain immutable closed-candle prefixes and current portfolio state; local policy code is trusted, not sandboxed.

Execution ordering is open mark → gap/age exits → requested exits → risk-checked entries → intrabar protective exits → close mark → new decisions. Simultaneous entries are admitted sequentially in symbol order with updated cash/equity. Close-derived signals fill at the next open with costs; there is no same-close fill. Both stop and target touched means stop first. Protective gaps fill at the open. Final pending proposals expire; remaining positions stay marked to market and are reported explicitly.

Limits of this increment:

- Risk caps govern entry admission. Existing market exposure can exceed planned risk after price changes or gaps. Stops do not guarantee a maximum loss. The drawdown halt is latched for the run, blocks entries, and keeps protective exits active.
- Drawdown is sampled at opens/closes and executions; unknown intrabar portfolio paths are not reconstructed. Results can understate true drawdown. End equity includes unrealized positions and does not deduct hypothetical future liquidation fees.
- One position per symbol, long-only, no borrowing. No exchange lot sizes, minimum notionals, spread/queue/partial-fill models, measured decision latency or chart rendering yet. Zero additional decision latency is assumed.
- SQLite is an audit journal, not a resumable account checkpoint. Replay refuses instance reuse and journal overwrite. Restart recovery and durable breaker restoration remain unfinished; no unattended operation.
- No teacher, learned memory, curriculum retrieval, provider calls, exit modification or separate scalping agent yet. A 60-second replay is exploratory and cannot validate scalping profitability.
- `daily_sharpe` is null until the evaluation layer implements a declared daily-return convention. There is no pass/fail profitability screen in this increment.
- Freqtrade remains a separate baseline. This independent replay avoids requiring stateful agent decisions inside its vectorized strategy pipeline; a paper-execution bridge is still unverified.
- Python 3.12 was used for local verification. NumPy is capped below 2.5 so its stubs parse with the project's Python 3.11 type-check target. Full dependency locking and Python 3.11 runtime verification remain P0 tasks.

P1/P2 are partial: simulation and admission enforcement exist; restart and realistic execution do not. P3 has the decision interface only. Next work: checkpoint/recovery and daily evaluation, then a recorded-response trader/teacher adapter with causal memory tests before any paid-model experiment.

## 10. Background operation and cost control

Persist a complete checkpoint, not only a text summary. Reconcile pending/filled orders on restart; never assume a timed-out submission failed. Halt new entries on stale data, bad state, invalid decisions, cost exhaustion or risk breach while maintaining existing protection.

Estimate inference volume before model selection: one year contains 105,120 five-minute steps or 525,600 one-minute steps per symbol, before teacher calls. Five symbols multiply these counts by five. Consider cheap deterministic screening/batching, but measure whether it suppresses opportunities. Record cost per simulated day and per paper day; require a hard approved spending ceiling.

Weekly review is an eventual operating goal after stabilization, not a guarantee. Reports should include performance versus controls, costs, risk violations, candidate changes, data gaps and failures. Urgent faults must alert separately. Hosting, channel, budget and unattended execution need explicit setup authorization.

## 11. Remaining decisions and handoff

No additional conceptual questionnaire is needed. Before spending or launching, resolve:
- Simulated capital and intended eventual capital (not yet selected by the user).
- Venue/data availability and permitted use.
- Model credentials, budget ceiling, host and alert destination.
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
