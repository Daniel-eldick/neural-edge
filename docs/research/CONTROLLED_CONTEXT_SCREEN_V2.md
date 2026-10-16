# Controlled context screen v2 — frozen design, execution blocked

Prepared 2026-10-14 UTC. Study ID: `controlled-context-screen-v2`.
This commit freezes the proposed design, not an executable experiment: the matched
control policies and their validator do not yet exist. No data acquisition, paid
inference or market evaluation was performed for this document. The
[active plan](../active/APPRENTICE_TRADER_PLAN.md) remains authoritative.

## Question and decision

Can daily/weekly context change decisions beyond the effect of its instructions,
with reliable coverage and reconciled costs? This is a feasibility and attribution
screen, **not a profitable-edge, learning or promotion test**. Existing
[memory](MEMORY_SCREEN_V1.md) and [context](CONTEXT_SCREEN_V1.md) comparisons change
instructions and inputs together; the latter also contains only falling periods.
The [opportunity screen](OPPORTUNITY_SCREEN_V1.md) remains incomplete and must not
be retried, extended, relabeled or folded into this study as a clean result.

## Hard prerequisites

1. Obtain authoritative provider usage evidence for the earlier uncertain request;
   retain its USD 0.003 reservation until evidence supports reconciliation. A new
   month, new response store or unused budget does not resolve unknown usage.
   Read the actual persistent ledger; September figures are historical, not current
   available budget. Missing original ledger/evidence means blocked, not initialize
   a replacement or infer zero spending. No credential or billing evidence in Git.
2. Implement the three separately identified policies below and an offline validator.
   Review source, pass applicable quality gates and record the exact code commit,
   policy/source hashes, full canonical prompt strings, option order, provider model,
   version and generation parameters in a committed execution manifest **before**
   acquiring these datasets or evaluating any window. Do not silently reuse v1 labels.
3. Verify current provider price/model availability before any paid call; the old
   pricing expiry is not permission to assume unchanged pricing. All calls must use
   the existing shared USD 3/calendar-month guard. The per-study reservation ceiling
   below must fit the actual remaining authorized allowance at the verified rate.
4. Require no unresolved attempts in the shared ledger, exclusive study execution,
   immutable source/result destinations and a study-wide stop on the first uncertain
   call. No unattended process, real orders or deployment is part of this protocol.

If implementation cannot honor these fixed choices, stop and publish a superseding
protocol before data acquisition. Do not amend this design after viewing results.

## Matched arms

Every arm has memory, curriculum, teacher and cross-run retrieval disabled. All see
identical causal base candles, portfolio fields and options. Model version,
generation settings, entry logic, stops, targets and execution engine are identical.

| Arm | Instructions | Daily/weekly payload |
| --- | --- | --- |
| A: base | Frozen existing base instructions | No context field |
| B: context instructions only | One frozen context-aware instruction string | Explicit unavailable daily/weekly context with empty candles; never fake zero prices |
| C: context content | Byte-identical instructions to B | Verified causal daily/weekly snapshot |

The shared B/C addition instructs: use available closed higher-timeframe OHLCV as
supporting evidence; unavailable context is unknown, not a negative market signal;
do not infer missing values. Exact serialized wording and unavailable schema must
be frozen with the implementation. B versus A estimates the **instruction plus
schema** effect; C versus B estimates the available-context treatment conditional
on that instruction/schema. It does not disentangle useful arithmetic content from
context availability, token length or attention effects. No shuffled/future/wrong
market context is permitted as a placebo. This does not test memory learning.

## Fixed data and execution

BTC/USDT spot, 5m candles; UTC start inclusive/end exclusive:

| Window | Replay interval | Daily source interval |
| --- | --- | --- |
| W1 | 2025-02-10 to 2025-02-11 | 2024-12-01 to 2025-02-11 |
| W2 | 2025-05-10 to 2025-05-11 | 2025-03-01 to 2025-05-11 |
| W3 | 2025-08-10 to 2025-08-11 | 2025-06-01 to 2025-08-11 |
| W4 | 2025-11-10 to 2025-11-11 | 2025-09-01 to 2025-11-11 |

These are fixed quarterly calendar dates, not selected regimes. No prices were
inspected to select them here. Before acquisition, inventory existing experiment
manifests: any previously evaluated overlap makes this design ineligible as fresh
project evidence. Stop without substituting dates. Historical model pretraining
contamination remains possible even for new project windows.

Use official checksum-verified monthly 5m and 1d archives. Validate full source
months, timestamp units, contiguous rows, finite OHLCV and daily reconciliation.
Each replay has 288 bars including the initial 21-bar warmup; independent 1,000-USDT
accounts; fee 0.001 per fill; adverse slippage 0.001; 2% stop/4% target;
0.5% account-risk admission, 2.5% aggregate cap, five positions and 24h maximum hold.
Retain next-open fills and stop-first ambiguous candles. Mark final holdings with
no hypothetical liquidation fee; disclose open positions and unmatched pending
last-bar decisions. Never carry accounts or memory across windows.

