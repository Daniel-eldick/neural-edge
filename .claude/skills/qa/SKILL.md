---
name: qa
description: Pre-merge quality gate — automated checks + manual verification via Chrome DevTools MCP. Use after implementation, before /commit.
allowed-tools: Read, Bash, Glob, Grep, mcp__database__get_advisors, mcp__database__execute_sql, mcp__chrome-devtools__take_snapshot, mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__click, mcp__chrome-devtools__fill
---

# QA Skill

Pre-merge quality gate: automated checks + manual verification. One question: **"Is this ready to merge?"**

## When to Use

- `/qa`, "is this ready?", "ready to merge", "pre-merge check"
- After implementation is complete, before `/commit`
- After `/code-review` passes

## When NOT to Use

- Implementation isn't done yet (finish first)
- Code hasn't been reviewed (use `/code-review` first)
- Running tests only (use `/test`)
- Plan review (use `/sign-off`)

---

## QA Tiers

Scale checks to risk, matching the plan tier:

| Tier      | Checks Run                          | When                                   |
| --------- | ----------------------------------- | -------------------------------------- |
| **Light** | Checks 1, 3, 4, 5, 9                | Docs, skills, config, CSS-only changes |
| **Full**  | All 10 checks + manual verification | Code changes, DB, auth, offline        |

Infer tier from the planning doc's tier or the type of changes. Default to **Full** if unsure.

---

## Workflow

### Step 1: Identify What Was Built

Find the active planning doc. Get branch and changed files:

```bash
git branch --show-current
git diff develop --name-only
```

### Step 2: Automated Checks

Run checks in order. Mark each PASS, FAIL, WARN, or SKIP.

**Check 1 — Planning doc completeness**: All task checkboxes `[x]`?

**Check 2 — Landmine re-scan** (Full only): Read `.claude/landmines.md`. Check each relevant pattern against the ACTUAL diff.

**Top 3 patterns to check first** (highest recurrence in QA):

| Pattern                    | Trigger (in diff)                  | Quick check                                                        |
| -------------------------- | ---------------------------------- | ------------------------------------------------------------------ |
| **#6 Tenant isolation**    | `.from(` queries, new hooks        | `tenant_id` filter + React Query key includes it?              |
| **#11 Admin colors**       | `src/components/admin/**`          | All tokens use <!-- FILL: your design token convention -->?    |
| **#2 local database undefined** | `src/lib/offline/**`, local DB writes | No field set to `undefined`? Using `'pending'`/`null` explicitly?  |

If the diff touches these areas, verify the specific prevention check from `landmines.md`. Then scan remaining patterns.

**Check 3 — Lint**: `npm run lint` → zero warnings.

**Check 4 — Type-check**: `npm run type-check` → zero errors.

**Check 5 — Unit tests**: `npm run test:run` → no NEW failures beyond 11 pre-existing (rpc-performance 6, useTestAuth 2, OrdersList 3).

**Check 6 — Security advisor** (Full only, if `database/migrations/` in diff): `mcp__database__get_advisors({ type: "security" })`. No new warnings.

**Check 7 — Performance advisor** (Full only, if `database/migrations/` in diff): `mcp__database__get_advisors({ type: "performance" })`. No new warnings.

**Check 8 — Tenant isolation** (Full only, if `.from(` queries changed): Verify `tenant_id` filter + React Query key.

**Check 9 — Scope guard**: Compare original vs current task count. WARN if > 1.5x.

**Check 10 — Manual verification** (Full only): Walk through manual verification steps from planning doc using Chrome DevTools MCP.

**Check 10b — UX verification** (Full only, if UI changes in diff):

- [ ] Works on tablet viewport (820×1180)? Navigate via Chrome DevTools MCP with emulation
- [ ] Primary action obvious without instructions? (Learnability: <5 min to productive)
- [ ] Error states show WHAT went wrong + WHAT to do? (not just a red toast)

**Check 11 — Verification language gate** (Light + Full):

```
┌─────────────────────────────────────────────────────────┐
│  HARD-GATE: Evidence Before Claims                      │
│                                                         │
│  Scan YOUR OWN output in this session. If you used      │
│  any of these phrases about the work being reviewed,    │
│  replace them with evidence:                            │
│                                                         │
│  FORBIDDEN: "should work", "probably passes",           │
│  "looks correct", "seems fine", "I believe this works", │
│  "this should be good"                                  │
│                                                         │
│  REQUIRED: "I ran [command] and the output was [X]",    │
│  "Test [name] passes with assertion [Y]",               │
│  "MCP query returned [Z]"                               │
│                                                         │
│  Claiming work is complete without verification is      │
│  dishonesty, not efficiency.                            │
└─────────────────────────────────────────────────────────┘
```

For **Full tier only** — evidence table required:

| Claim                    | Evidence Command           | Actual Output                                  |
| ------------------------ | -------------------------- | ---------------------------------------------- |
| [e.g., "Tests pass"]     | [e.g., `npm run test:run`] | [e.g., "42 passed, 11 skipped (pre-existing)"] |
| [e.g., "No lint errors"] | [e.g., `npm run lint`]     | [e.g., "0 errors, 0 warnings"]                 |

**Verification Rationalization Table** — If you catch yourself thinking any of these, stop:

