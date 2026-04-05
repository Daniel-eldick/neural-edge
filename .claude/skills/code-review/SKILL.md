---
name: code-review
description: Strict pre-commit quality gate — analyzes code, runs checks, produces evidence-based findings with verdict. Hard to pass by design.
allowed-tools: Read, Grep, Glob, Bash, Task, mcp__database__get_advisors, mcp__database__execute_sql, mcp__chrome-devtools__take_snapshot
---

# Code Review Skill

Strict pre-commit quality gate. Analyzes changes, runs automated checks, traces business rules, and produces evidence-based findings with verdict. Review depth scales with change risk. **Hard to pass by design** — this is the tough analytical gate. `/qa` is the integration confirmation gate. Both are serious.

## When to Use

- `/code-review`, "review this code", "check my changes"
- After implementation, before `/qa`
- After making significant changes to production code

## When NOT to Use

- Reviewing external library code (not your changes)
- Minor typo fixes in documentation (just commit)
- Plan hasn't been implemented yet (use `/sign-off` for plans)

---

## Step 1: Identify Changes and Classify Risk

```bash
git status --short
git diff --name-only
git diff --cached --name-only
```

Classify into a review tier:

| Tier         | Criteria                                               | Review Depth                  |
| ------------ | ------------------------------------------------------ | ----------------------------- |
| **Light**    | Docs, skills, config, CSS-only, copy changes           | Single-pass checklist         |
| **Standard** | UI components, hooks, refactors, API integration       | Full analysis + auto checks   |
| **Deep**     | DB migrations, RLS, auth, offline sync, service worker | Full + MCP + Devil's Advocate |

### Light Tier — Single-Pass Checklist

For Light tier, skip all subsequent steps. Run this checklist and produce verdict:

- [ ] Changes match intent (no accidental modifications in the diff)
- [ ] Formatting correct (markdown, YAML, JSON, etc.)
- [ ] No secrets or sensitive data (API keys, tokens, passwords)
- [ ] No unrelated code changes hiding in the diff

**Verdict**: APPROVED (unless secrets found → BLOCKED). Done — skip to Step 7 (Produce Findings).

---

## Step 2: Context Gathering (Standard + Deep)

### Landmine Scan (Standard + Deep)

Read `.claude/landmines.md`. Check each pattern against the diff:

- Any landmine match → **auto-flag as HIGH** in findings with the specific pattern ID
- Document which patterns were checked and which matched

### MCP Verification (Deep tier)

**IF database changes detected** (migrations, RPC, RLS):

```
mcp__database__get_advisors({ type: "security" })
mcp__database__get_advisors({ type: "performance" })
mcp__database__execute_sql("EXPLAIN ANALYZE ...")  // for new/modified queries
```

**IF frontend changes detected** (Standard + Deep):

```
mcp__chrome-devtools__take_snapshot()  // inspect current UI state
Read component files — check patterns, types, hooks usage
```

**IF offline changes detected** (Deep):

```
<!-- FILL: Add grep checks for your offline system's critical constants:
- Batch size configuration — verify expected value
- Data retention policy — verify cleanup intact
- Sync status field — verify proper state checks
- Reconnection delay — verify anti-stampede delay present
-->
```

---

## Step 3: Spec Compliance + Scope Guard (Standard + Deep)

### Spec Compliance

**Before reviewing code quality, verify the implementation matches the plan.**

For **Standard** tier — check as a dimension:

- [ ] Compare `git diff` against the planning doc's task list
- [ ] Every completed task in the plan has corresponding code changes
- [ ] No unplanned changes snuck in (scope creep)
- [ ] Test approach from the plan was followed (if specified)

For **Deep** tier — this is a **separate phase** that must pass before Step 4:

> **Phase 1: Spec Compliance** — "Did you build what was asked? Nothing more, nothing less?"
>
> Read the planning doc. Read the diff. Answer these questions:
>
> - [ ] Every task in the plan has corresponding implementation
> - [ ] No tasks were skipped without documented reason
> - [ ] No unplanned features or refactors were added
> - [ ] Test approach from the plan was followed
> - [ ] If spec compliance fails → STOP. Fix before proceeding to Phase 2 (quality review).

### Scope Guard (Standard + Deep)

- Compare planning doc's original task count vs changes in the diff
- **WARN** if changes touch > 1.5x the planned scope
- Flag unplanned files that weren't in the plan's "Files & Blast Radius" table
- If no planning doc exists → skip (but note the gap in findings)

### Test Awareness (Standard + Deep)

Check git log to determine test coverage approach:

| Level          | Description                          | Action                                                   |
| -------------- | ------------------------------------ | -------------------------------------------------------- |
| **Test-first** | Tests committed before code          | Note as strength                                         |
| **Test-with**  | Tests in same commit as code         | Acceptable (Standard), note for Deep                     |
| **Test-after** | Tests exist but committed after code | Flag MEDIUM — verify tests aren't implementation-mirrors |
| **No tests**   | No test coverage for new behavior    | Flag HIGH (Standard) / CRITICAL (Deep)                   |

---

## Step 3.5: Behavior Verification (Standard + Deep)

**"Did you build it RIGHT?"** — traces business rules from the plan through the code.

This is different from spec compliance (Step 3), which checks "did you build the RIGHT thing?"

1. Read the planning doc's test plan and business rules
2. For each business rule in the plan, trace through the code to verify the rule is implemented correctly
3. Flag any rule that is:
   - **Missing**: No code implements this rule → CRITICAL
   - **Partially implemented**: Code exists but doesn't cover all cases → HIGH
   - **Implemented differently than specified**: Logic diverges from plan → HIGH
   - **Correctly implemented**: Mark as verified

If no planning doc exists → check the PR description or commit messages for business intent. If neither exists, note the gap but still review the code's logic for correctness.

---

## Step 4: Engineering Philosophy + Security + UX (Standard + Deep)

For **Standard and Deep** tiers (Deep: this is **Phase 2 — Quality Review**):

### Scale Analysis (10x Load)

- [ ] What happens at 10x current load?
- [ ] Any N+1 queries?
- [ ] Memory leak potential over weeks?
- [ ] Worst-case performance?

### Failure Analysis

- [ ] What happens when this fails?
- [ ] Error handling adequate?
- [ ] Retry logic appropriate?

### Security Check (Deep tier)

- [ ] RLS policies adequate?
- [ ] Input validation present?
- [ ] No sensitive data exposure?
- [ ] Auth checks in place?

### Tenant Isolation Check (Standard + Deep)

Whenever `.from(` query patterns appear in the diff:

- [ ] `tenant_id` filter present on every query?
- [ ] React Query key includes `tenant_id`?
- Any missing filter → **auto-flag as CRITICAL** (multi-tenant data leak risk)

### Code Quality (Standard + Deep)

- [ ] Follows existing codebase patterns?
- [ ] Tests cover new functionality?
- [ ] Admin components use <!-- FILL: your design token convention --> (not hardcoded colors)?

### UX Verification (Standard + Deep, if UI changes detected)

