---
name: sign-off
description: Quality gate for planning documents. Tiered review matching plan risk level. Use after /plan, before implementation.
allowed-tools: Read, Glob, Grep, Task, AskUserQuestion, mcp__database__execute_sql, mcp__database__get_advisors, mcp__database__list_tables
---

# Sign-Off Skill

Quality gate that verifies plan accuracy, completeness, and implementation-readiness. Review rigor scales with the plan's risk tier. Dimensions align 1:1 with plan sections.

## When to Use

- After `/plan`, before implementation
- When iterating on a plan that previously got NO-GO
- User says `/sign-off`, "review the plan", "is the plan ready?"

## When NOT to Use

- Plan hasn't been written yet (use `/plan` first)
- Implementation is done (use `/code-review` or `/qa`)
- Trivial 1-2 line fix (skip ceremony)

---

## Step 1: Identify Plan and Tier

Read the plan file (argument or auto-detect from `docs/active/`). Determine the tier from the plan's header:

| Plan Header         | Review Tier     |
| ------------------- | --------------- |
| `Tier: 🟢 Quick`    | Quick Review    |
| `Tier: 🟡 Standard` | Standard Review |
| `Tier: 🔴 Full`     | Full Review     |

If tier isn't marked, classify using the plan skill's risk table (zero-risk = Quick, code-only = Standard, DB/auth/offline = Full).

**Tier mismatch check**: If the plan content clearly exceeds its declared tier (e.g., marked Quick but contains DB queries or auth changes), escalate the review to the correct tier and note the mismatch in the review.

---

## Step 2: Run the Review

### Quick Review — Inline (no agent spawn)

For Quick tier plans, review inline. Pause, mentally reset, and reread the plan as if you've never seen it. Score 4 dimensions, present results. No fresh-eyes agent needed — the overhead isn't warranted for zero-risk work.

**Exception**: If the Quick plan touches code you haven't read this session, spawn an agent for fresh perspective.

### Standard & Full Review — Fresh-Eyes Agent

Spawn a `general-purpose` agent via Task tool. The agent has no session context — plans must stand alone.

**Agent prompt**:

```
You are a thorough quality partner reviewing a planning document. You have not seen this plan before — you're reading it fresh.

Your job: verify the plan is accurate, complete, and ready for implementation at its risk tier. Be honest and constructive. Catch real problems, not hypothetical edge cases. Score proportionately — don't hold a Standard plan to Full plan standards.

## Process

### A. Read the Plan
Read: [PLAN_PATH]

### B. Read Project Standards
Read CLAUDE.md (root) for architecture and conventions.

### C. Spot-Check Claims
Verify claims using tools. Do NOT trust numbers or file lists blindly.

[TIER-SPECIFIC: Standard = 2 checks minimum, Full = 3 checks minimum]

Examples:
- Plan says "X files affected" → glob and count
- Plan says "this query pattern" → grep for it
- Plan says "N violations" → verify the count
- Plan references specific paths → verify they exist

### D. Score Dimensions
Score ONLY the dimensions for this tier. Use 1-10 scale. Be fair, not generous.

[INSERT TIER DIMENSIONS — see section below]

### E. Output Format

---

## Sign-Off Review

**Plan**: [name]
**Tier**: [Quick/Standard/Full]
**Date**: [date]

### Plan Recap

[2-4 sentences summarizing WHAT the plan does, WHY it matters, and its scope. Write for someone who hasn't read the plan.]

### Spot-Checks

| Claim | Method | Result |
|-------|--------|--------|
| [claim] | [how checked] | Confirmed / MISMATCH: [actual] |

### Scores

| # | Dimension | Score | Finding |
|---|-----------|-------|---------|
| 1 | [dim] | X/10 | [1 sentence] |

**Average**: X.X / 10

### Production Risk

- **Level**: [Low / Medium / High]
- **What could go wrong**: [1 sentence — the specific risk to production users if this goes sideways]

### Issues (must fix before GO)

[Numbered list. Empty if none.]

### Suggestions (would strengthen, not blocking)

[Numbered list. Even passing plans get feedback.]

### Strengths

[2-3 bullets. Good work deserves recognition.]

### Verdict

**[GO / GO WITH NOTES / NO-GO]**

[1-2 sentence justification]

---
```

