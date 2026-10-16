# First Jev historical pilot — development evidence

Run date: 2026-09-30. Protocol: the 2026-09-30 historical-comparison entry in the
[active plan](../active/APPRENTICE_TRADER_PLAN.md), written before running either policy.
**Outcome: completed simulations, but incomplete Jev candidate coverage. No promotion.**

## What ran

BTC/USDT spot, 2,016 five-minute candles from 2024-06-01 00:00 UTC inclusive to
2024-06-08 00:00 UTC exclusive. Both accounts started with 1,000 USDT, identical 21-bar
warmup and market observations, 0.1% fee per side and 0.1% adverse slippage per fill.
The baseline uses a 20-bar breakout with a 2% price stop and 4% target. Jev selects ENTER
or WAIT for the same candidate definition; deterministic code retains all risk authority.
No teacher, learned memory, parameter tuning or real exchange orders were involved.

This is development data that overlaps earlier baseline research, not a sealed holdout.
The candidate limit was fixed at 100 before execution, inside the approved USD 3/month
allowance. The prompt and strategy were unchanged from `0c84bc1`.

## Results

| Metric | Fixed breakout baseline | Jev filter with 100-attempt cap |
| --- | ---: | ---: |
| Ending marked equity (USDT) | 1,000.623855 | 1,001.785873 |
| Trading P&L after simulated fees/slippage (USDT) | +0.623855 | +1.785873 |
| Trading return | +0.062385% | +0.178587% |
| Maximum sampled drawdown | 0.755254% | 0.357227% |
| Closed trades | 7 | 2 |
| Open positions at end | 1 | 0 |
| Complete UTC days | 7 | 7 |
| Daily Sharpe | Unavailable: fewer than 30 days | Unavailable: fewer than 30 days |
| Successful model choices | 0 | 100: 98 WAIT, 2 ENTER |
| Unevaluated candidates after attempt cap | 0 | 11 |
| Model/API failures | 0 | 0 |
| Accounted inference cost (USD) | 0 | 0.009907590 |

Cash reference: 0% trading return. Jev's observed return was approximately 0.116202
percentage points higher, but its policy stopped evaluating candidates after the cap.
That changes exposure and makes this unsuitable for claiming unrestricted Jev performance.
Two closed Jev trades are far too little evidence to infer a durable advantage or learning.
Baseline ending equity includes an open position and excludes its future liquidation cost.
One week/asset, coarse candles, zero modeled decision latency and possible historical
pretraining contamination further limit interpretation. No confidence score is treated as
a probability of profit. Both implementations may lose money in other periods.

AI cost is reported in USD separately from trading P&L in USDT; no implicit exchange-rate
assumption is used to combine them. The 100 successful receipt costs exactly equal the
shared budget increase. There are no pending/failed response receipts or unresolved budget
reservations. Total monthly accounted spending after the run is USD 0.010000914, including
earlier integration checks; USD 2.989999086 remains under the application cap.

## Provenance and reproducibility

Source ZIP: `BTCUSDT-5m-2024-06.zip`, checked against its official Binance SHA-256 file.
[Binance's source format and checksum documentation](https://github.com/binance/binance-public-data)
describes the kline columns, archive verification and timestamp units. The importer makes
no gap filling, interpolation or price adjustments.

- Source ZIP SHA-256: `627dd48125d89759e498d2db2e523166787bda4dd9a64ca56abf9fba235ba71e`
- Selected CSV SHA-256: `1b93a39e68ed677167db302f29b5065a3080f76c682e1e851df02c7a0358c037`
- Replay source hash (identical in both checkpoints): `d4171a56d03cc298e78b0b7ac41477a52052ddfde5bb2b34e1e3761adde3d516`
- Baseline journal SHA-256: `107b7d9fba3f9bede1d49aa2cb2e09ff47b4609804d9f1df739768d7ecbe8b7b`
- Jev journal SHA-256: `e7e4642df44a226291832aff2a6ea3256325da2a9c15ec4f9f2a91392b02bdc5`

Local artifacts live under ignored `user_data/research/btc-week-2024-06-v1/`: the official
checksum, normalized CSV/provenance manifest, baseline/jev journals, Jev response store,
pre-run budget snapshot and reconciled `comparison.json`. Recorded responses preserve the
observed choices; a new provider request is not guaranteed to reproduce them. Preserve
these artifacts rather than recreating or extending the completed journals.

The generated cockpit is `user_data/cockpit/index.html`; `src/cockpit/template.html` is
only its source template and contains no saved results. The cockpit shows a degraded-coverage
warning for this comparison and retains a separately labeled legacy baseline archive.

## Next decision

Do not promote or tune from this pilot. Predeclare a wider development protocol with a
candidate schedule that fits the budget without silently dropping the end of the sample;
then compare frozen variants and cash/buy-and-hold controls across multiple windows. Keep
final holdout data separate. Teacher/memory and online operating controls remain unimplemented.
