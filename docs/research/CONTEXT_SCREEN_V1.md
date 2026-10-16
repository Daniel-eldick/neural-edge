# Context comparison screen v1 — caution observed, edge unproven

Run date: 2026-09-30. Protocol commit **`c0ad832`** preceded source acquisition. Decision/risk/
replay/context implementation remains byte-identical to `19ed060`; before/after hashes verified.
All nine runs completed once with full candidate coverage, zero policy errors, no retries and
no replacements. Context+memory Jev declined all 88 candidates. Memory-only Jev closed one
losing trade in each period. **Context matched cash, not a demonstrated profitable strategy.**

## Results after simulated trading costs

Each BTC/USDT 5m window runs from 00:00 UTC on the 10th to 00:00 on the 13th, end exclusive.
Each policy starts an independent 1,000-USDT account; 864 candles, first21 warmup, 0.1% fee
per fill and 0.1% adverse slippage. No cross-window compounding. Risk/entry rules unchanged.

| Window | Simple breakout | Memory-only Jev | Context + memory | Cash | Buy & hold | Context − memory (pp) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022-02 10–13 | -1.5780% | -0.4998% | +0.0000% | +0.0000% | -4.7075% | +0.499791 |
| 2022-06 10–13 | -2.4741% | -0.4998% | +0.0000% | +0.0000% | -11.3511% | +0.499791 |
| 2022-10 10–13 | -0.5558% | -0.4998% | +0.0000% | +0.0000% | -2.0063% | +0.499791 |

Buy-and-hold is a full-allocation analytical reference, not risk-governed: entry at common
bar21 open with fee/slippage, no stop or 24h exit, final marked holdings with no hypothetical
liquidation costs. More exposure than the agent; not a directly interchangeable strategy.

## Coverage, decisions and cost

| Window | Raw bound | Memory calls | Context calls | Memory-exposed choices (memory/context) | Memory AI USD | Context AI USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2022-02 | 36 | 35 | 36 | 19 / 0 | $0.003910998 | $0.010617852 |
| 2022-06 | 25 | 23 | 25 | 22 / 0 | $0.002717442 | $0.007391748 |
| 2022-10 | 27 | 27 | 27 | 13 / 0 | $0.003005226 | $0.008142204 |

**173 successful requests; study cost USD 0.035785470**, exactly reconciled to the ledger.
Accounted monthly total **USD 0.068974836**; remaining **USD 2.931025164**, no unresolved
reservations. Trading P&L in USDT excludes AI spending in USD; no unstated currency conversion.
Cash matched context trading performance and required no inference spending.

| Window | Policy | Closed / open trades | Max sampled drawdown | Reviewed cases |
| --- | --- | ---: | ---: | ---: |
| 2022-02 | breakout-baseline-v1 | 3 / 1 | 2.1247% | 0 |
| 2022-02 | Cash reference | 0 / 0 | 0.0000% | 0 |
| 2022-02 | Buy & hold reference | 0 / 1 | 8.4645% | 0 |
| 2022-02 | jev-memory-filter-v1 | 1 / 0 | 0.6130% | 1 |
| 2022-02 | jev-context-filter-v1 | 0 / 0 | 0.0000% | 0 |
| 2022-06 | breakout-baseline-v1 | 5 / 0 | 2.4741% | 0 |
| 2022-06 | Cash reference | 0 / 0 | 0.0000% | 0 |
| 2022-06 | Buy & hold reference | 0 / 1 | 12.4044% | 0 |
| 2022-06 | jev-memory-filter-v1 | 1 / 0 | 0.4998% | 1 |
| 2022-06 | jev-context-filter-v1 | 0 / 0 | 0.0000% | 0 |
| 2022-10 | breakout-baseline-v1 | 2 / 1 | 0.7773% | 0 |
| 2022-10 | Cash reference | 0 / 0 | 0.0000% | 0 |
| 2022-10 | Buy & hold reference | 0 / 1 | 3.3037% | 0 |
| 2022-10 | jev-memory-filter-v1 | 1 / 0 | 0.4998% | 1 |
| 2022-10 | jev-context-filter-v1 | 0 / 0 | 0.0000% | 0 |