---

## Dimensions by Tier

### Quick Review (4 dimensions)

| #   | Dimension        | Checks                                  | Maps to Plan Section |
| --- | ---------------- | --------------------------------------- | -------------------- |
| 1   | **Accuracy**     | File paths, names, references correct?  | Tasks + Files        |
| 2   | **Completeness** | Anything missing from task list?        | Tasks                |
| 3   | **Clarity**      | Can implement without asking questions? | What & Why           |
| 4   | **Verification** | Do checks actually prove it works?      | Verification         |

### Standard Review (7 dimensions, UX Design scored only if UI changes — SKIP otherwise)

| #   | Dimension        | Checks                                                                         | Maps to Plan Section         |
| --- | ---------------- | ------------------------------------------------------------------------------ | ---------------------------- |
| 1   | **Accuracy**     | File paths, references, counts correct?                                        | Tasks + Files                |
| 2   | **Completeness** | Tasks cover the full scope?                                                    | Tasks + Solution Design      |
| 3   | **Clarity**      | Unambiguous, implementation-ready?                                             | What & Why + Solution Design |
| 4   | **UX Design**    | User context defined? Journey mapped? Wireframe present? 8 principles checked? | UX Brief (Solution Design)   |
| 5   | **Blast Radius** | Impact analysis honest? Regressions identified?                                | Files & Blast Radius         |
| 6   | **Test Quality** | Assertions specific and measurable? CRITICAL-07 lesson applied? E2E specs listed (or explicitly stated as N/A)?               | Test Plan                    |
| 7   | **Rollback**     | Undo strategy realistic? Time estimate credible?                               | Rollback                     |

### Full Review (9 dimensions, UX Design scored only if UI changes — SKIP otherwise)

| #   | Dimension              | Checks                                                                         | Maps to Plan Section         |
| --- | ---------------------- | ------------------------------------------------------------------------------ | ---------------------------- |
| 1   | **Accuracy**           | Claims verified via MCP? Counts match?                                         | Tasks + Files                |
| 2   | **Completeness**       | Full scope covered? Edge cases?                                                | Tasks + Solution Design      |
| 3   | **Clarity**            | Unambiguous, implementation-ready?                                             | What & Why + Solution Design |
| 4   | **UX Design**          | User context defined? Journey mapped? Wireframe present? 8 principles checked? | UX Brief (Solution Design)   |
| 5   | **Blast Radius**       | Impact honest? Dependencies identified?                                        | Files & Blast Radius         |
| 6   | **Test Quality**       | Specific assertions? Server-side verified? E2E specs listed for blast-radius?                                    | Test Plan                    |
| 7   | **Scale & Resilience** | 10x analysis real? Failure modes covered? Recovery paths credible?             | Scalability & Failure Modes  |
| 8   | **Security & Risk**    | RLS impact assessed? Rollback tested? Risk level honest?                       | Security & Risk              |
| 9   | **Honesty**            | Gaps acknowledged? Limitations stated? Tech debt flagged?                      | Enforcement Gaps             |

---

## Thresholds

```
Tier        │ GO               │ GO WITH NOTES       │ NO-GO
────────────┼──────────────────┼─────────────────────┼───────────────────
Quick       │ avg >= 7         │ avg 6-6.9           │ any dim < 5 OR avg < 6
Standard    │ avg >= 7.5       │ avg 6.5-7.4         │ any dim < 6 OR avg < 6.5
Full        │ avg >= 8         │ avg 7-7.9           │ any dim < 7 OR avg < 7
```

### GO

Plan is solid. Ready for implementation. Proceed when CEO confirms.

### GO WITH NOTES

