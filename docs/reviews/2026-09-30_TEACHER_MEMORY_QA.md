# Teacher/memory review and QA evidence

Date: 2026-09-30. Branch: `codex/apprentice-cockpit`. Reviewed implementation: `3ad54f8`.
Plan: [causal teacher/memory increment](../active/APPRENTICE_TRADER_PLAN.md).
Scope: the 17-file increment from `40e5970` to `3ad54f8`; the larger diff against develop
contains earlier unmerged foundations and is not newly approved wholesale by this report.

## Code review — Standard tier

**Verdict: APPROVED for the bounded offline increment.** The code-review skill was applied
before commit, including an independent fresh-context review. This report records that work;
it does not claim a second independent review occurred today. No unresolved blocking finding.

Spec compliance: all six increment tasks have implementation/evidence; package metadata is
within the recorded blast radius. Test awareness: failing tests were exercised before code,
but source and tests were committed together (test-with in the skill's Git classification).
The current 0.5%/2.5% risk mandate and root guidance supersede the skill's stale 1% examples.

| Business rule | Implementation / verification | Result |
| --- | --- | --- |
| Closed outcomes only; delayed availability | `src/memory/teacher.py` consume/review/context; delayed, future-event and future-suffix tests | Verified |
| Losses retained; bounded retrieval | 64 retained cases, latest six same-symbol cases; mixed win/loss bound test | Verified |
| No curriculum backdating/answer keys | Separate JSON pack available 2026-09-30; runtime never loads exercise document | Verified |
| Same-run recovery isolation | `LearningPolicy.restore_state`; cursor, clock, journal reconstruction, fingerprint and response identity checks | Verified |
| No duplicate paid request after crash | ResponseStore reused; saved second response survives rollback test | Verified |
| Integrity failure cannot persist partial memory | Failed advancement poisons save_state; candle transaction rollback regression | Verified |
| Provider errors preserve protection | Both frozen and memory policy tests retain deterministic exits | Verified |
| No fabricated improvement | Existing pilot remains memory-free; cockpit labels memory status and unproven improvement | Verified |

Self-corrected two implementation findings in one review-preparation round: reject partial
memory checkpoints after teacher failure; include curriculum JSON in installed package data.
Fresh-eyes review checked both fixes. An isolated wheel build confirmed the JSON is included.
No dependency, network fanout, evaluator or live-trading path was added. Memory/state remain
bounded; recovery scans one committed journal prefix. Local policy code remains trusted,
not a security sandbox. The missing `.Codex/landmines.md` was disclosed during review.

## QA — Full tier

**Verdict: PASS WITH WARNINGS for the bounded offline increment.** Formal QA was completed
on request after the implementation commit; prior automated/browser verification was performed,
but there was no separately recorded full QA verdict before that commit. This process gap is
acknowledged rather than retroactively calling the prior work a formal QA pass.

The inherited skill's npm commands, Supabase checks and eleven JavaScript failures are not
applicable to this Python repository. Root AGENTS.md provides the actual commands below.

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Plan completeness | PASS | Six tasks 0–5 complete for this increment; full product milestones explicitly remain unfinished |
| 2 | Landmine scan | WARN | `.Codex/landmines.md` absent; named React/tenant/offline-JS patterns do not occur in the increment |
| 3 | Lint | PASS | `.venv/bin/ruff check .` → `All checks passed!` |
| 4 | Types | PASS | `.venv/bin/mypy .` → `Success: no issues found in 57 source files` |
| 5 | Tests | PASS | `.venv/bin/pytest -x --timeout=30` → `177 passed, 17 xfailed in 4.27s`; no new failures |
| 6 | Database security advisor | SKIP | No hosted database/migration; local SQLite only |
| 7 | Database performance advisor | SKIP | No hosted database/migration |
| 8 | Tenant isolation | SKIP | No multitenant service or tenant query changes; same-run memory isolation tested separately |
| 9 | Scope guard | PASS | Six planned tasks completed; no >1.5x expansion; 17 implementation/document/test files |
| 10 | Browser and integration | PASS | Authenticated preview HTTP 200; desktop 1440×1050, tablet 820×1180, phone 390×844; no page/console errors or horizontal overflow; chart radio click/keyboard and expanded evidence work |
| 10b | UX | WARN | Performance and evidence controls visible; incomplete-coverage warning names 11 missing evaluations. Recovery/refresh guidance is in documentation, not a cockpit action; no real-user learnability study claimed |
| 11 | Evidence language | PASS | Outcomes tied to commands/tests; no profitability, unattended-operation or full-product readiness claim |

Chrome DevTools MCP is unavailable in the enabled tools. The permitted Playwright fallback
ran with bundled Chromium through the local Node CLI. Authentication used the existing
project credential in memory and restricted its header to the deployment origin; no credential
was printed or stored in this report. Private preview:
[neural-edge-cockpit](https://neural-edge-cockpit-16pe3ge3m-daniel-eldicks-projects.vercel.app).
The exact 820×1180 tablet viewport was exercised on this QA run. Local raw result:
`/private/tmp/neural-edge-browser-check.json` (temporary, not a durable repository artifact).

Manual integration evidence also includes the actual Replay/Journal/ResponseStore tests in
`tests/test_learning_memory.py` and the mocked-network CLI pause/resume tests in
`tests/test_jev_policy.py`. These are synthetic correctness checks, not market performance.
`config.json` remains `dry_run: true`; both original pilot database hashes match the frozen
research record. No paid inference or runtime code change was made by this QA pass.

Warnings: 17 pre-existing sensory expected failures remain; absent risk-pattern registry;
UI recovery actions and live controls remain unfinished. These are disclosed limitations.
No deterministic failure required correction during this QA run (zero fix rounds).

This does not authorize merging the cumulative draft PR: its unmerged predecessor branches
still need reconciliation and review. No merge, main promotion or real trading occurred.
Next: retain this evidence, run the predeclared comparisons, and develop the separately
recorded regime/pattern requirement through design and validation.
