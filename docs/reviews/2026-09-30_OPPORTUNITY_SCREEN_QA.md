# Opportunity screen failure and durable request gate — review and QA

Date: 2026-09-30. Branch: `codex/apprentice-cockpit`.
Plan: [single active reference](../active/APPRENTICE_TRADER_PLAN.md).
Evidence: [stopped study](../research/OPPORTUNITY_SCREEN_V1.md).
Scope: one response-store guard, two test files, preserved research evidence and protected
static snapshot. This is not a review/approval of the cumulative draft PR's predecessor work.

## Research outcome — incomplete, preserved

Fixed protocol `2ce4894` preceded sixteen archive acquisitions. All four data windows passed
checksum/continuity/daily-overlap checks; candidate bounds 35/25/26/54 fit the original cap.
February baseline and memory completed with zero errors. Context had one connection failure,
then one distinct later request under unchanged `44287a5` runtime. Failed key never retried.
Runner stopped subsequent windows after the replay returned. May/August/November never ran.
The normal paired validator rejects `Comparison candidate coverage is incomplete`; no clean
comparison or completed four-window outcome is claimed. Diagnostic partial returns stay visible.

Read-only audit matches 37 successful receipts to events and exact source-cutoff context/memory,
verifies the one failed request, and reconciles USD .007903602 known cost + .003 retained
uncertain reservation = .010903602 ledger increase. Monthly accounted .079878438, remaining
2.920121562, one unresolved reservation. Accounting uncertainty remains; no ledger repair,
reset or speculative settlement. Source hashes matched at study close before the separate fix.
Fifteen memory-screen, fifteen context-screen and five new journal/receipt hashes remain intact.
No new paid request followed the study. Later code/test changes did not alter its results.

## Code review — Standard tier

**APPROVED for the scoped reliability repair. No unresolved blocking finding.**

| Requirement | Evidence | Result |
| --- | --- | --- |
| Failed/pending attempt blocks all new keys | New response-store query precedes insert/network | PASS |
| Durable across reopening | Stored attempt status is the gate; no volatile latch | PASS |
| Concurrent distinct requests cannot bypass pending state | Query and insert share existing BEGIN IMMEDIATE; two-connection test | PASS |
| Successful cached recovery remains usable | Existing key validation/return precedes gate; provider count unchanged in tests | PASS |
| Protective exits remain independent | Existing two-policy multi-symbol stop tests pass; no engine/risk change | PASS |
| All Jev variants inherit gate | Resume integration tests for jev, jev-memory, jev-context | PASS |
| Persistence uncertainty blocks new requests | Injected failed SQLite update leaves pending row; same/reopened connection tests | PASS |
| No misleading success | Policy errors retained; cockpit incomplete warning; comparison validator rejects old failure | PASS |
| Recovery identity | Existing policy fingerprint includes responses.py; changed source cannot resume old run | PASS |
| Cost and security | No ledger/token/config/evaluator changes; no new dependency or provider call | PASS |

Regression reproduced first: `test_failure_blocks_new_keys_across_reopen_but_allows_cached_answers`
failed on original source with `DID NOT RAISE ResponseError`. The new guard made it pass.
Six new test cases plus stronger persistence-failure assertions cover the repair. Cached successes
remain validated for matching request/checksum/schema. Gate inspects at most100 attempt rows
in supported replay runs; local SQLite work only, no new external request or unbounded buffer.
A still-running pending request may settle normally; new claims remain blocked while pending.
Interrupted/failed records are not automatically cleared. This is per response store, not a
provider-wide health breaker or a repair mechanism for the unresolved global ledger charge.

Fresh-context reviewer independently traced the scoped diff, ran 27 focused tests plus focused
Ruff/mypy, and approved without blocking findings. No paid call, file edit or deploy by reviewer.
The failure gate changes future policy identity; all observed study results remain from frozen old
source. Model/prompt/risk changes, tuning and historical reruns were explicitly excluded.

## QA — Full tier

**PASS WITH WARNINGS for the repair and honest publication. The research comparison remains incomplete.**

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Plan | PASS | Three corrective tasks complete; stopped original study explicitly separate |
| 2 | Landmine registry | WARN | Legacy .Codex/landmines.md absent; .claude/landmines.md has no patterns |
| 3 | Lint | PASS | `.venv/bin/ruff check .`: All checks passed! |
| 4 | Types | PASS | `.venv/bin/mypy .`: Success: no issues found in 66 source files |
| 5 | Full tests | PASS | `.venv/bin/pytest -x --timeout=30`: 234 passed, 17 xfailed in 6.09s |
| 6 | DB security advisor | SKIP | No hosted database/migration; existing local SQLite transaction reviewed |
| 7 | DB performance advisor | SKIP | No hosted DB; bounded local attempt scan |
| 8 | Tenant isolation | SKIP | No tenant service; per-run response identity retained |
| 9 | Scope | PASS | Three corrective tasks; one source/two test files plus declared evidence/docs |
| 10 | Actual integration | PASS | Failure preserved and audited; original comparison rejected; no retry/new paid trial |
| 10b | Hosting | PASS | READY preview, target null, empty aliases; authentication retained; anonymous302 login |
| 10c | HTML integrity | PASS | Authenticated curl completed, then cmp with local report exited0 |
| 10d | Browser | PASS | 1440×1050 desktop, 820×1180 tablet, 390×844 phone; zero errors/overflow |
| 10e | Controls and warning | PASS | Incomplete test visible, chart click/keyboard, evidence/run/group disclosures work |
| 10f | Visual inspection | PASS | Phone screenshot: February dates, -0.02%, 1 trade, 1 unavailable evaluation, warning, 38 records |
| 11 | Evidence language | PASS | No clean-pair, profit, learned-edge, billing-certainty or unattended-readiness claim |

Full source gate initially passed 228 tests before protocol commit. The later 234-test run
validates the guard. Existing17 sensory expected failures remain documented; no new xfail/skip.
Self-corrections: two long lines wrapped; a new test's guessed warning string corrected to the
existing `Incomplete test` UI text. Verbatim ignored execution-script copies were archived as
`.py.txt` evidence after mypy treated those scratch copies as application modules. No source
code checks, assertion coverage, type configuration or quality thresholds were weakened.

Chrome DevTools MCP unavailable; permitted Playwright CLI fallback used. Credential reused in
memory, header restricted to exact preview origin, other origins blocked. No credential output.
Eight comparison tables, 44 SVGs, no expanded overflow. Screenshot/result artifacts:
`/private/tmp/neural-opportunity-study-mobile.png`,
`/private/tmp/neural-opportunity-study-browser-check.json`.
Hosted HTML verification: `/private/tmp/opportunity-study-hosted.html`.
Deployment: `dpl_9eNE8J213h15injrq4WVm2Dxv3xu`; [access guide](../guides/COCKPIT_HOSTING.md).
Only static HTML/config from isolated staging; existing plan, no alias/worker/order/main promotion.

## Remaining limits

The uncertain USD .003 reservation needs authoritative provider usage evidence; leave it reserved
until then. Do not retry/replace the failed study to obtain a clean result. No more paid runs
under this protocol. The missed-opportunity question is unresolved; prospective paper evidence,
prompt/content controls and broader market tests remain future work. Historical pretraining,
archive delivery/revisions and candle execution assumptions remain limitations. Private cockpit
is a dated snapshot. Keep cumulative PR draft until predecessor reconciliation and broader review.
