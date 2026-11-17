# Strategy search — 2026-11-18

**Status**: ✅ COMPLETE — no configuration passed. The archive decision stands.

Follow-up to [ARCHIVE_DECISION_2026-11-18.md](ARCHIVE_DECISION_2026-11-18.md): instead of
only testing the existing strategy, twelve textbook long-only rules were tested on six
years of public Binance data, with the last 28 months held back as an unseen exam.
Parameters, split date, costs and the pass rule were fixed in `src/backtest/search.py`
before any result was seen. Run: GitHub Actions `Strategy search`, run 44198126742.

Train 2020-09 to 2024-06, holdout 2024-07 to 2026-10. BTC/ETH/SOL equal weight,
long or flat, 0.15% cost per position change.

| Config | Train return | Train Sharpe | Train DD | Holdout return | Holdout Sharpe | Holdout DD | Holdout trades | Verdict |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| buy_and_hold | 1726% | 1.35 | 85% | -13% | 0.20 | 64% | - | benchmark |
| sma50_1d | 3113% | 1.99 | 52% | 49% | 0.66 | 34% | 73 | FAIL: holdout Sharpe below 0.8 |
| sma100_1d | 1041% | 1.45 | 62% | 18% | 0.38 | 28% | 60 | FAIL: holdout Sharpe below 0.8 |
| sma200_1d | 585% | 1.27 | 45% | -4% | 0.12 | 28% | 36 | FAIL: holdout return not positive |
| ema20_50_1d | 2228% | 1.77 | 58% | 12% | 0.31 | 33% | 26 | FAIL: holdout Sharpe below 0.8 |
| ema50_200_4h | 2201% | 1.78 | 61% | 16% | 0.35 | 42% | 47 | FAIL: holdout Sharpe below 0.8 |
| donchian20_10_1d | 2298% | 1.97 | 47% | -13% | -0.07 | 40% | 42 | FAIL: holdout return not positive |
| donchian55_20_1d | 1725% | 1.88 | 43% | -6% | 0.04 | 31% | 20 | FAIL: holdout return not positive |
| donchian55_20_4h | 695% | 1.51 | 40% | 18% | 0.40 | 34% | 100 | FAIL: holdout Sharpe below 0.8 |
| momentum30_1d | 4699% | 2.19 | 38% | 23% | 0.42 | 41% | 109 | FAIL: holdout Sharpe below 0.8 |
| momentum90_1d | 1103% | 1.45 | 64% | -2% | 0.15 | 35% | 45 | FAIL: holdout return not positive |
| rsi2_dip_1d | 8% | 0.20 | 27% | 3% | 0.15 | 17% | 53 | FAIL: holdout Sharpe below 0.8 |
| rsi14_dip_1h | -7% | 0.11 | 55% | -57% | -1.32 | 63% | 435 | FAIL: holdout return not positive |


DD = maximum drawdown. Pass rule (holdout): positive return, Sharpe of 0.8 or more and
above buy-and-hold, drawdown under 30% and below buy-and-hold, 20+ trades, positive
train return.

## Reading

- Nothing passed. Every trend and momentum rule looked excellent in 2020-2024 and
  ordinary afterwards. That gap is the difference between a backtest and an edge.
- The best holdout result was the 50-day moving-average rule: +49% against -13% for
  buy-and-hold, with about half the drawdown. It still missed the bar on Sharpe (0.66)
  and drawdown (34%), and with twelve tries one result like this is expected by chance.
- Most trend rules had smaller drawdowns than holding. That is a risk reduction, not a
  source of profit.
- Dip-buying on RSI lost money or went nowhere in both periods.

## Limits

Three highly correlated coins, one exchange, daily-rebalanced equal weights, a flat
0.15% cost per position change, and no funding, tax or outage effects.