| Excuse                                     | Rebuttal                                                                            |
| ------------------------------------------ | ----------------------------------------------------------------------------------- |
| "It should work based on the code I wrote" | Reading code is not running code. Run it. Report what happened.                     |
| "Linter/type-checker passed, so it works"  | Type safety proves types match, not that behavior is correct. Run the actual tests. |
| "I tested a similar change before"         | Similar != identical. Context changes. Test THIS change.                            |
| "Manual testing would take too long"       | Shipping a bug takes longer. Automate or test manually — "skip" is not an option.   |
| "The test suite covers this"               | Which test? Name it. If you can't name it, the suite doesn't cover it.              |

### Step 2.5: Fix-and-Recheck Loop

After running automated checks, if any check is **FAIL** and the failure is fixable (not environment or flaky test), self-correct before presenting to the CEO.

#### Convergence Target

All checks PASS (or SKIP where appropriate).

**Max iterations**: 3 fix-recheck cycles.

#### Loop Flow

```
Run checks → Any FAIL?
    ├── No → Present result (Step 3)
    └── Yes → Failure fixable?
                 ├── Yes → Fix the failure cause
                 │           → Re-run that specific check (G3, G6)
                 │           → All pass OR budget OR stuck?
                 │                ├── All pass → Present clean result
                 │                ├── Budget → Present best + remaining FAILs
                 │                └── Stuck → Escalate with context
                 └── No (flaky test, environment issue, manual-only)
                      → Escalate to CEO immediately
```

#### What QA Can Fix (Editing Boundary)

| CAN fix (deterministic)            | MUST escalate (non-deterministic)    |
| ---------------------------------- | ------------------------------------ |
| Lint warnings → fix code           | Flaky test not caused by this change |
| Type errors → fix types            | Environment/infrastructure issue     |
| Failing unit test → fix the bug    | Manual-only verification needed      |
| Missing test coverage → write test | Business logic ambiguity             |

#### No Fresh-Eyes Agent Needed

QA checks are predominantly deterministic (lint, types, tests). The tools ARE the judge — objective command output, not subjective scoring. No self-bias risk.

#### Circuit Breaker (G8)

For Check 10 (manual verification via Chrome DevTools MCP):

1. Chrome DevTools MCP fails → try Playwright CLI fallback
2. Playwright CLI also fails → **STOP** and notify CEO
3. Never skip manual verification silently

#### Diff Transparency (G5)

Each iteration logs:

- Which check failed
- What was fixed (1-line summary)
- Re-run result

#### Iteration Output

Show in final output: `"Self-corrected: lint (1 warning fixed), type-check (1 error fixed)"`

If budget exhausted: `"Fixed X/Y failures in 3 rounds. Remaining: [list]"`

### Step 3: Verdict

| Condition               | Verdict                |
| ----------------------- | ---------------------- |
| All checks PASS or SKIP | **PASS**               |
| Any WARN but no FAIL    | **PASS WITH WARNINGS** |
| Any FAIL                | **FAIL**               |

### Step 4: Report

```markdown
## QA Report — [Feature Name]

**Date**: [timestamp]
**Branch**: [branch name]
**Tier**: Light / Full
**Verdict**: PASS / FAIL / PASS WITH WARNINGS

### Results

| #   | Check                 | Result         | Notes                             |
| --- | --------------------- | -------------- | --------------------------------- |
| 1   | Planning doc          | PASS/FAIL      | [details]                         |
| 2   | Landmine scan         | PASS/WARN/SKIP | [details]                         |
| 3   | Lint                  | PASS/FAIL      | [details]                         |
| 4   | Type-check            | PASS/FAIL      | [details]                         |
| 5   | Unit tests            | PASS/FAIL      | [X pass, Y new]                   |
| 6   | Security advisor      | PASS/FAIL/SKIP | [details]                         |
| 7   | Performance advisor   | PASS/FAIL/SKIP | [details]                         |
| 8   | Tenant isolation      | PASS/FAIL/SKIP | [details]                         |
| 9   | Scope guard           | PASS/WARN      | [X/Y tasks]                       |
| 10  | Manual verification   | PASS/FAIL/SKIP | [details]                         |
| 11  | Verification language | PASS/FAIL      | [forbidden phrases found / clean] |

### Blockers (if FAIL)

- [Must fix before merge]

### Warnings (if any)

- [Non-blocking, documented]

### Next Steps

- [ ] Fix blockers (if any)
- [ ] `/commit`
```

---

## Principles

1. **Risk-proportionate** — Light QA for docs changes. Full QA for production code.
2. **Pre-existing failures don't count** — 11 known failures are NOT new regressions.
3. **Landmine scan is critical** — Many bugs recur because we didn't check the patterns.
4. **Manual verification uses Chrome DevTools MCP** — Navigate, snapshot, click, verify.
5. **FAIL means stop** — Don't commit with FAIL. Fix first.
6. **Scope guard catches creep** — If tasks grew > 1.5x, something drifted.

---

## Anti-Patterns

- Skipping QA because "it's just a small change"
- Running QA before implementation is done
- Ignoring WARN results without documenting why
- Running Full QA for docs-only changes (use Light)
- Committing with FAIL verdict
- Not checking the 11 pre-existing failures before reporting "new" failures

---

## Skill Pipeline

```
/plan → /sign-off → implement → /code-review → /qa → commit → push → PR → /review-pr (in develop)
                                                  ↑
                                             you are here
```
