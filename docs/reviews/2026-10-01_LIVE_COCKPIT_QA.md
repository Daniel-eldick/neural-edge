# Live cockpit — review and local QA

Date: 2026-10-01. Branch: `codex/apprentice-cockpit`.
Plan: [single reference, October 1 live increment](../active/APPRENTICE_TRADER_PLAN.md).
Scope: new read-only Python observer, plain-JS polling shell, private storage transport/read API,
local tests and operating documentation. No engine, policy, risk, provider ledger, completed
research journal, protected evaluator or credential change. This does not approve unrelated
predecessor work in the cumulative draft PR.

## Outcome and remaining gate

**Code review: APPROVED for the scoped local implementation. Full QA: local checks pass;
online acceptance remains BLOCKED by owner integration-terms acceptance.**
Five of six increment tasks are complete. Do not mark deployment, hosted protection or real
cloud updates verified. The existing Vercel URL still serves the protected static snapshot.

The Vercel CLI returned `integration_terms_acceptance_required` and `userActionRequired: true`.
The owner was given the actual verification URL. No resource was created, legal terms accepted,
paid upgrade performed or temporary unclaimed database substituted. Intended transport is the
Upstash free plan with `autoUpgrade=false`, `prodPack=false`, `eviction=false`, preview only.
No browser storage token. No SDK or new runtime library remains after transport selection.

## Code-review evidence

| Requirement | Evidence | Result |
| --- | --- | --- |
| Observe rather than execute | Python opens SQLite mode=ro; no model/trading imports or calls; worker lock only indicates observed process | PASS |
| No invented completed performance | Checkpoint checksum/sequence verified in one transaction; incomplete runs expose status only | PASS |
| Preserve experiment integrity | Reference data SHA/settings checked against baseline; 15 memory + 15 context + 5 opportunity artifacts rehashed without mismatch | PASS |
| Freshness means source time | Browser age uses source timestamp, rejects future/regressing timestamps; endpoint never stamps now | PASS |
| Report updates only on change | Fingerprint cache includes completed evidence/references; restart restores normalized source-key SHA and original report metadata | PASS |
| Source failure recovery | Corrupt SQLite/ZIP/malformed archive, disappearing source and prior missing journals retain verified report and explicit warning | PASS |
| Upload failure recovery | Python retries one-shot transport at 60/120/240/300 seconds; confirmed revision changes only on successful acknowledgment | PASS |
| Single supported publisher | Parent advisory flock; duplicate observer rejected; SIGTERM unwinds child and releases lock; marker presence does not prevent restart | PASS |
| Atomic cloud result | MSET report + metadata; unchanged heartbeat uses SET; API verifies requested revision against actual report hash | PASS locally with injected storage |
| Reader privilege/privacy | Fixed two keys, GET-only route, server read-only token required, bounded/sanitized errors, no arbitrary upstream or local path | PASS code/local tests |
| Browser recovery/security | Timeout/retry, pause hidden tabs, same-origin polling, script-free sandboxed report, restrictive CSP, no-store/noindex | PASS locally |
| Scope/cost | Six planned tasks; no extra model calls, new experiment, account upgrade, live orders or main promotion | PASS |

Review findings were fixed without weakening checks:

1. Initial fresh reviewer: one HIGH (watch exits permanently after transient upload), two
   MEDIUM (bad ZIP escapes; O_EXCL marker survives signals). Replaced Node's continuous loop
   with parent-locked Python retry orchestration, caught ZIP errors, added subprocess/lock tests.
2. Fresh fix reviewer: three MEDIUM (malformed archive structure, enumeration/fingerprint race,
   lost report metadata across restart). Added explicit source-error handling and bounded private
   persisted inventory/config/report verification. Regression cases added.
3. Next fresh reviewer: one MEDIUM (unchanged healthy restart regenerates report timestamp).
   Reproduced the failed assertion before repair; persisted a normalized source fingerprint.
   Final fresh reviewer found no remaining findings in that bounded fix and reran the restart test.

