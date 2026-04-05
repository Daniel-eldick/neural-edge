[← Back to Main Guide](../../CLAUDE.md)

# Development Workflows

Step-by-step workflows for common development tasks, ensuring documentation stays synchronized and quality standards are maintained.

## Core Documents Workflow

**Purpose**: Keeping core documents synchronized during every work session.

### Document Responsibilities

**1. [INCOMPLETE_FEATURES.md](../INCOMPLETE_FEATURES.md) — Simple jump-back list**

- **Update when**: Starting/completing features, discovering bugs, changing priorities
- **Contains**: 🔴 BLOCKING, 🟡 IN PROGRESS, 🟢 PLANNED sections
- **Rule**: Check this FIRST at every session start

**2. [PRODUCTION_READINESS_ROADMAP.md](../PRODUCTION_READINESS_ROADMAP.md) — Master plan**

- **Update when**: Phase completion, task progress, timeline changes
- **Contains**: Phase statuses, time estimates, completion summaries
- **Rule**: This is the single source of truth for production readiness %

**3. [TECHNICAL_DEBT.md](../TECHNICAL_DEBT.md) — Scalability concerns**

- **Update when**: Discovering scalability issues, resolving concerns, deep dive sessions
- **Contains**: CRITICAL/HIGH/MEDIUM/LOW prioritized concerns
- **Rule**: CRITICAL count must match INCOMPLETE_FEATURES.md BLOCKING count

**4. [BACKLOG.md](../BACKLOG.md) — Future work**

- **Update when**: Adding future ideas, deferring work, completing backlog items
- **Contains**: Batched work items, future ideas, deferred items

## Core Workflows

### Workflow: Starting a New Feature

1. **Check** INCOMPLETE_FEATURES.md — Is this feature planned?
2. **Check** PRODUCTION_READINESS_ROADMAP.md — Which phase does it belong to?
3. **Check** TECHNICAL_DEBT.md — Related scalability concerns?
4. **Update** INCOMPLETE_FEATURES.md — Move to 🟡 IN PROGRESS
5. **Run** `/plan` — Create planning document in `docs/active/`
6. **Run** `/sign-off` — Quality gate the plan
7. **Get approval** — CEO says "go for it"
8. **Run** `/worktree create` — Spawn feature workspace
9. **Implement** — Follow the plan, update checkboxes
10. **Run** `/code-review` → `/qa` — Quality gates
11. **Commit, push, create PR** targeting `develop`

### Workflow: Found a Bug

1. **Assess severity** — Is it breaking production?
   - **YES** → Add to INCOMPLETE_FEATURES 🔴 BLOCKING, fix immediately
   - **NO** → Continue assessment
2. **Check scale impact** — Will it break at 10x load?
   - **YES** → Add to TECHNICAL_DEBT.md (HIGH/MEDIUM)
   - **NO** → Add to INCOMPLETE_FEATURES 🟢 PLANNED
3. **If fixing now** — Follow feature workflow (plan, approve, execute)
4. **If deferring** — Document in BACKLOG.md with revisit trigger

### Workflow: Completing Work

1. **Verify** all task checkboxes in the plan are checked
2. **Run** `/code-review` — Must pass
3. **Run** `/qa` — Must pass
4. **Commit** with conventional format
5. **Push** and create PR targeting `develop`
6. **In main worktree** — Run `/review-pr` to merge
7. **Archive** plan to `docs/completed/`
8. **Update** core docs (INCOMPLETE_FEATURES, ROADMAP, etc.)

### Workflow: Session Start

1. **Run** `/session-start` (or manually):
   - Read INCOMPLETE_FEATURES.md — any blockers?
   - Read TECHNICAL_DEBT.md — any new concerns?
   - Check `docs/active/` — any in-progress plans?
2. **Check git status** — which branch? Any uncommitted work?
3. **Decide** what to work on based on priorities

### Workflow: Documentation Sync

Run `/sync-docs` after major work to verify all core docs agree. Fix any conflicts before starting new work.

---

## Workflow Quick Reference

| I want to... | Run this... |
|---------------|-------------|
| Start a feature | `/plan` → `/sign-off` → CEO approval → `/worktree create` |
| Fix a bug | Assess severity → `/plan` (if non-trivial) → implement → `/qa` |
| Ship to staging | `/deploy` or merge PR to `develop` via `/review-pr` |
| Ship to production | `/release` (CEO must say "ship it") |
| Check project health | `/session-start` or read core docs |
| Deep-dive a system | `/investigate` |
| Monthly maintenance | `/hygiene` + `/organize` + `/sync-docs` |

---

[Back to CLAUDE.md](../../CLAUDE.md) | [Documentation Hub](../README.md)