Plan is good enough. Notes are captured as implementation reminders — not blockers. Prevents infinite iteration loops. Proceed when CEO confirms.

### NO-GO

Real issues found that would cause problems in implementation. Fix the specific issues listed, then re-run `/sign-off`.

---

## Step 2.5: Self-Correction Loop

After scoring, check if the plan meets the **convergence target** (distinct from the formal GO threshold above):

| Tier     | Convergence Target        | Max Iterations |
| -------- | ------------------------- | -------------- |
| Quick    | avg ≥ 9, no dimension < 8 | 3 rounds       |
| Standard | avg ≥ 9, no dimension < 8 | 3 rounds       |
| Full     | avg ≥ 9, no dimension < 8 | 3 rounds       |

**Important**: Convergence targets are aspirational. The formal GO/NO-GO thresholds above are unchanged. If the loop exhausts its budget at 8.2, that's still GO — just not as polished.

### Loop Flow

```
Score plan → Target met?
    ├── Yes → Present clean result (Step 3)
    └── No → Identify weakest 1-2 dimensions
                 → Edit plan to strengthen them
                 → Re-score (fresh-eyes for Standard/Full)
                 → Target met OR budget exhausted OR stuck?
                      ├── Met → Present clean result
                      ├── Budget → Present best + honest score
                      └── Stuck → Escalate to CEO with context
```

### What Sign-Off Can Edit (Editing Boundary)

Sign-off becomes both reviewer AND editor during self-correction. Explicit boundary:

| CAN strengthen (HOW)               | MUST escalate (WHAT)           |
| ---------------------------------- | ------------------------------ |
| Strengthen explanations and detail | Add or remove tasks            |
| Add missing verification criteria  | Change architectural decisions |
| Fix factual inaccuracies           | Alter scope (features in/out)  |
| Tighten vague assertions           | Change technology choices      |
| Add missing edge case coverage     | Modify business requirements   |

**Golden rule**: If the edit changes WHAT we're building → escalate. If it changes HOW we describe or verify it → self-correct.

### Before Looping (Anti-Scope-Reduction — G4)

Snapshot before first iteration:

- Task count from the plan
- File count from the plan

After each iteration, compare. Flag if either shrank.

### Re-Scoring Rules

| Tier     | Re-Score Method                           | Guardrail            |
| -------- | ----------------------------------------- | -------------------- |
| Quick    | Inline re-score (same context)            | G5: log what changed |
| Standard | Fresh-eyes agent spawn (no prior context) | G2 + G5 + G6         |
| Full     | Fresh-eyes agent spawn (no prior context) | G2 + G5 + G6         |

### Diff Transparency (G5)

Each iteration logs:

- What dimension was targeted
- What was changed in the plan (1-line summary for Quick, iteration table for Standard/Full)
- Score before → after

### Re-Verify After Edit (G6)

After editing the plan, re-run spot-checks on the changed sections — don't just re-score subjectively. Verify that new claims are accurate.

### Iteration Output

Show in final output: `"Converged in N rounds (X.X → Y.Y → Z.Z)"`

If budget exhausted without convergence: `"Best after 3 rounds: X.X (target: 9.0)"`

---

## Step 3: Present CEO Brief

After review (inline or from agent), present in accessible language:

```markdown
## Sign-Off: [Plan Name]

### Plan Recap

[2-4 sentences summarizing WHAT the plan does, WHY it matters, and its scope. Write for someone who hasn't read the plan — this makes the review self-contained.]

### Bottom Line

[1-2 sentences. Is it ready? Plain language.]

### Review Summary

- Tier: [Quick/Standard/Full]
- Spot-checked [N] claims
- Scored [N] dimensions → **avg X.X / 10**

### Production Risk

- **Level**: [Low / Medium / High]
- **What could go wrong**: [1 sentence — the specific risk to production users if this goes sideways]

### Issues

[If NO-GO: numbered list, plain language]
[If GO/GO WITH NOTES: "No blocking issues." + any notes]

### Verdict: [GO / GO WITH NOTES / NO-GO]

[If GO]: Ready for implementation. Proceed when you say "go for it".
[If GO WITH NOTES]: Ready with minor notes captured. Proceed when you say "go for it".
[If NO-GO]: Fix these issues, then `/sign-off` again.
```