## Interpretation and decision

- All selected periods declined in the buy-and-hold reference. Dates were fixed by calendar
  before acquisition, but the realized sample does not cover rising or sideways markets.
- Weekly descriptors were down on every context request; daily direction was mixed. All
  daily/weekly inputs were available and matched exact reconstructed cutoff snapshots. These
  are trailing arithmetic descriptions, not an independently validated market-regime label.
- Context held no positions, closed no trades and generated no trade experience to learn from.
  Abstention avoided the controls’ losses, but supplies no evidence of profitable entry timing,
  adaptation, cycle recognition or improved model weights.
- Context changes instructions as well as input. One draw per variant cannot separate prompt
  effects, context content, stochastic variation and pretraining knowledge.
- Contemporary model pretraining and historical archive revisions remain unresolved. Candle
  fills omit spread/latency measurement, queueing and partial fills. No forward paper operation.
- Keep research status. Next evaluation must test missed opportunities, include broader market
  conditions under a fresh predeclared protocol, and separate context from prompt effects.
  Do not retune or rerun these consumed periods to manufacture an advantage. No promotion.

## Provenance and reproducibility

Downloaded checksum-verified [Binance monthly spot archives](https://github.com/binance/binance-public-data):
one 5m and three 1d ZIPs per window. Daily starts: 2021-12-01, 2022-04-01, 2022-08-01;
each ends at its test end. Every full replay day reconciled against its daily OHLCV (relative
tolerance 1e-9, absolute 1e-8). No missing rows repaired. Monthly file publication is later
than candle close; replay reconstructs historical bars, not original data-delivery timestamps.
Pinned model/pricing rechecked before execution against [TypeSafe models](https://docs.typesafe.ai/models).

| Window | Intraday CSV SHA-256 | Daily CSV SHA-256 |
| --- | --- | --- |
| 2022-02 | `82c67b35b767af0aae266b1ea6b16b3823e8a178727986840a2762d335cccfad` | `cc719ed70013ea3e85796f159df685d998bfa8642aa83f36da5c72661e551d23` |
| 2022-06 | `7c8dbe92b85649198c6137ef9b83ed2ef959c3fb1c2f356c378988e6a772c108` | `a896d1a28fc559be188bc276629bb5cda11bb109e0ec2a3bbeac5246547d028d` |
| 2022-10 | `5a6bdce08266b54be817ac3039faa6806c0a724f92245116a6254f64b3629b50` | `d88f63e23a759fb67d95de9450d5532fe0f6de962312d5896a6e9ae60a058ac3` |

All twelve ZIP hashes and download URLs are preserved in adjacent `*.manifest.json` files.
Ignored local root: `user_data/research/context-screen-v1/`. It contains source/checksum files,
CSV/manifests, nine journals, six response stores, preserved stdout/stderr, `preflight.json`,
`execution-start.json`, `execution-end.json`, `evidence-hashes.json`, `comparison.json`,
`reconciliation.json`, `cockpit.html` and `published-cockpit.html`. Completed new and earlier
study journal/receipt hashes remain unchanged. No inference responses or credentials in Git.

Regenerate a read-only report using new output paths (no model calls):

```bash
.venv/bin/python -m src.evaluation --with-context \
  --window user_data/research/context-screen-v1/2022-02 \
  --window user_data/research/context-screen-v1/2022-06 \
  --window user_data/research/context-screen-v1/2022-10 \
  --output /private/tmp/context-study-report.json \
  --html /private/tmp/context-study-cockpit.html
```

Published cockpit retains all eighteen earlier replay/reference records plus fifteen new
records (33 total). Its overview selects October context mode by input order, not best return
or latest historical date. Seven dated comparison groups retain all windows and the old pilot.
Memory-only Jev is the context chart comparator. Zero trade/review counts are intentional.

[Review and Full QA](../reviews/2026-09-30_CONTEXT_SCREEN_QA.md).
[Private cockpit access](../guides/COCKPIT_HOSTING.md).
