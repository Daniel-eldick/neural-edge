---
name: plan
description: Active DDD assistant that creates planning documents. Use when starting new features or fixes.
allowed-tools: Read, Write, Edit, Glob, Bash, AskUserQuestion, mcp__database__list_tables, mcp__database__execute_sql, mcp__database__get_advisors, mcp__shadcn__search_items_in_registries, mcp__shadcn__view_items_in_registries, mcp__chrome-devtools__take_snapshot
---

# Plan Skill

Creates planning documents with MCP-verified context. Three tiers match risk to rigor.

## When to Use

- `/plan`, "plan this feature", "start a new feature", "fix this bug"
- Any non-trivial work (3+ files or unclear scope)

**Need current facts?** Run `/research` first. **Not sure what to build?** Run `/brainstorm`. Plan documents a decided approach.

---

## Step 1: Classify Risk Tier

| Tier         | Criteria                                                  | Examples                                         |
| ------------ | --------------------------------------------------------- | ------------------------------------------------ |
| **Quick**    | Zero production risk. No code, no DB, no auth, no offline | Skills, docs, config, copy, CSS-only             |
| **Standard** | Production code. No DB/auth/offline                       | UI components, refactors, hooks, API integration |
| **Full**     | DB, RLS, auth, offline sync, or security                  | Schema, RPC, sync manager, service worker        |

**Rule**: If in doubt, go one tier UP.

**Escalation (hard stop)**: If during context gathering or planning you discover DB/auth/offline impact that wasn't initially apparent — STOP, upgrade the tier, and regenerate from the correct template. Do not retrofit a Quick template with Full-tier content.

**Quick plan guard**: Quick plans must not introduce new abstractions, patterns, or architectural concepts. If the work requires inventing something new, it's at least Standard.

---

## Step 2: Context Gathering

### Quick Plans

- Read relevant files to verify paths and names
- MCP verification: optional

### Standard Plans