---

## Step 4: Handle Verdict

### On GO or GO WITH NOTES

- Do NOT auto-start implementation
- Wait for CEO to say "go for it" / "proceed" / "approved"
- Sign-off confirms quality — CEO confirms the green light

### On NO-GO

- List specific issues to fix
- User (or Claude) updates the plan
- Run `/sign-off` again after fixes
- Expect 1-2 rounds max for Standard/Full, 0 for Quick

---

## Spot-Check Scaling

| Tier     | Min Checks | What to Verify                       |
| -------- | ---------- | ------------------------------------ |
| Quick    | 1          | File paths exist, names correct      |
| Standard | 2          | + Code patterns referenced exist     |
| Full     | 3          | + DB claims via MCP, EXPLAIN ANALYZE |

### Spot-Check Examples by Tier

**Quick** — verify file references exist:

```bash
# Plan says "modify src/components/StatusCard.tsx"
ls -la src/components/StatusCard.tsx
# PASS: file exists. MISMATCH: file not found → plan has wrong path
```

**Standard** — verify file references + code claims:

```bash
# Plan says "StatusCard has 3 variants at line 42"
# 1. Verify the file
wc -l src/components/StatusCard.tsx    # PASS: file exists, line count plausible
# 2. Verify the code claim
grep -n "status" src/components/StatusCard.tsx | head -5    # PASS: status logic at ~line 42
```

**Full** — verify file references + code claims + DB claims:

```bash
# Plan says "12 RLS policies on orders table"
# Via MCP:
mcp__database__execute_sql("SELECT count(*) FROM pg_policies WHERE tablename = 'orders'")
# PASS: count matches 12. MISMATCH: actual count differs → plan has stale number
```

### Edge Function Observability Gate

If the plan creates or modifies serverless functions, verify:

- [ ] Sentry import + init block present (graceful degrade pattern)
- [ ] `Sentry.captureException()` at every catch site with operation tags
- [ ] `Sentry.flush(2000)` before error responses
- [ ] Function still works if `SENTRY_DSN` is missing (check `if (sentryDsn)` guard)

See landmine #15 in `.claude/landmines.md` for the full pattern.

---

## Principles

1. **Risk-proportionate** — Quick plans get Quick reviews. Don't hold a prompt file to DB migration standards.
2. **Aligned with /plan** — Every plan section maps to exactly one sign-off dimension. No orphans.
3. **Verify, don't trust** — Spot-checking is mandatory. Numbers drift from reality.
4. **Constructive, not adversarial** — Find real problems, suggest improvements, recognize strengths.
5. **GO WITH NOTES prevents loops** — An 8/10 plan is production-ready. Capture feedback, don't block.
6. **Even GO plans get suggestions** — A 9 can become a 10. Always offer improvements.
7. **Iteration is healthy, not infinite** — NO-GO means real issues. 1-2 rounds, not 5+.

---

## Skill Pipeline

```
/research → /brainstorm → /ux-design → /plan → /sign-off → CEO approval → /worktree create → implement → /code-review → /qa → commit → push → PR → /review-pr (in develop)
                                                    ↑                                                                                │
                                                    └── NO-GO (1-2 rounds max) ────────────────────────────────────────────────────────┘
```

### Dual Context

`/sign-off` works in both worktree contexts:

| Context              | What it reviews                                  | Trigger                              |
| -------------------- | ------------------------------------------------ | ------------------------------------ |
| **Main worktree**    | Planning documents (`docs/active/*.md`)          | After `/plan`, before implementation |
| **Feature worktree** | Implementation quality (optional, for high-risk) | After `/qa`, before push (rare)      |
