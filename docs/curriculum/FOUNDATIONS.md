# Apprentice curriculum v0.1

Prepared and sources checked: 2026-09-30. **Status: curated teaching material; not loaded
into Jev, no automated teacher, no training or competency pass claimed.** This is the first
foundation module, not a complete trading course. The [active plan](../active/APPRENTICE_TRADER_PLAN.md)
governs risk, learning permissions and implementation. No course purchase is needed.

## Source register, ranked by teaching order

We retain links and our own short lesson summaries, not copies of books, courses or articles.
Public access does not imply permission to redistribute or bulk-ingest a source. No reuse
license was established for these retrieved pages/PDF; automated full-text ingestion remains
out of scope. This document contains original exercises and no substantial source quotations.

| ID | Source / author | Date/version observed | What it supports and its limits |
| --- | --- | --- | --- |
| S1 | [Spot filters — Binance](https://developers.binance.com/en/docs/products/spot/filters) | Living documentation; page reports modified 2026-09-30 | Order price, quantity and notional constraints. Current examples are not historical exchange settings. |
| S2 | [Backtesting assumptions — Freqtrade contributors](https://www.freqtrade.io/en/stable/backtesting/#assumptions-made-by-backtesting) | Living stable docs; publication date not established | Candle simulation relies on assumptions about fills and event order. It does not prove realistic execution or describe our separate replay exactly. |
| S3 | [Proper Position Size — CME Group](https://www.cmegroup.com/education/courses/trade-and-risk-management/proper-position-size) | Publication date not stated in retrieved page | Position size depends on stop distance and the account risk budget. Futures examples/risk percentages do not override our spot-only 0.5% limit. |
| S4 | [Lookahead analysis — Freqtrade contributors](https://www.freqtrade.io/en/stable/lookahead-analysis/) | Living stable docs; publication date not established | Full-data calculations can leak future information. A diagnostic is not a universal proof of causality or a check of model pretraining. |
| S5 | [The Probability of Backtest Overfitting — Bailey, Borwein, López de Prado and Zhu](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) | PDF dated 2015-02-27; February 2015 revision | Strategy selection across backtests can overfit. The paper develops a way to assess that risk; this project has not implemented its estimator. |

## Lessons and original exercises

### L1 — An order must be executable

**Read:** S1. Price increments, quantity increments and minimum notional can invalidate a
proposed order. A simulated fill is not evidence that a venue would accept it.

**Exercise:** hypothetical quantity step 0.01, minimum notional 10 USDT, price 100 USDT:
can a proposal for 0.099 units execute after rounding quantity down?

**Answer:** 0.09 × 100 = 9 USDT, below the minimum. Reject; do not round up through a risk
limit. These are invented numbers, not Binance's current BTC filters.

**Required behavior:** reject invalid orders explicitly; obtain dated venue rules before
exchange integration. **Current gap:** replay does not enforce venue filters.

### L2 — Costs can erase a correct direction call

**Read:** S2. Our evaluation must state its fill assumptions and distinguish trading results
from operating costs. A candle does not reveal queue position or the complete price path.

**Exercise:** buy one unit at market reference 100, sell at reference 100.3; apply 0.1%
adverse slippage and 0.1% fee on each side. What is the result before AI cost?

**Answer:** purchase debit = 100 × 1.001 × 1.001 = 100.2001; sale credit =
100.3 × 0.999 × 0.999 = 100.0995003; net = **−0.1005997** quote units. Rising price alone
does not establish a profitable trade. This is an original arithmetic fixture, not market evidence.

**Required behavior:** show fees, slippage, open exposure and AI costs; do not present a
cost-free score as deployable performance. Unresolved inference reservations remain disclosed.

### L3 — Account risk differs from position value

**Read:** S3. Our approved per-trade risk is at most 0.5% of account equity. The five-position
and 2.5% aggregate limits remain code-enforced; teaching material cannot change them.

**Exercise:** equity 1,000; entry 100; protective stop 98; ignore fees/slippage solely for
this arithmetic exercise. What is the maximum quantity before cash/portfolio constraints?

**Answer:** risk budget 5; per-unit planned loss 2; quantity at most **2.5**, not 5 units
and not 0.5% of position value. Real sizing must include costs, cash and existing exposure.
A gap through the stop can exceed planned loss. Neither the curriculum nor the model may
promise a guaranteed loss ceiling.

### L4 — Only use information available at the decision time

**Read:** S4 and our [replay implementation](../../src/replay/engine.py).

**Exercise:** a five-minute bar opens at 10:00 and closes at 10:05. Can a decision at 10:03
use that bar's final high or close? Can a teacher release the eventual trade outcome then?

**Answer:** neither is available. Our close-based proposal can first execute at the next
bar's open, subject to the simulator's declared zero additional latency assumption.

**Required behavior:** changing candles after time T must not change observations/decisions
through T; a lesson from a completed trade becomes available only after completion and review.
Do not put future outcomes, answer keys or evaluation scores in a trader prompt.

### L5 — A setup is a testable definition, not a profitable fact

**Read:** our [fixed baseline](../../src/replay/__main__.py) and
[Jev filter](../../src/agents/policy.py). This is a project hypothesis, not a source-backed
claim that breakouts predict returns.

**Exercise:** candidate close 101; highest high of the previous 20 completed bars 100.5.
Is the breakout predicate true? Does that imply entering is profitable?

**Answer:** true, but profitability remains unknown. Exclude the candidate bar from the
reference maximum. WAIT is permitted; count all eligible opportunities and missed evaluations.
The 2% stop/4% target are frozen experimental parameters, not learned optimal values.

**Probability exercise:** a hypothetical system wins 40% of the time with average win 2R
and average loss 1R. Expected payoff is 0.4 × 2 − 0.6 × 1 = **0.2R before costs**. These
assumed frequencies are not supplied by Jev's classification confidence. Calibration and
unseen observations are separate evidence requirements.

### L6 — A lesson needs counterexamples and an untouched test

**Read:** S5. Repeated strategy selection can favor luck; report the whole experiment history.

**Exercise:** after trying 50 variations on the same week, one looks best. Is that week an
untouched validation set for the selected rule? Do two winning trades justify promotion?

**Answer:** no to both. Freeze the candidate, its comparisons, costs, dates and coverage
rules before a new evaluation. Passing an arithmetic quiz demonstrates comprehension only.

**Required behavior:** retain failed trials, supporting and contradicting cases. Do not tune
or extend a completed evaluation to rescue its result. Compare learned and frozen variants;
teacher approval alone cannot promote a strategy. The existing one-week pilot's 11 capped
candidates prevent a claim of complete model coverage.

## Historical availability and leakage boundary

This curriculum version was assembled on **2026-09-30**. Its conservative availability date
is that date; it must not be relabeled as known in 2024. Earlier publication of S5 does not
backdate our synthesis. Living docs may contain later venue rules and historical examples.
No raw webpage or later market example is to be automatically retrieved during an old replay.

For a future historical study, a fixed contemporary curriculum would be an explicit external
knowledge assumption, not a leakage-free simulation of a trader trained at the old date.
Prefer forward paper evaluation for the strongest temporal check. Model pretraining knowledge
cannot be excluded merely by hiding future CSV rows. Current runtime does not load this file.

## Handoff to the teacher/memory implementation

The next implementation should store original structured lesson cards separately from quiz
answer keys. Each card needs `lesson_id`, curriculum version/content hash, source IDs,
creation/availability time, claim, supporting case IDs, counterexample IDs, uncertainty,
test protocol and status (`candidate`, `evaluated`, `approved`, `rejected`). This is a proposed
contract; no new database or runtime integration is implemented by this document.

Teacher input is limited to matured outcomes available at review time. A retrieval cutoff
must apply to every case and derived lesson, including after restart. Quizzes use synthetic
fixtures; evaluation uses separately frozen data. Neither teacher nor memory can change
risk caps, spending limits, evaluation criteria, or strategy source at runtime.

Completion evidence will require tests for future-case rejection, answer-key isolation,
checkpoint recovery, counterexample retention and same-data learned-versus-frozen comparisons.
Record actual API cost before selecting any additional teacher provider. Stay inside the
existing total USD 3/month allowance; no provider purchase is required for this source pack.