- Read affected files and understand patterns
- For UI: `mcp__shadcn__search_items_in_registries` for components
- Check `.claude/references/claude-cookbooks.md` for relevant architecture patterns or prior art
- Scan `landmines.md` — add relevant prevention checks to Test Plan
- **Edge Function check**: If creating/modifying Edge Functions, verify Sentry observability (see landmine #15)

### Full Plans (all of the above, plus)

- `mcp__database__list_tables` — schema context
- `mcp__database__execute_sql` — data patterns, EXPLAIN ANALYZE
- `mcp__database__get_advisors` — security and performance audit
- Full `landmines.md` scan (all 15 patterns)
- Engineering Philosophy gate (all 6 questions):
  - [ ] What happens at 10x load?
  - [ ] What happens when this fails?
  - [ ] N+1 query risk?
  - [ ] Memory leak potential over weeks?
  - [ ] Worst-case performance?
  - [ ] Distributed systems footgun?

---

## Step 3: Create Planning Document

File: `docs/active/[DESCRIPTIVE_NAME].md`

Use the template matching the tier. **Every numbered section maps to exactly one sign-off dimension** — this is by design.

### Quick Plan Template (4 sections)

```markdown
# [Name]

**Status**: 📋 PLANNING (0%) | **Tier**: 🟢 Quick | **Risk**: Zero/Low
**Created**: [Date]

## 1. What & Why

[Problem + solution in 2-4 sentences. What changes, why it matters.]

## 2. Tasks

| #   | Task   | Status |
| --- | ------ | ------ |
| 1   | [task] | [ ]    |

**Scope guard**: [N] tasks. Stop if > [N × 1.5].

## 3. Files

| File   | Action        | Purpose |
| ------ | ------------- | ------- |
| `path` | Create/Modify | [why]   |

## 4. Verification

- [ ] [Specific, measurable check that proves this works]

## Progress Log

| Date    | Update       | %   |
| ------- | ------------ | --- |
| [today] | Created plan | 0%  |
```

### Standard Plan Template (6 sections)

```markdown
# [Name]

**Status**: 📋 PLANNING (0%) | **Tier**: 🟡 Standard | **Risk**: Medium
**Created**: [Date]

## 1. What & Why

[Problem, solution, business value.]

## 2. Solution Design

> **UI features**: If this feature has a user-facing component, include the UX Brief from `/ux-design` here — user context, journey map, wireframe, and heuristic compliance. If `/ux-design` wasn't run, document at minimum: who uses this, what's the primary action, and how it looks (ASCII wireframe or description).

[Approach, key decisions, alternatives considered. ASCII mockup if UI.]

## 3. Tasks

### Phase 1: [Name]

| #   | Task   | Test approach                                                 | Status |
| --- | ------ | ------------------------------------------------------------- | ------ |
| 1   | [task] | [How this will be verified — test name, manual check, or N/A] | [ ]    |

> **TDD gate (Standard)**: Each task must identify its test approach BEFORE implementation begins. If a task changes behavior, describe the failing test to write first. Skip for pure refactors where existing tests cover the behavior.

**Scope guard**: [N] tasks. Stop if > [N × 1.5].

## 4. Files & Blast Radius

| File   | Action | Used By    | Regression Risk |
| ------ | ------ | ---------- | --------------- |
| `path` | Modify | [features] | Low/Med/High    |

If High risk: add regression test to section 5.

## 5. Test Plan

**CRITICAL-07 rule**: Every test must have a specific, measurable assertion.
**E2E specs**: [List specific E2E specs/directories to run via `/test blast`, OR state "None — no production code changes" if only skill/doc/config files are modified. This makes blast-radius routing explicit.]

| What to verify                | Type            | Status |
| ----------------------------- | --------------- | ------ |
| [specific measurable outcome] | Unit/E2E/Manual | [ ]    |

New UI elements: define `data-testid` values here.

## 6. Rollback

[How to undo. Time estimate. Data loss risk.]

---

### Admin Design System Check

> Skip if no admin UI changes.

- [ ] All colors use <!-- FILL: your design token convention --> (no hardcoded colors)
- [ ] `npm run lint` passes (linter enforces at error level)
- [ ] Tested in BOTH light and dark mode
- [ ] Reference: <!-- FILL: your design system guide path -->

### Landmine Check

[Only patterns relevant to this work, from .claude/landmines.md]

### Engineering Check

- [ ] What happens when this fails?
- [ ] N+1 query risk?
- [ ] Can this be feature-flagged?

## Progress Log

| Date    | Update       | %   |
| ------- | ------------ | --- |
| [today] | Created plan | 0%  |
```

### Full Plan Template (8 sections)

```markdown
# [Name]

**Status**: 📋 PLANNING (0%) | **Tier**: 🔴 Full | **Risk**: High/Critical
**Created**: [Date]

## 1. What & Why

[Problem, solution, business value. Quantified impact.]

## 2. Solution Design

> **UI features**: If this feature has a user-facing component, include the UX Brief from `/ux-design` here — user context, journey map, wireframe, and heuristic compliance. If `/ux-design` wasn't run, document at minimum: who uses this, what's the primary action, and how it looks (ASCII wireframe or description).

[Architecture, decisions, trade-offs. Diagrams if helpful.]

## 3. Tasks

### Phase 1: [Name]

| #   | Task                                     | Failing test                           | Status |
| --- | ---------------------------------------- | -------------------------------------- | ------ |
| 0   | Write failing tests for Phase 1 behavior | [test file + assertion names]          | [ ]    |
| 1   | [task]                                   | [test from task 0 that validates this] | [ ]    |

> **TDD gate (Full)**: Every phase MUST start with a "Write failing tests" task (task 0). Implementation tasks reference which failing test they will make pass. No production code without a failing test first.
>
> **If you catch yourself writing code before the test**: STOP. Delete the code. Write the test. Start over. This is non-negotiable at Full tier.

**Scope guard**: [N] tasks. Stop if > [N × 1.5].

## 4. Files & Blast Radius

| File   | Action | Used By    | Regression Risk |
| ------ | ------ | ---------- | --------------- |
| `path` | Modify | [features] | Low/Med/High    |

If High risk: add regression test to section 5.

## 5. Test Plan

**CRITICAL-07 rule**: Every test must have a specific, measurable assertion.
**E2E specs**: [List specific E2E specs/directories to run via `/test blast`. Full-tier plans MUST have E2E coverage — state which spec files/directories validate the changes.]

| What to verify                | Type            | testid   | Status |
| ----------------------------- | --------------- | -------- | ------ |
| [specific measurable outcome] | Unit/E2E/Manual | [if E2E] | [ ]    |

Test-first: Phase 1 includes test scaffolding.

## 6. Scalability & Failure Modes

**10x Load**:

- [ ] Database: N+1 queries? Indexes needed?
- [ ] Memory: Could this leak over weeks?
- [ ] Concurrency: 50+ simultaneous operations?
- [ ] Connections: Pool exhaustion risk?

**MCP Verification**:

- [ ] `EXPLAIN ANALYZE` for new queries
- [ ] `get_advisors({ type: "performance" })` for index recs

**Failure Scenarios**:

| Scenario                    | System Behavior | Recovery   |
| --------------------------- | --------------- | ---------- |
| Backend down 1hr           | [describe]      | [describe] |
| Network loss mid-operation  | [describe]      | [describe] |
| Concurrent operations (50+) | [describe]      | [describe] |

## 7. Security & Risk

- RLS impact: [describe]
- Auth changes: [describe]
- Rollback strategy: [how, time estimate, data loss risk]
- Red flags: [ ] None / [ ] Identified (detail below)

## 8. Enforcement Gaps

What this plan WON'T catch:

- [limitation 1]
- [limitation 2]

Tech debt accepted: [describe, add to TECHNICAL_DEBT.md if significant]

---

### Admin Design System Check

> Skip if no admin UI changes.

- [ ] All colors use <!-- FILL: your design token convention --> (no hardcoded colors)
- [ ] `npm run lint` passes (linter enforces at error level)
- [ ] Tested in BOTH light and dark mode
- [ ] Reference: <!-- FILL: your design system guide path -->

### Landmine Check (full scan)

[All 15 patterns from .claude/landmines.md checked]

### Engineering Philosophy Gate

- [ ] What happens at 10x load?
- [ ] What happens when this fails?
- [ ] N+1 query risk?
- [ ] Memory leak potential over weeks?
- [ ] Worst-case performance?
- [ ] Distributed systems footgun?
- [ ] Config over code: feature-flaggable?
- [ ] Incremental: extending patterns, not creating?
- [ ] Reversible: disable without rollback?

### Pre-Approval MCP Verification

- [ ] `get_advisors({ type: "security" })` — no new warnings
- [ ] `get_advisors({ type: "performance" })` — no regressions
- [ ] `EXPLAIN ANALYZE` — acceptable query performance
- [ ] Cross-tenant isolation verified (if applicable)

## Progress Log

| Date    | Update       | %   |
| ------- | ------------ | --- |
| [today] | Created plan | 0%  |
```

---

## Step 4: Present to User

```markdown
## Plan Ready for Review

**Document**: `docs/active/[NAME].md`
**Tier**: 🟢 Quick / 🟡 Standard / 🔴 Full
**Problem**: [1 sentence]
**Solution**: [1 sentence]
**Tasks**: [N tasks]
**Risk**: [Low/Medium/High — brief rationale]

**Next step**: Run `/sign-off` to quality-gate this plan, or tell me what to adjust first.
```

---

## Step 5: After Approval

1. Update status: `🔧 IN PROGRESS (5%)`
2. Update task checkboxes in real-time
3. If scope grows > 1.5x → STOP and re-evaluate with user
4. On completion: status → `✅ COMPLETE (100%)`, move to `docs/completed/`, update core docs

---

## Skill Pipeline

```
/plan → [/db-audit if DB] → /sign-off → CEO approval → /worktree create → implement → /code-review → /qa → commit → push → PR → /review-pr (in develop)
```