Run windows chronologically. Within each, complete the deterministic breakout
baseline first, then W1 A/B/C, W2 B/C/A, W3 C/A/B, W4 A/C/B. This balances some order
effects; one draw per arm cannot estimate provider stochastic variance. Include
cash and the existing full-allocation buy-and-hold analytical reference, explicitly
not governed by agent risk limits. Do not describe its gap as attainable lost profit.

## Coverage and conservative budget

Precompute the raw prior-20-high breakout count from source data, ignoring position
gates, for all four windows before paid work. Require every count <=60 and all
initial context snapshots complete. If any fails, stop the **entire paid study** as
infeasible; preserve the counts and do not shorten, replace, or cherry-pick windows.
Set each paid run's attempt cap to 60. Four windows × three arms × 60 attempts ×
USD 0.003 gives **USD 2.16 maximum reservations** at the existing bound. This is a
budget ceiling, not expected spending. Verify that the bound still covers each
maximum-size request under current pricing and that remaining shared funds suffice.

Full coverage means every eligible decision in each arm has one durable successful
receipt. Position-dependent eligibility can differ across arms. Report raw bounds,
actual attempts, successful receipts, risk/position exclusions, waits, entries,
errors and open/end-of-window state per arm. Never count an error/cap veto as an
intentional wait. No missing observations may be imputed as cash returns.

First failure or uncertainty ends new paid work across **all arms/windows**, while
protective replay exits remain operational. Preserve partial artifacts and label
the comparison incomplete. No retry, replacement trial, new-store bypass or fresh
account reset; no post-failure completion of a paired contrast. Read-only report
reconstruction is allowed from preserved evidence under its original contract.

## Frozen analysis and sample sufficiency

Primary descriptive contrast: C minus B net trading return in percentage points,
reported separately for every scheduled window, including missing/incomplete status.
Secondary: B minus A, C minus A, each versus cash/breakout/holding, sampled drawdown,
exposure, turnover, closed/open trade counts, decision agreement on **common**
eligible timestamps, and USD inference cost. Common-timestamp agreement is selected
by each policy's portfolio trajectory and is not a causal per-opportunity estimate.

Report full opportunity counts and both positive/negative performance gaps; no
post-hoc winning-window selection, pooled compounded portfolio, significance claim
or annualized Sharpe from four one-day windows. Retain the existing 30-complete-day
threshold for descriptive Sharpe; meeting it elsewhere would still not prove edge.
Trading USDT and inference USD remain separate without a frozen conversion rule.
Unknown cost means unknown operating P&L, never zero cost.

The outcome categories are fixed:

- **Operational failure:** any missing coverage, uncertain usage or mismatched evidence.
- **Feasible but uninformative:** clean completion, including all-wait behavior or too
  few entries to assess entry quality. Zero trades cannot establish profitable skill.
- **Feasible with descriptive treatment differences:** clean completion and observed
  differences; these motivate a separate study, not promotion or a changed policy.

No trade-count threshold converts this pilot into adequate efficacy evidence.
A later efficacy protocol needs longer unseen periods, independent windows across
trailing-defined regimes, stochastic replicates if supported, a predeclared minimum
useful effect and uncertainty method appropriate for serially correlated returns.
Determine its sample requirement from development-only variance/dependence and
budget before touching its holdout; if affordable power is inadequate, declare that.
Do not extend this pilot until significance appears. Cost stress and forward paper
validation are later separately frozen studies; forward operation requires its own
authorization. Existing positive-profit/Sharpe/drawdown targets remain unchanged.

## Evidence contract and implementation gaps

Persist an append-only experiment manifest, original archives/checksums, normalized
CSV hashes, exact source commit/hash set, per-arm journals/response stores, execution
start/end metadata and ledger reconciliation. Hash immutable artifacts at close.
Publish every attempted window and failure, including blocked preflight outcomes.
No model responses or credentials in Git. A report is not a substitute for originals.

The existing `src/evaluation/screen.py` cannot validate these new arms as-is. In
addition to policy/schema support, require exact prompt/model/options validation,
canonical base-candle reconstruction at each decision, causal context snapshots,
portfolio/policy identity checks and reconciliation of every eligible opportunity
and receipt. Historical v1 artifacts must remain readable under their old contract.

Static audit of baseline `eb879f67004e788a6db18e59c80a96adf72b94c1` found that
`receipt_evidence()` validates saved response hashes,
choice/cost events, context snapshots and temporal bounds, but does **not** compare
saved request instructions/options/model to the declared contract or base OHLCV
values to canonical input candles. Its response checksum covers the response, not
the request. Therefore its acceptance alone does not prove prompt/input fidelity.
This is a reproducibility validator gap, not evidence that original results were
modified. The corrective implementation must add synthetic altered-request regression
fixtures and reject them without touching saved market evidence.

Documentation verification: check local links and diff scope only. This protocol
adds no execution authorization, runtime behavior or claims of completed research.