- [ ] Touch targets >= 44px (Apple HIG / WCAG 2.1 AAA)
- [ ] Loading/skeleton states present (user knows what's happening)
- [ ] Error messages include recovery action (not just "Something went wrong")
- [ ] Destructive actions have confirmation dialog
- [ ] Primary action visible without scrolling
- [ ] Consistent interaction patterns with existing app flows

---

## Step 5: Automated Verification (Standard + Deep)

**A strict gate produces evidence, not opinions.** Actually run:

```bash
npm run lint          # Zero warnings
npm run type-check    # Zero errors
npm run test:run      # No NEW failures beyond known pre-existing (11)
```

| Check      | Pass Criteria                          | On Failure    |
| ---------- | -------------------------------------- | ------------- |
| Lint       | Zero warnings                          | Flag HIGH     |
| Type-check | Zero errors                            | Flag CRITICAL |
| Unit tests | No NEW failures beyond 11 pre-existing | Flag CRITICAL |

Record exact output for each command — these feed into the Evidence Gate (Step 7).

---

## Step 5.5: Devil's Advocate (Deep tier only)

**Self-review is biased.** Spawn a fresh-context agent to break the echo chamber.

Spawn a `general-purpose` Task agent with:

- **No prior conversation context** — the agent reads the diff cold
- The `git diff` output (pipe to a temp file or pass inline)
- The planning doc path

**Agent prompt**:

```
You are a senior engineer reviewing code you did NOT write. You have no context about why decisions were made — you're reading this diff for the first time.

## Your Job

Find assumptions, edge cases, and failure modes the author likely missed. Be constructively ruthless.

## Process

1. Read the planning doc: [PLAN_PATH]
2. Read the diff: [DIFF or git diff develop]
3. Read CLAUDE.md for project conventions
4. For each changed file, ask:
   - What happens if this input is null/undefined/empty?
   - What happens at 10x concurrent usage?
   - Is there a race condition between this and other operations?
   - Could this silently corrupt data?
   - Is tenant isolation maintained (tenant_id on every query)?

## Output Format

Return findings as a severity-tagged table:

| Severity | File:Line | Description | Why Author Likely Missed It |
|----------|-----------|-------------|----------------------------|
| CRITICAL | ... | ... | ... |
| HIGH | ... | ... | ... |
| MEDIUM | ... | ... | ... |

If you find nothing concerning, say so — don't manufacture issues.
```

Merge agent findings into the main findings table in Step 8. Tag each with `[DA]` prefix so the origin is clear.

---

## Step 6: Evidence Gate (Standard + Deep)

**The review's own output must be evidence-based.** No hand-waving past this point.

### Forbidden Phrases

Scan the review narrative for these phrases. If found, replace with evidence:

| Forbidden              | Replace With                                                  |
| ---------------------- | ------------------------------------------------------------- |
| "should work"          | "I ran [command] and the output was [X]"                      |
| "probably passes"      | "Test [name] passes with assertion [Y]"                       |
| "looks correct"        | "I traced [rule] through [file:line] and verified [behavior]" |
| "seems fine"           | "MCP query returned [Z]"                                      |
| "I believe this works" | "[specific evidence]"                                         |

### Evidence Table (Deep tier — required)

| Claim            | Evidence Command                     | Actual Output    |
| ---------------- | ------------------------------------ | ---------------- |
| "Tests pass"     | `npm run test:run`                   | "[exact output]" |
| "No lint errors" | `npm run lint`                       | "[exact output]" |
| "No type errors" | `npm run type-check`                 | "[exact output]" |
| "RLS is secure"  | `get_advisors({ type: "security" })` | "[exact output]" |

For Standard tier, the evidence table is recommended but not required — the automated check results from Step 5 serve as baseline evidence.

---

## Step 6.5: Fix-and-Re-Review Loop (Standard + Deep)

After producing findings internally, if the verdict would be **NEEDS CHANGES** and the findings are code-fixable (not design decisions), self-correct before presenting to the CEO.

### Convergence Target

| Condition                             | Target   |
| ------------------------------------- | -------- |
| CRITICAL findings                     | 0        |
| HIGH findings                         | 0        |
| Automated checks (lint, types, tests) | All pass |

**Max iterations**: 3 fix-review cycles.

### Loop Flow

```
Produce findings → NEEDS CHANGES?
    ├── No (APPROVED) → Present result (Step 7)
    └── Yes → All findings code-fixable?
                 ├── Yes → Fix CRITICAL/HIGH findings
                 │           → Re-run affected automated checks (G3, G6)
                 │           → Re-review changed code with fresh agent (G2)
                 │           → Converged OR budget OR stuck?
                 │                ├── Converged → Present clean result
                 │                ├── Budget → Present best + remaining issues
                 │                └── Stuck → Escalate with context
                 └── No (design flaw, unclear spec, new dependency)
                      → Escalate to CEO immediately
```

### Before Looping (Anti-Scope-Reduction — G4)

Snapshot before first iteration:

- Finding counts by severity (CRITICAL, HIGH, MEDIUM, LOW)

After each iteration, findings can decrease (with evidence of fix) but cannot disappear without a corresponding code diff.

### Re-Review Rules

| Tier     | Re-Review Method                      | Guardrail    |
| -------- | ------------------------------------- | ------------ |
| Standard | Fresh-eyes agent reviews the fix diff | G2 + G5 + G6 |
| Deep     | Fresh-eyes agent reviews the fix diff | G2 + G5 + G6 |

### What Code-Review Can Fix (Editing Boundary)

| CAN fix (code-level)             | MUST escalate (decision-level)                |
| -------------------------------- | --------------------------------------------- |
| Lint warnings → fix code         | Design flaws requiring architectural change   |
| Type errors → fix types          | Unclear spec (multiple valid interpretations) |
| Missing error handling → add it  | New dependency decisions                      |
| Missing null checks → add guards | Business logic ambiguity                      |
| Test coverage gaps → write tests | Trade-offs requiring CEO judgment             |

### Diff Transparency (G5)

Each iteration logs:

- Which findings were addressed
- What code changes were made (file:line summary)
- Which automated checks were re-run and their results

### Iteration Output

Show in final output: `"Self-corrected N findings in M rounds"`

If budget exhausted: `"Fixed X/Y findings in 3 rounds. Remaining: [list]"`

---

## Step 7: Produce Findings

```markdown
## Code Review: [Component/Feature Name]

**Tier**: Light / Standard / Deep
**Files reviewed**: [count]
**Date**: [timestamp]

### Spec Compliance (Standard + Deep)

- Plan followed: [Yes / Partial / No — details]
- Scope: [Clean / Scope creep detected — X planned vs Y actual]
- Test awareness: [Test-first / Test-with / Test-after / No tests]

### Behavior Verification (Standard + Deep)

| Business Rule    | Code Location | Status                                   |
| ---------------- | ------------- | ---------------------------------------- |
| [rule from plan] | [file:line]   | Verified / Missing / Partial / Divergent |

### Summary

[1-2 sentence overview of changes]

### Findings

| Severity | Source   | File:Line | Description          | Recommended Fix |
| -------- | -------- | --------- | -------------------- | --------------- |
| CRITICAL | Review   | path:42   | [issue]              | [fix]           |
| HIGH     | [DA]     | path:78   | [issue]              | [fix]           |
| MEDIUM   | Landmine | path:123  | [pattern ID + issue] | [fix]           |
| LOW      | Review   | path:200  | [issue]              | [fix]           |

Source legend: Review = main review, [DA] = Devil's Advocate agent, Landmine = landmine scan match

### Automated Check Results

| Check      | Result    | Output                          |
| ---------- | --------- | ------------------------------- |
| Lint       | PASS/FAIL | [summary]                       |
| Type-check | PASS/FAIL | [summary]                       |
| Unit tests | PASS/FAIL | [X passed, Y failed, Z skipped] |

### MCP Verification Results (Deep tier only)

- Security advisors: [X warnings found / Clean]
- Performance advisors: [X warnings found / Clean]
- Query performance: [EXPLAIN ANALYZE results if applicable]

### Strengths

- [What's done well — good work deserves recognition]

### Verdict

**[APPROVED / APPROVED WITH NOTES / NEEDS CHANGES / BLOCKED]**

| Verdict             | Criteria                                                                  |
| ------------------- | ------------------------------------------------------------------------- |
| APPROVED            | Zero CRITICAL/HIGH findings. Automated checks pass.                       |
| APPROVED WITH NOTES | Zero CRITICAL. ≤2 HIGH (documented, non-blocking). Automated checks pass. |
| NEEDS CHANGES       | Any CRITICAL finding, OR >2 HIGH findings, OR automated checks fail.      |
| BLOCKED             | Tenant isolation breach, security vulnerability, or data corruption risk. |

Rationale: [Specific reason based on findings severity]

**Next step**: [If APPROVED → "/qa" | If NEEDS CHANGES → "Fix CRITICAL/HIGH issues, then re-run /code-review"]
```

---

## Anti-Patterns to Flag

**Database**:

- Missing RLS policies on new tables
- N+1 queries in RPC functions
- Adding LIMIT to RPC functions (breaks tenant isolation)
- SECURITY DEFINER without `SET search_path TO ''` or auth checks

**Offline System**:

- Removing 30-day local database cleanup (storage bloat)
- Removing stagger delay from handleOnline (sync stampede)
- Missing sync_status checks before deletion
- Disabling slow-retry phase (breaks self-healing)
- Bypassing sync queue semaphore (connection pool exhaustion)

**Security**:

- Storing PII in local database without encryption
- Missing input validation on user-provided data
- Skipping auth checks in API calls
- Exposing sensitive data in client-side logs

**Testing**:

- Vague test assertions ("order syncs" → "sync_status changes to 'synced' within 5s")
- Missing test coverage for new features
- Console.log in production code (except allowed: debug-offline.ts, debug.ts, authSecurity.ts)

**Admin UI**:

- Hardcoded colors in admin components (use <!-- FILL: your design token convention -->)

---

## Principles

1. **Strict by design** — This gate should be hard to pass. If everything always gets APPROVED, the bar is too low.
2. **Evidence over opinion** — Every claim must be backed by a command output, MCP result, or code trace. No "looks good to me."
3. **Risk-proportionate** — Light changes get a checklist. Deep changes get a Devil's Advocate agent. Don't hold a docs commit to Deep standards.
4. **Verify, don't trust** — Use MCP tools to confirm claims. "RLS is fine" → prove it with `get_advisors`.
5. **Flag the landmines** — Read `.claude/landmines.md` and cross-reference patterns against the diff. This is a step, not a suggestion.
6. **Constructive, not adversarial** — Find real problems. Recognize strengths. Suggest improvements.
7. **Existing patterns over new patterns** — If the codebase does X one way, new code should too.

---

## Skill Pipeline

```
/plan → /sign-off → [implement] → /code-review → /qa → commit → push → PR → /review-pr (in develop)
                                        ↑
                                   you are here
                            (the strict analytical gate)
```
