# Archive decision — 2026-11-18

**Status**: ✅ COMPLETE — project archived, nothing scheduled, nothing spending.

## Decision

NeuralEdge is archived. No evidence of a trading edge was found, and the two
mechanisms meant to find one cannot produce a result as built.

## Evidence

### 1. The public strategy barely trades

`AlphaStrategy` was backtested for the first time, on two years of public
Binance 5m candles (2024-11 to 2026-10; BTC, ETH, SOL vs USDT; 630,720 candles;
0.1% fee per side). Run: GitHub Actions `Strategy backtest`, run 44196628803.

| Variant | Stoploss | ROI | Trades | Win rate | Avg trade | t-stat | Net return | Max drawdown |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| as_is | -10% | 4% / 2% / 1% | 14 | 35.7% | -0.003% | -0.03 | -0.01% | 0.2% |
| tight_stop | -2% | 4% / 2% / 1% | 14 | 35.7% | -0.003% | -0.03 | -0.01% | 0.2% |
| symmetric | -4% | 4% | 14 | 35.7% | -0.003% | -0.03 | -0.01% | 0.2% |

Pass rule, declared in `src/backtest/run.py` before the run: at least 200
trades, positive average trade after fees with a t-statistic of 2 or more, and
positive in both halves of the period. All three variants fail on the first
check.

Why: the entry requires RSI below 30 while the fast EMA is above the slow EMA.
Those two conditions almost never coincide, so the strategy took 14 trades in
two years (BTC 6, ETH 6, SOL 2). Every one closed on the exit signal within a
few candles; no stoploss or ROI target was ever reached, which is why the three
variants are identical. The strategy is neither profitable nor unprofitable. It
is inert.

Equal-weight buy and hold over the same window returned -14.6% in this data, so
"did nothing" was not the worst outcome, but that is not an edge.

### 2. The hosted research loop did not change the picture

The recurring Jev loop has been running since 2 November. Its results were
reviewed for this decision and give no reason to continue. They stay in the
private results repository by design and are not repeated here.

### 3. The remaining layers were never built

The sensory modules raise `NotImplementedError`; the signal aggregator,
adapters and autoresearch packages are empty.

## What was changed

- Removed the daily schedule from `jev-recurring-research.yml`. The two one-shot
  workflows were already disabled. Remote research state, encrypted results and
  budget holds are untouched.
- Added `src/backtest/` (pandas-only backtester, 11 tests) and the manual
  `Strategy backtest` workflow. It uses no secrets and costs nothing.
- Corrected the README to describe what exists.

No code was deleted. `dry_run` remains `true`.

## What would justify reopening

A specific, written hypothesis for an entry rule that trades often enough to
measure (hundreds of trades over two years), tested with the backtester under
the same pass rule before any AI layer or hosted loop is switched back on.

## How to resume the hosted loop

Restore the `schedule` trigger noted at the top of
`.github/workflows/jev-recurring-research.yml`. Read `deploy/research/README.md`
first: the budget ledger must not be reinitialised.
