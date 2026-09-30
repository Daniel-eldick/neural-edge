# Memory comparison screen — code review and QA

Date: 2026-09-30. Branch: `codex/apprentice-cockpit`.
Protocol: `698a714`; unchanged decision/risk/replay baseline: `a3de91b`.
Plan: [memory-screen-v1 increment](../active/APPRENTICE_TRADER_PLAN.md).
Results: [actual study report](../research/MEMORY_SCREEN_V1.md).
Scope: new read-only evaluation helpers, cockpit comparison presentation, tests and evidence.
This review does not approve the cumulative draft PR's unmerged predecessor foundations.

## Code review — Standard tier

**Verdict: APPROVED for this bounded increment; no unresolved blocking findings.**
All six planned tasks have corresponding implementation or recorded execution evidence.
The small cockpit changes implement the declared dated comparison UX; no new operating controls.
Failing tests were exercised before helper/CLI implementation and before integrity corrections.
Source and tests are committed together (test-with under the skill's Git classification).

| Business rule | Implementation / evidence | Result |
| --- | --- | --- |
| Fixed windows and original decisions | Protocol committed before acquisition; before/after source hashes match | Verified |
| Full candidate coverage | `screen.candidates` bounds raw breakout eligibility; ceilings 42/33/49, all below 100; nine completed runs, no policy errors | Verified |
| Comparable inputs | `window_runs` validates dates, symbol, CSV hash, completed checkpoints and numeric settings; equal settings canonicalized for grouping | Verified |
| Authentic recorded model choices | `receipt_evidence` validates response-store identity, completed receipts/checksums, every parsed choice field, timestamps, symbols, counts and costs against journal | Verified |
| No future supplied evidence | Receipt validation rejects future candles, cases, reviews and curriculum; unchanged policy causal tests pass | Verified for supplied input; model pretraining remains outside this guarantee |
| Fairly labeled references | `references` buys only at common bar 21 open, charges entry costs, marks final holdings; full allocation explicitly differs from risk-governed bot | Verified |
| Preserve evidence | Read-only SQLite access; CLI refuses existing output paths; original pilot and completed study artifact hashes unchanged | Verified |
| No misleading summary | Three separate dated groups; last window selected by input order; frozen comparator preferred for memory; improvement unproven | Verified |
| Spending accountability | Receipt costs equal ledger delta: USD 0.023188452, 223 calls, no pending reservations | Verified |

### Findings resolved before completion

Self-corrected **four findings in three rounds**; no findings were removed by reducing scope.

| Round | Finding | Correction and verification |
| --- | --- | --- |
| 1 | HIGH: equal receipt counts/costs alone did not bind recorded choices to model replies | Compare all parsed decision fields and request identity/time; same-cost forged-choice regression rejects alteration |
| 1 | HIGH: completed checkpoint could claim a different candle dataset | Bind checkpoint dataset to canonical loaded candle hash and length; forged-contract regression rejects alteration |
| 2 | MEDIUM: integer CLI balance and equal float default settings falsely rejected a valid study | Compare decoded numeric settings; actual CLI integer-balance regression passes |
| 3 | MEDIUM [fresh-eyes]: accepted numeric equivalents still produced separate string-based UI groups | Canonicalize comparison key only after integrity checks; mixed int/float fixture yields one group |

Independent agent re-review verified the corrections and reran the twelve evaluation cases.
Its final assessment found no remaining blockers. Full checks below ran after the final source
change. Reporting fixes used completed evidence only; no paid study was rerun or retuned.

No dependency, exchange API fanout, trading-policy change or evaluator modification.
CSV readers reject malformed/mixed/gapped data and cap input at 100,000 bars. Current studies
have 864 bars each; journals are read locally. At ten times the planned study load, keep fixed
per-study bounds and explicit scheduling; this is not a continuous/distributed worker design.
Credentials and journals remain outside the hosted static snapshot. Local files/code are trusted;
checksums and cross-checks are corruption defenses, not independently signed provider evidence.

## QA — Full tier

**Verdict: PASS WITH WARNINGS.** No deterministic failures remain for the increment.
Inherited npm/Supabase commands are inapplicable; root AGENTS.md supplies Python checks.

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Plan | PASS | Six tasks completed against protocol fixed before acquisition |
| 2 | Landmine registry | WARN | `.Codex/landmines.md` is absent; no claim that its missing patterns were checked |
| 3 | Lint | PASS | `.venv/bin/ruff check .`: `All checks passed!` |
| 4 | Types | PASS | `.venv/bin/mypy .`: `Success: no issues found in 61 source files` |
| 5 | Tests | PASS | `.venv/bin/pytest -x --timeout=30`: `190 passed, 17 xfailed in 7.29s` |
| 6 | Hosted database security advisor | SKIP | No hosted database or migration |
| 7 | Hosted database performance advisor | SKIP | No hosted database or migration |
| 8 | Tenant isolation | SKIP | No multitenant service; experiment identity isolation tested |
| 9 | Scope | PASS | Six tasks; read-only helpers, bounded presentation changes, tests and documentation |
| 10 | Browser integration | PASS | Authenticated Chromium: 1440×1050 desktop, 820×1180 tablet, 390×844 phone; no console/page errors or horizontal overflow |
| 10b | Interaction and visual inspection | PASS | Click/keyboard chart switching, expanded evidence, run 18 and January group; four comparison tables retained, 24 SVGs; mobile screenshot inspected |
| 10c | Deployment access | PASS | READY preview, no aliases; authentication enabled; anonymous redirect to login; authenticated HTML byte-identical to local report |
| 11 | Evidence language | PASS | Tiny sample and limitations explicit; no profitability, learning, live-operation or total-completion claim |

Twelve evaluation tests cover candidate bounds, exact reference accounting and warmup,
strict datasets, missing/wrong policies, recorded-provider CLI integration, settings/hash/
partial/receipt mismatch, same-cost altered choices, dataset-contract forgery and integer/float
settings equivalence. Cockpit regression checks frozen comparator preference and dated summaries.
The seventeen expected failures are pre-existing legacy sensory integration gaps, not new skips.

Chrome DevTools MCP is unavailable; the skill's permitted Playwright CLI fallback used bundled
Chromium. Existing Vercel credentials stayed in memory, restricted to the exact preview origin;
other origins were blocked. No credential was printed or added to a URL. Temporary raw browser
results: `/private/tmp/neural-edge-browser-check.json`; images `/private/tmp/neural-edge-*.png`.
Durable hosting instructions: [cockpit access](../guides/COCKPIT_HOSTING.md).

Warnings: absent landmine registry; seventeen existing sensory expected failures; static UI
has no refresh worker, operating controls or real-user learnability study. Historical model
pretraining, only three closed memory trades, changed prompt instructions and single draws
prevent attribution of a reliable learning effect. These are not erased by passing software QA.

`dry_run: true` remains unchanged; locked `src/autoresearch/prepare.py` is untouched. No live
orders, unattended process, main promotion or PR merge. Keep the cumulative PR draft until
its predecessor branches and broader scope are reconciled and reviewed.