No unresolved HIGH/CRITICAL or reported MEDIUM remains in this scoped review. The three-cycle
fix limit was respected. Input-failure tests use temporary fixtures only, not real study artifacts.
Local generated-state corruption/config mismatch fails explicitly rather than trusting changed
HTML. Only one configured source/output publishes to a private store; separate output directories
are not coordinated by the same lock.

## Full QA evidence

| # | Check | Result | Actual evidence |
| --- | --- | --- | --- |
| 1 | Plan | WARN | Five of six tasks complete; hosted task explicitly pending |
| 2 | Landmines | PASS | `.Codex/landmines.md` absent; actual `.claude/landmines.md` read, no active entries |
| 3 | Lint | PASS | `.venv/bin/ruff check .`: `All checks passed!` |
| 4 | Types | PASS | `.venv/bin/mypy .`: `Success: no issues found in 68 source files` |
| 5 | Full Python suite | PASS | `.venv/bin/pytest -x --timeout=30`: `247 passed, 17 xfailed in 30.31s` |
| 5b | JS transport/protocol | PASS | `npm test --prefix web/cockpit`: 6 passed, 0 failed/skipped |
| 6 | DB security advisor | SKIP | No relational migration/Supabase; private Redis adapter directly reviewed; cloud provisioning pending |
| 7 | DB performance advisor | SKIP | No relational query plan; bounded/fixed-key transport, no per-journal external queries |
| 8 | Tenant isolation | SKIP | Single-owner protected project, no multi-tenant service or `.from()` queries |
| 9 | Scope | PASS | Six planned tasks; observer/web/tests/docs only |
| 10 | Browser/local integration | PASS | 1440×1050 desktop, 820×1180 tablet, 390×844 phone; no overflow/page errors |
| 10b | Result refresh | PASS | Test-only response interception changes report; selected account-value chart and open evidence survive |
| 10c | Stale/offline/recovery | PASS | Advancing browser clock 181s shows stale; rolling it back 60s gives a clock warning without page errors; offline retains charts; recovery reconnects |
| 10d | Actual saved evidence | PASS | 38 records observed idle/no source errors; second real one-shot observer retains revision and report timestamp |
| 10e | Signal/restart | PASS | Subprocess regression refuses second writer, SIGTERM stops first, restart succeeds without deleting lock |
| 10f | Hosted integration | BLOCKED | Free-store legal acceptance not yet supplied; no live deployment or cloud heartbeat proof |

The 17 expected failures are unchanged sensory stubs, not newly waived tests. No new skip/xfail
or threshold change. New code uses 13 Python live-feed cases plus six JS cases. Regression
failures were observed before the relevant recovery fixes. Existing studies are unchanged;
mock transport and browser-intercepted labels are testing fixtures, not trading evidence.

Chrome DevTools MCP was unavailable; the skill's permitted Playwright fallback verified the
local app. Real browser measurements: document/viewport widths 1440/1440, 820/820 and 390/390;
iframe heights 1473, 1695 and 2380 respectively, no resize loop. Keyboard chart arrows and
Refresh activation passed. A browser clock-injection check exposed an uncaught periodic freshness
exception; the status renderer now displays an explicit clock-verification warning and retains
charts. Final test uses the browser clock consistently, covers rollback and recovery, and records
zero page errors. No future-timestamp validation was relaxed. Phone screenshot inspected:
source/result timestamp, idle status, degraded February result and all38 saved records visible.
Artifacts: `/private/tmp/neural-live-browser.json`,
`/private/tmp/neural-live-desktop.png`, `/private/tmp/neural-live-tablet.png`,
`/private/tmp/neural-live-mobile.png`. These are local artifacts, not cloud acceptance evidence.

## Operating limits

The read-only source and loopback test server are Mac terminal processes, not installed login
services. Sleeping/closing the Mac stops source freshness. No 24/7 worker or agent start/pause
control is claimed. Free Redis quota and existing Vercel usage allowances must be checked at
provisioning; no blanket free-account invoice promise. The old unresolved USD .003 AI reservation
remains untouched. No request retry, new paid experiment, strategy promotion or demonstrated
learning/trading edge is implied by a connected dashboard.

See [hosting and activation runbook](../guides/COCKPIT_HOSTING.md#live-updates-local-implementation-online-connection-pending).
