# Context comparison screen v1 — review and QA

Date: 2026-09-30. Branch: `codex/apprentice-cockpit`. Fixed protocol: `c0ad832`.
Runtime/prompt baseline: `19ed060`; source hashes verified unchanged before/after all trials.
Plan: [context-screen-v1](../active/APPRENTICE_TRADER_PLAN.md).
Results: [complete study](../research/CONTEXT_SCREEN_V1.md).
This review covers four evaluation/test files and supporting docs, not the cumulative draft
PR's unmerged predecessor implementations.

## Code review — Standard tier

**Verdict: APPROVED for the bounded read-only data/evaluation increment.**
No unresolved blocking finding. Six declared tasks completed without risk/policy changes.
Failing tests preceded the new importer and study mode; source/tests are committed together
(test-with). The separate context variant is unchanged and received only the predeclared data.

| Rule | Verification | Result |
| --- | --- | --- |
| Fixed dates before data | Protocol commit precedes acquisition; original calendar periods retained | PASS |
| Strict daily source | `convert_daily`: exact monthly filenames, sidecar SHA, bounded ZIP/member, twelve kline columns, every UTC daily open/close, no missing days or repairs | PASS |
| Intraday/daily consistency | `reconcile`: aggregate 288 intraday bars per UTC day; OHLCV tolerance 1e-9 relative / 1e-8 absolute | PASS |
| Adequate prior context | Both frames available at first eligibility in all three windows; daily ranges fixed before acquisition | PASS |
| Exact causal model input | Context receipt equals `MarketContext.snapshot(symbol, cutoff)`; injected/altered/missing context rejected | PASS |
| Control isolation | Context rejected in memory-only receipt; existing legacy memory-screen default remains unchanged | PASS |
| Source binding | Context manifest SHA and checkpoint policy identity must bind supplied daily CSV | PASS |
| Completed comparable runs | Existing CSV/settings/checkpoint/data/receipt validation and zero-error requirement retained | PASS |
| Full candidate coverage | Raw bounds 36/25/27 ≤100; six model runs complete, 173 receipts, zero policy errors | PASS |
| No outcome selection | One run per policy/window; no reruns, altered dates, expanded limits or discarded failures | PASS |
| Spending and evidence | Exact USD 0.035785470 ledger increase equals receipt costs; no unresolved reservations; old/new hashes unchanged | PASS |

Fresh-eyes review independently checked all four source/test files, ran targeted tests and a
control-context injection probe, and found no blocking issue. Its full gate also passed.
Generic helpers do not independently enforce the entire study protocol (selected dates/source
acquisition/frozen source); execution preflight and preserved manifests/hashes provide that
study-specific evidence. Checksums are not a cryptographic attestation of exchange truth.

Implementation corrections: ordinary lint/test typing, and a synthetic fixture serialized
integers while the real CSV parser uses floats. The fixture now uses the same canonical
numeric input type; the production dataset hash check was retained. No study was rerun or
validation weakened to accept observed results. No unresolved code-review findings remain.

Scale/failure: max12 daily archives, each compressed/member bound 4MiB; selected range ≤10,000
rows; no extraction paths, new dependency, hosted DB or automatic dataset repair. Invalid
sources fail before output. Receipts/journals are read-only. Model calls use the unchanged
shared budget, maximum attempts, timeout and no-retry behavior. Dataset/run failures remain
saved rather than generating replacements. Local files/policies remain trusted.

## QA — Full tier

**Verdict: PASS WITH WARNINGS for this increment; not full-product readiness or merge approval.**

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Plan | PASS | Six tasks; protocol committed before acquisition, execution and publication recorded |
| 2 | Landmine scan | WARN | `.Codex/landmines.md` absent; missing registry not counted as a pass |
| 3 | Lint | PASS | `.venv/bin/ruff check .` → `All checks passed!` |
| 4 | Types | PASS | `.venv/bin/mypy .` → `Success: no issues found in 66 source files` |
| 5 | Full tests | PASS | `.venv/bin/pytest -x --timeout=30` → `228 passed, 17 xfailed in 7.44s` |
| 6 | DB security advisor | SKIP | No hosted DB/migration |
| 7 | DB performance advisor | SKIP | No hosted DB/migration |
| 8 | Tenant isolation | SKIP | No tenant service; experiment/source identity checked directly |
| 9 | Scope | PASS | Six planned tasks, no >1.5× expansion; no trading or UI behavior change |
| 10 | Actual integration | PASS | Twelve checksum-verified archives; nine completed replays, exact 173 receipts and shared ledger reconciliation |
| 10b | Protected hosting | PASS | READY preview, target null, no aliases; project authentication enabled; anonymous HTTP302 login redirect |
| 10c | Hosted content | PASS | `cmp user_data/cockpit/index.html /private/tmp/context-study-hosted.html` exit0 |
| 10d | Browser | PASS | Authenticated Chromium: 1440×1050 desktop, 820×1180 tablet, 390×844 phone; zero errors/overflow, chart click/keyboard and evidence expansion |
| 10e | Visual inspection | PASS | Phone screenshot inspected: October dates, 0 trades, 27 WAIT decisions, memory-only comparison and 33 saved records visible |
| 11 | Evidence language | PASS | Explicitly matches cash, no profit/learning/cycle claim; all three realized periods fell |

Thirteen new test cases cover source checksums/close boundaries/gaps/name/month-set/ranges,
overlap mismatch and output preservation, context CLI reporting, old default behavior, and
altered/missing context, manifest, checkpoint and source bytes. Existing 17 expected sensory
failures remain unchanged. Root Python instructions supersede inherited npm/Supabase examples.

Chrome DevTools MCP is unavailable; permitted Playwright CLI fallback used existing Vercel
access in memory restricted to the exact preview origin. Other origins blocked; no credentials
printed or embedded in links/screenshots. Local temporary artifacts:
`/private/tmp/neural-context-study-browser-check.json`, `/private/tmp/neural-context-study-mobile.png`.
Seven comparison tables retained, 39 SVGs, no expanded evidence overflow. An initial byte
comparison ran while download was unfinished; the authoritative comparison ran after curl
completed and passed. No page change or authentication weakening was needed.

Published deployment `dpl_AKRwNes3s2GDaUVWds8JTwUWXabw`; [access guide](../guides/COCKPIT_HOSTING.md).
Only static report/config uploaded from isolated staging using the existing account/plan.
No production promotion, alias, live order, worker or new service.

## Limits and next gate

Context abstained on all 88 candidates, so it generated zero closed-trade learning examples.
Memory-only lost about 0.50% per period; cash matched context without model cost. The study
establishes observed abstention, not profitable entry timing or learning. Larger/fresh protocols
must examine missed opportunities and broader market conditions while separating prompt and
context effects. Historical revision/publication latency, model pretraining and coarse candle
execution remain limitations. New and old completed study artifact hashes remain unchanged.

Warnings: absent landmine registry, legacy sensory xfails, static cockpit and insufficient
performance evidence. No deterministic check remains failed. Keep cumulative PR draft pending
predecessor reconciliation and broader review; no merge or main promotion performed.
