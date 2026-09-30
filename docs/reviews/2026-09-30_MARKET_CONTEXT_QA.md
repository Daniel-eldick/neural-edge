# Causal daily/weekly context v1 — review and QA

Date: 2026-09-30. Branch: `codex/apprentice-cockpit`. Increment base: `850efc9`.
Plan: [daily/weekly context v1](../active/APPRENTICE_TRADER_PLAN.md).
Scope: two new agent modules, replay CLI, existing cockpit labels/evidence, tests and docs.
This report does not approve the cumulative draft PR or its unmerged predecessor branches.

## Code review — Standard tier

**Verdict: APPROVED for the bounded opt-in offline increment. No unresolved blocking finding.**
All six planned tasks have code/test/evidence coverage. Test scaffolding failed before the
new modules, new CLI mode and context comparator existed; Git contains source/tests together
(test-with). Existing frozen and memory-only prompts, engine/risk, budget and teacher source
are unchanged. The CLI is part of the existing recovery source fingerprint, so older unfinished
runs require their original revision; completed journals remain readable.

| Rule | Code / verification | Result |
| --- | --- | --- |
| Closed daily bars only | `MarketContext._frame`, bisect at `opened_at + 86400 <= now`; exact boundary and future-suffix tests | Verified |
| Complete Monday weeks only | Seven contiguous midnight daily rows, Monday alignment, weekly close cutoff; hand-calculated OHLCV test | Verified |
| Unknown when insufficient/stale | 20-day / 8-week minimum and latest calendar boundary; null descriptors, explicit reason | Verified |
| No implicit bull-cycle forecast | Numeric trailing return/range and sign only; contextual instructions explicitly reject that inference | Verified; model obedience is not assumed as a risk boundary |
| Bounded data and payload | 4 MiB read bound, 10,000 rows, one contiguous symbol; 30 daily / 12 weekly request rows | Verified |
| Future suffix cannot influence earlier requests | Full-file hash outside prompt; altered future candles produce identical snapshots and recorded requests | Verified for valid supplied data |
| Recovery binds source | Context CSV bytes and new module hashes join existing policy identity; changed source rejected before another call | Verified |
| No duplicate paid request after crash | Actual replay/journal/store fixture crashes after saved response; resumed events match uninterrupted run, provider count unchanged for reused response | Verified |
| Existing protection remains active | Context provider failure records a veto; existing position exits and run ends with no open positions | Verified |
| Honest cockpit identity | Distinct context+memory label, memory metrics, dated context records, memory-only comparator | Verified |
| No accidental real study | Mocked HTTP/recorded providers only; no paid calls, no synthetic QA artifact published | Verified |

### Corrections and independent review

During implementation, lint findings and a duplicate local type annotation were corrected.
The full test run then exposed an incorrect *test expectation*: zero-range descending daily
candles produce a nonzero weekly high-low range. The correction asserts the exact weekly
arithmetic (`mean(6 / weekly_open)`); production aggregation was not weakened or changed.
Independent fresh-eyes review confirmed this correction and found no blocking production
issue. Its focused regression suite passed **43 tests in 1.43s**; changed-file Ruff passed.

Self-corrected: lint/type-check issues during implementation, one QA test expectation, and
one browser-test selector. No test was removed, skipped or changed to accept a faulty runtime
behavior. The browser selector was narrowed to the specific decisions disclosure, which
coexists with a separate assumptions disclosure. Final evidence below supersedes those runs.

Scale: one bounded daily CSV load, O(n) weekly preparation, O(log n + 42) selection per
candidate. No new network call, per-candidate file read, unbounded cache, dependency or hosted
service. Numeric overflow is explicitly rejected. The adapter and local history remain trusted
code/data; checksums detect changes, not vendor authenticity or malicious coordinated rewriting.

## QA — Full tier

**Verdict: PASS WITH WARNINGS for this increment.**

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Plan/spec | PASS | Six tasks implemented; broader pattern library and performance study explicitly pending |
| 2 | Landmine scan | WARN | `.Codex/landmines.md` absent; no fabricated registry pass |
| 3 | Lint | PASS | `.venv/bin/ruff check .` → `All checks passed!` |
| 4 | Types | PASS | `.venv/bin/mypy .` → `Success: no issues found in 64 source files` |
| 5 | Full tests | PASS | `.venv/bin/pytest -x --timeout=30` → `215 passed, 17 xfailed in 5.18s` |
| 6 | Hosted DB security advisor | SKIP | No hosted DB/migration |
| 7 | Hosted DB performance advisor | SKIP | No hosted DB/migration |
| 8 | Tenant isolation | SKIP | No tenant service; source/symbol/run isolation covered directly |
| 9 | Scope guard | PASS | Six tasks, no >1.5× expansion; no new trading rule or worker |
| 10 | CLI integration | PASS | Mocked actual HTTP client + temporary budget, context option/provenance path, pause/resume, one request only, secret exclusion; invalid flag combinations/symbol fail before journal creation |
| 10b | Local browser | PASS | Chromium 1440×1050, 820×1180, 390×844: no page/console errors or horizontal overflow; chart click/keyboard, evidence and context records visible |
| 10c | Visual inspection | PASS | Phone screenshot inspected; context label, comparison control and memory summary fit existing layout; synthetic warning visible |
| 11 | Evidence language | PASS | No paid performance result, cycle recognition or learned improvement claimed |

Twenty-five additional passing cases include twenty in `tests/test_market_context.py`, four
CLI cases and one comparator case. The seventeen xfails are the same documented legacy
sensory integration gaps. Standard root Python commands supersede inherited npm instructions.

Chrome DevTools MCP is unavailable. Playwright CLI fallback initially hit macOS sandbox
process restrictions; the authorized escalated launch succeeded. Its first interaction pass
found an ambiguous test locator; the corrected specific locator passed. This was not waived.
All browser traffic was blocked; only a clearly labeled local synthetic HTML fixture was
opened. Temporary evidence: `/private/tmp/neural-context-qa/{browser.json,phone.png,expanded.png}`.
No Vercel deployment, token access or existing account configuration change was needed.

## Preserved evidence and limits

All fifteen completed memory-screen journal/receipt SHA-256 values match their saved manifest.
Budget status remains **USD 0.033189366 accounted / USD 2.966810634 remaining / zero unresolved
reservations**. No real inference was made in this increment. The hosted cockpit still shows
actual completed memory-screen results; synthetic UI fixtures are not trading evidence.

Daily input origin and point-in-time publication/revision latency are not certified by this
loader. Real evaluation needs verified daily data, fresh predeclared windows, sufficient prior
history, candidate-coverage checks and frozen comparisons. Pattern-example retrieval and
multi-year-cycle validation remain unimplemented. Timestamp safety does not establish profit.

Missing landmine registry, existing sensory xfails and static-only operation remain warnings.
No risk-limit/evaluator change, unattended process, real order, main promotion or merge.
