# Active Work

This directory contains planning documents for features and tasks currently in progress.

## Lifecycle

```
📋 PLANNING (0%) → 🔧 IN PROGRESS (5-95%) → ✅ COMPLETE (100%) → move to docs/completed/
```

### Creating a New Plan

Run `/plan` to create a planning document. The skill creates files here automatically.

### Document States

| State | Marker | Meaning |
|-------|--------|---------|
| Planning | `📋 PLANNING (0%)` | Plan written, awaiting approval |
| In Progress | `🔧 IN PROGRESS (X%)` | Approved, work underway |
| Complete | `✅ COMPLETE (100%)` | All tasks done, ready to archive |

### Completion Rules

When a document reaches `✅ COMPLETE (100%)`:

1. **Verify** all task checkboxes are checked
2. **Move** to `docs/completed/` immediately
3. **Update** cross-references (search for old path)
4. **Update** core docs (INCOMPLETE_FEATURES, ROADMAP, etc.)

**A completed document must never remain in `docs/active/`.** See the DDD rule (`document-driven-dev.md`) for full archival requirements.

## Current Active Plans

_None yet. Run `/plan` to create your first planning document._
