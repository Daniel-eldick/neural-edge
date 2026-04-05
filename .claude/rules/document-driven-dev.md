---
description: Document-Driven Development workflow
globs:
  - 'docs/active/**'
  - 'docs/completed/**'
  - 'INCOMPLETE_FEATURES.md'
  - 'TECHNICAL_DEBT.md'
  - 'BACKLOG.md'
---

# Document-Driven Development (DDD) - MANDATORY

**User Mandate** (November 23, 2025): _"Document the plan to fix, the plan to test, and once approved we move to development. Keep updating the same documentation files with progress and completion percentage."_

## Core Principle

**Plan → Document → Approve → Execute → Update → Archive**

**Never write code without**:

1. Planning document in `docs/active/` (comprehensive plan + test plan)
2. User approval ("go for it" confirmation)
3. Real-time progress updates (% completion, timestamps)

## Why This Matters

**Lesson from CRITICAL-07** (November 23, 2025):

- Bug discovered by manual testing (E2E Test 2.4 missed it - wrong success criteria)
- Offline orders never synced (missing `sync_status: 'pending'` field)
- **DDD prevents this**: Forces "How will I test this?" thinking BEFORE coding
- Can't get approval without test plan → Forces quality

**Benefits**: Single source of truth, progress visibility, audit trail, prevents shortcuts

## Quick Workflow

1. Create `docs/active/ISSUE_NAME.md` (problem, fix plan, test plan, checkboxes)
2. Get approval (walk through test plan)
3. Execute with updates (check off tasks, update %, add timestamps)
4. Archive to `docs/completed/` when done (update 5 core docs)

**Document States**: 📋 PLANNING (0%) → 🔧 DEVELOPMENT (45%) → ✅ COMPLETE (100%)

## Anti-Patterns

- "Fix quickly, document later"
- Plan in chat only
- Skip test plan
- Code before approval

**Always**: Plan → Approve → Execute → Archive

## 5 Core Documents (MUST Stay Synchronized)

1. **docs/INCOMPLETE_FEATURES.md** - Check FIRST at every session start
2. **docs/PRODUCTION_READINESS_ROADMAP.md** - Single source of truth for production %
3. **docs/OFFLINE_SYSTEM_STATUS.md** - Health dashboard
4. **docs/TECHNICAL_DEBT.md** - Real scalability debt
5. **docs/BACKLOG.md** - Future features & optimizations

## Core Doc Update Frequency

**Update core docs at milestones, not every commit.** This reduces friction on multi-commit features.

**Milestones that trigger core doc updates**:

1. **Feature start** — Add entry to INCOMPLETE_FEATURES.md
2. **Blocked event** — Update status in relevant core docs
3. **Scope change** — Update task counts, add new entries if needed
4. **Feature complete** — Update all 5 core docs, archive planning doc

**NOT a milestone** (skip core doc updates):

- Intermediate commits during implementation
- Progress percentage changes within a phase
- Minor code adjustments between phases

**The active planning doc** (`docs/active/*.md`) should still be updated in real-time with task checkboxes and progress log entries — this is the working document. The 5 core docs are the summary layer.

**`/sync-docs` remains available** for periodic alignment checks after major work.

---

## Documentation Lifecycle

**When Completing Work**:

1. Update all living documents with completion status
2. Move completed reports to `docs/completed/`
3. Archive reference documents to `docs/archive/` if applicable
4. Update cross-references

**Before Moving to New Work**:

1. Verify all documents aligned
2. Archive all completed work
3. Update master roadmap if necessary
4. Challenge user if distracting from documented plan

## Archival Verification Gate (MANDATORY)

**Before moving ANY document to `docs/completed/`**, verify it's actually complete:

```
┌─────────────────────────────────────────────────────────┐
│  STOP: Before archiving, run all 4 checks:              │
│  1. Read every task checkbox in the plan                 │
│  2. Verify checked tasks against actual code/tool output │
│  3. Confirm status header says ✅ COMPLETE               │
│  4. Compare plan task count against PR file list          │
│  ALL must pass. "PR merged" ≠ "plan complete".           │
└─────────────────────────────────────────────────────────┘
```

**Why**: March 24, 2026 postmortem — two plans (DEFENSE_STACK_V2, INBOUND_01) were nearly archived as "complete" when they were only ~70-79% done. The PR merged successfully, but the plans had unfinished tasks (Edge Functions not redeployed, DB migrations not applied, manual items pending). "PR merged" is not proof of "plan complete."

## Location Verification (MANDATORY)

**After marking any document ✅ COMPLETE** (and passing the Archival Verification Gate above):

```
┌─────────────────────────────────────────────────────────┐
│  STOP: Is the file still in docs/active/?               │
│  If YES → Move to docs/completed/ IMMEDIATELY           │
└─────────────────────────────────────────────────────────┘
```

**Checklist (must complete before session end)**:

- [ ] File with ✅ COMPLETE status moved to `docs/completed/`
- [ ] Cross-references updated (search for old path)
- [ ] No "COMPLETE" files remain in `docs/active/`

**Why**: Files in `docs/active/` signal ongoing work. Leaving completed work there causes confusion and process drift.

## COMPLETION TRIGGER (MANDATORY)

**When I write "✅ COMPLETE" or "100%" in any document:**

1. **STOP** immediately after that edit
2. **CHECK**: Is this file in `docs/active/`?
3. **If YES**: Move to `docs/completed/` NOW (before any other work)
4. **UPDATE**: All cross-references (grep for old path)
5. **ONLY THEN**: Continue with other tasks

```
┌─────────────────────────────────────────────────────────┐
│  ✅ COMPLETE written? → ARCHIVE IMMEDIATELY             │
│  This is NOT optional. Archive BEFORE moving on.        │
└─────────────────────────────────────────────────────────┘
```
