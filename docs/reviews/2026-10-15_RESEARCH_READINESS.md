# Research-readiness review — 2026-10-15 Beirut

Scope: requested parallel Codex investigation, next-evaluation design and cumulative-PR audit.
Baseline: `eb879f67004e788a6db18e59c80a96adf72b94c1` on `codex/apprentice-cockpit`.
Implementation branch: `codex/research-readiness`; intended base: `develop`.

## Completed

- Read-only `--audit-budget` surfaces unresolved reservations across all UTC months. It
  neither creates a missing ledger nor changes reservations, settlement or response gates.
- Paired evaluation now checks request model, options, instructions, exact 21-candle causal
  prefix, candidate prices/key and matching execution-engine source hashes. Six regression
  cases failed before the repair and passed afterward. Independent agent review found no
  blocking issue in this repair.
- Four additional budget/CLI tests verify earlier-month visibility, settled omission, byte
  preservation, missing/corrupt ledgers and credential/network-free auditing.
- [Controlled context screen v2](../research/CONTROLLED_CONTEXT_SCREEN_V2.md) records the next
  study design. Its three matched arms/validator and execution manifest are not implemented;
  the design is not an executable or completed experiment.
- Removed four obsolete TA-Lib type-ignore comments exposed by fresh dependency installation.
  Indicator logic and risk settings are unchanged.

## Fresh verification

Python 3.12.14, pytest 9.1.1, mypy 2.4.0, TA-Lib 0.8.2.

| Check | Result |
| --- | --- |
| `.venv/bin/ruff check .` | Pass |
| `.venv/bin/mypy --no-native-parser -n 0 --cache-dir=/tmp/neural-edge-final-mypy .` | Pass, 68 source files |
| `.venv/bin/pytest -x --timeout=30` | 257 passed, 17 pre-existing sensory expected failures |
| `node --test web/cockpit/test/*.test.mjs` | 6 passed |
| `git diff --check` | Pass |

Default mypy crashes in this container during psutil process discovery (`NoSuchProcess`,
PID 2). Disabling its native parser/worker path and using a fresh cache bypasses that tool
runtime issue without disabling project type checks. Full dependency locking and verification
on the original host remain outstanding; this is not a claim of a reproducible locked build.

## Findings and limits

The historical September connection error did not preserve a transport subtype or provider
request ID. Exact network cause and billing cannot be recovered from the committed report.
The historical USD 0.003 reservation stays unresolved. The original private ledger, response
stores and market journals are absent from this checkout, so no current balance or historical
artifact hash verification is claimed. Use the audit command on the authoritative original host
and obtain provider evidence; do not initialize a substitute ledger or assume a new month clears
uncertainty. The failure gate is per response store, not a global account lock.

The validation gaps are evidence-integrity weaknesses, not proof prior studies were contaminated.
The strengthened validator still trusts local artifacts and does not fully reconstruct portfolio
or memory facts. Freeze new policy versions if prompts change; retain historical source contracts.
The cumulative audit found no additional confirmed replay/risk/recovery defect in this review,
which is not an exhaustive safety certification or blanket approval to merge prior work.

No paid inference, market-data acquisition, replay of consumed experiments, ledger settlement,
unattended worker, deployment, merge or real order occurred. Existing dashboard hosting still
requires the previously documented integration setup. No performance/learning claim changed.
