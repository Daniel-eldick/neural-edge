# Opportunity screen v1 — stopped; comparison incomplete

**The four-window study did not complete.** The first context run recorded a TypeSafe connection
failure. Its partial performance is retained and flagged; it is not eligible evidence for
comparing agent quality. The three later windows were never run. No failed request was retried,
no trial was replaced, and no extra paid trial followed the failure investigation.

Protocol commit **`2ce4894`** preceded data acquisition on 2026-09-30. Frozen implementation
was `44287a5`. Source hashes matched at study close. The subsequent failure-gate repair changes
future runtime behavior only; this study and its journals were not rerun or rewritten.

## Predeclared windows and actual execution

BTC/USDT 5m, 10th 00:00 UTC to 12th 00:00 UTC, end exclusive. Independent 1,000-USDT accounts,
576 bars, first21 warmup, .001 fee/side, .001 adverse slippage, unchanged risk/entry/exit rules.
Memory begins empty. Fixed calendar dates once per quarter; no assumption the periods rise.

| Window | Raw candidate bound | Daily / weekly initially available | Execution |
| --- | ---: | --- | --- |
| 2024-02 10–12 | 35 | Yes / yes | Baseline and memory clean; context degraded |
| 2024-05 10–12 | 25 | Yes / yes | Not run after earlier failure |
| 2024-08 10–12 | 26 | Yes / yes | Not run after earlier failure |
| 2024-11 10–12 | 54 | Yes / yes | Not run after earlier failure |

## Preserved first-window observations — not a valid paired comparison

| Policy | Return after trading costs | Sampled max drawdown | Closed / open | Successful decisions | Policy errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| breakout-baseline-v1 | +0.2414% | 0.2581% | 1 / 1 | 0 | 0 |
| Cash reference | +0.0000% | 0.0000% | 0 / 0 | 0 | 0 |
| Buy & hold reference | +1.8582% | 1.2340% | 0 / 1 | 0 | 0 |
| jev-memory-filter-v1 | +0.2765% | 0.2378% | 1 / 0 | 16 | 0 |
| jev-context-filter-v1 | -0.0221% | 0.2360% | 1 / 0 | 21 | 1 |

Diagnostic arithmetic only: context minus memory **-0.298655pp**,
minus baseline **-0.263556pp**, minus buy-and-hold **-1.880312pp**.
The missing model evaluation makes those differences unsuitable for judging context quality.
This first market period rose in the holding reference; context did enter once, so the previous
all-cash behavior was not universal. Neither fact establishes reliable timing, adaptation or learning.
Buy-and-hold allocates the entire account at common bar21 open with costs, no stop or 24h exit;
final holdings have no hypothetical liquidation costs. Higher exposure makes its gap descriptive,
not attainable foregone profit. USDT trading returns exclude USD AI spending.

## Failure and conservative accounting

Failure at historical decision time **2024-02-11T23:55:00+00:00**:
`TypeSafe connection failed; full reservation retained`. The safe error records a connection
exception, not its underlying network cause; timeout versus another connection fault is unknown.
Provider processing/billing of the uncertain request is also unknown. Do not assume it was free.

The old runtime vetoed that candidate, kept simulating protective exits, then issued **one
distinct later request**. The runner only checks errors after each replay returns, so it stopped
subsequent windows, not immediately all calls within the current run. No retry of the failed key
occurred. This reliability gap motivated the separate durable response-store failure gate.

- **37 successful requests**, one failed/uncertain attempt.
- Verified receipt costs: **USD 0.007903602** (memory .001695078; context .006208524).
- Uncertain reservation retained unchanged: **USD 0.003000000**; this is not confirmed spending.
- Total ledger increase: **USD 0.010903602**, exactly receipts plus retained reservation.
- Monthly accounted amount: **USD 0.079878438**; remaining **USD 2.920121562**.
- One unresolved reservation remains. No manual settlement/reset or further paid trial.
- Memory-only decisions with prior reviewed trades: 3; context: 2. Both reviewed one closed trade.

Exact successful response hashes/choices/costs were matched to journal events; every context
request (including the failed one) matched the closed-history snapshot and memory cutoff.
Completed checkpoints, shared input/settings identity, old/new artifact hashes and ledger delta
were audited read-only. The normal comparison validator correctly rejects this pair with
`Comparison candidate coverage is incomplete`. It was not weakened or bypassed to label a pass.

## Provenance and limitations

Sixteen checksum-verified [Binance monthly spot archives](https://github.com/binance/binance-public-data):
one 5m and three 1d per window. Daily starts 2023-12-01, 2024-03-01, 2024-06-01, 2024-09-01;
each ends at its test end. Every replay day reconciled with daily OHLCV (rtol1e-9, atol1e-8).
No missing rows repaired. Pinned model and price rechecked against [TypeSafe models](https://docs.typesafe.ai/models).

| Window | Intraday CSV SHA-256 | Daily CSV SHA-256 |
| --- | --- | --- |
| 2024-02 | `7eeb027f6591e0126427cbd0513da2552a760d4cbd71a6dbe8ae73a8ae989276` | `4f86780dc7797ca7b73a51c4a949d1d496732936b85f277041fcfea5de41dc9e` |
| 2024-05 | `abe33a389caa9c87d25c23a5920f38e255699740bbe1ff02be9071cd2b89dd21` | `ed0ed81a35a3de53984120a8ed9e63ee3d4567a32cbca9e5f849d8d457cefa7c` |
| 2024-08 | `dfebd00f7a5d1eab28d3051af63d875503193c0eb691881c84087b16847a97ff` | `3c25ea3967369ddbe53a614ebb6b5872effcf201ee8d9aaae0d0595bd11bf1cc` |
| 2024-11 | `5eb7a6ae2fa9c4eb947cae02c02abb3c15a88c518179dd28b4b29ee5bf5dbca8` | `dbf822418452e24afaafcc8aca182cd75301a2cbfcdc889f8b939444268a8004` |

Tested closed-bar and memory cutoffs limit leakage paths but do not rule out model pretraining
or historical-feed revisions. Context changes instructions as well as input; prompt/content
confounding remains. Candle fills omit measured spreads/latency, queueing and partial fills.
No forward paper operation or live order. Do not promote, claim learned edge, or tune/retest
consumed periods to manufacture improvement. Resolve provider accounting evidence and use a
new frozen protocol before further paid comparisons. Prospective paper evidence remains needed.

Ignored evidence: `user_data/research/opportunity-screen-v1/` contains sources/manifests,
preflight, execution-start/failure JSON, three journals/two response stores, stdout/stderr,
`partial-audit.json`, `evidence-hashes.json`, `published-cockpit.html` and execution script
copies archived as `.py.txt` (verbatim evidence, not imported application modules). No completed
comparison JSON is claimed. Later directories contain data only. No tokens or responses in Git.

Private cockpit retains all 33 earlier records plus five first-window records (38 total),
with eight dated comparison groups. February context is selected by fixed input order and
shows an incomplete-test warning. Static snapshot, not live monitoring or controls.

[Failure-gate review and QA](../reviews/2026-09-30_OPPORTUNITY_SCREEN_QA.md).
[Private cockpit access](../guides/COCKPIT_HOSTING.md).
