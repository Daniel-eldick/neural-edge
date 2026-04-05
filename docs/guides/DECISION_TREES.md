[← Back to Main Guide](../../CLAUDE.md)

# Decision Trees

Quick decision trees to help rapidly determine which documents need updates and what actions to take for common scenarios.

## Decision Tree 1: I Discovered a Bug

```
START: I found a bug
├─ Is it breaking production? (Users affected NOW)
│  ├─ YES → CRITICAL BUG
│  │  └─ Actions:
│  │     1. Add to INCOMPLETE_FEATURES.md 🔴 BLOCKING section
│  │     2. Add to TECHNICAL_DEBT.md as CRITICAL if scalability issue
│  │     3. Fix immediately (stop all other work)
│  │     4. Follow "Workflow: Found a Bug"
│  │
│  └─ NO → Will it break at scale? (10x load test)
│     ├─ YES → SCALABILITY CONCERN
│     │  └─ Actions:
│     │     1. Add to TECHNICAL_DEBT.md (HIGH/MEDIUM priority)
│     │     2. Document failure scenario with specific numbers
│     │     3. Add to INCOMPLETE_FEATURES.md if blocking
│     │     4. Schedule fix based on severity
│     │
│     └─ NO → MINOR BUG
│        └─ Actions:
│           1. Add to INCOMPLETE_FEATURES.md 🟢 PLANNED
│           2. Fix when convenient
│           3. Update INCOMPLETE_FEATURES.md when fixed
```

## Decision Tree 2: I'm Starting a Feature

```
START: I want to implement a feature
├─ Is it in INCOMPLETE_FEATURES.md 🟢 PLANNED?
│  ├─ YES → Proceed to roadmap check
│  │
│  └─ NO → Is it in PRODUCTION_READINESS_ROADMAP.md?
│     ├─ YES → Add to INCOMPLETE_FEATURES.md first, then proceed
│     │
│     └─ NO → ❌ CHALLENGE THE USER
│        └─ Actions:
│           1. Ask: "This feature isn't in the roadmap. Should we add it?"
│           2. If YES: Update ROADMAP first, then INCOMPLETE_FEATURES
│           3. If NO: Focus on documented priorities
│
├─ Does it interact with TECHNICAL_DEBT.md concerns?
│  ├─ YES → Read concern details, consider impact
│  └─ NO → Continue
│
├─ Is it trivial? (< 3 files, obvious fix)
│  ├─ YES → Implement directly (no /plan needed)
│  └─ NO → Run /plan → /sign-off → get approval → /worktree create
│
└─ Actions:
   1. Move from 🟢 PLANNED to 🟡 IN PROGRESS
   2. Follow "Workflow: Starting a New Feature"
```

## Decision Tree 3: I Completed Work

```
START: I finished my task
├─ What type of work was it?
│  ├─ Bug Fix
│  │  ├─ Was it BLOCKING? → Remove from INCOMPLETE_FEATURES 🔴
│  │  ├─ Was it in TECHNICAL_DEBT? → Mark RESOLVED
│  │  └─ Update ROADMAP if it was phase-tracked
│  │
│  ├─ Feature
│  │  ├─ Move from 🟡 IN PROGRESS → remove (completed)
│  │  ├─ Update ROADMAP phase status
│  │  ├─ Archive plan to docs/completed/
│  │  └─ Update BACKLOG if it was backlog-sourced
│  │
│  └─ Tech Debt Resolution
│     ├─ Mark RESOLVED in TECHNICAL_DEBT.md
│     ├─ Document the fix (what changed, performance improvement)
│     └─ Move to archive summary section
│
└─ Final check: Do all 4 core docs agree on the current state?
   ├─ YES → Done
   └─ NO → Fix the conflict NOW (before starting new work)
```

## Decision Tree 4: Should I Plan or Just Do It?

```
START: I have a task to do
├─ How many files will this touch?
│  ├─ 1-2 files, obvious change → Just do it (no /plan)
│  ├─ 3+ files → Run /plan
│  └─ Unsure → Run /investigate first, then decide
│
├─ Does it change behavior?
│  ├─ YES → Run /plan (even if small)
│  └─ NO (docs, config, formatting) → Just do it
│
├─ Does it touch the database or auth?
│  ├─ YES → Always /plan (Full tier)
│  └─ NO → Standard tier or just do it
│
└─ When in doubt → /plan. The overhead is 10 minutes.
   The cost of a bad change is hours.
```

## Decision Tree 5: Scalability Concern

```
START: I noticed something that might not scale
├─ Is it causing issues NOW?
│  ├─ YES → CRITICAL in TECHNICAL_DEBT.md, fix immediately
│  └─ NO → Continue assessment
│
├─ At 10x current load, would it:
│  ├─ Cause outages? → HIGH in TECHNICAL_DEBT.md
│  ├─ Degrade performance? → MEDIUM in TECHNICAL_DEBT.md
│  └─ Be slightly suboptimal? → LOW in TECHNICAL_DEBT.md
│
├─ Can I fix it as part of current work?
│  ├─ YES (< 30 min) → Fix now, document in TECHNICAL_DEBT as RESOLVED
│  └─ NO → Document and schedule separately
│
└─ Always: specific failure scenarios, not vague concerns
```

---

[Back to CLAUDE.md](../../CLAUDE.md) | [Documentation Hub](../README.md)
