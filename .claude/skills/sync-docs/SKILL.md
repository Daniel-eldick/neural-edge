---
name: sync-docs
description: Check and fix document synchronization across core docs. Use to verify alignment after major work.
allowed-tools: Read, Edit, Glob, Grep, Bash
---

# Sync Docs Skill

Check and fix synchronization across the 5 core documents + active docs.

## When to Use

- `/sync-docs`, "check document sync", "are docs aligned"
- After completing major work (DDD milestone: feature complete)
- When `/session-start` detects violations and recommends sync
- Before starting new features (verify clean baseline)

## When NOT to Use

- For moving/archiving files (use `/organize`)
- For process health checks (use `/wow-audit`)
- For code-level cleanup (use `/hygiene`)
- Mid-implementation (wait for a DDD milestone)

**Ownership boundary**: `/sync-docs` owns **content alignment** between the 5 core docs and active docs. `/organize` owns **file structure** (moving, archiving). `/wow-audit` owns **process health** (commit patterns, rules freshness).

---

## Run Modes

### Full Audit (default)

Run all 5 checks, comprehensive report.

### Focused Check

Run a single check when coming from `/session-start`:

- `archival` — Check 3 only (completed docs not archived)
- `staleness` — Check 4 only (stale active docs)
- `orphaned` — Check 2 only (orphaned active docs)

Example: "Run /sync-docs to fix archival violations" → Skip to Check 3 only.

---

## Documents to Check (6 Sources)

| #   | Document                               | Purpose                                 |
| --- | -------------------------------------- | --------------------------------------- |
| 1   | `docs/INCOMPLETE_FEATURES.md`          | Feature tracker                         |
| 2   | `docs/PRODUCTION_READINESS_ROADMAP.md` | Master plan (source of truth for %)     |
| 3   | `docs/OFFLINE_SYSTEM_STATUS.md`        | Health dashboard (must match roadmap %) |
| 4   | `docs/TECHNICAL_DEBT.md`               | Scalability concerns                    |
| 5   | `docs/BACKLOG.md`                      | Future work                             |
| 6   | `docs/active/*`                        | All active planning docs                |

---

## Checks

### Check 1: Percentage Alignment

`PRODUCTION_READINESS_ROADMAP.md` is source of truth. `OFFLINE_SYSTEM_STATUS.md` must match within 5%.

### Check 2: Orphaned Active Docs

Files in `docs/active/` should have corresponding entries in `INCOMPLETE_FEATURES.md`. Flag orphans (unless 100% complete — that's Check 3).

### Check 3: Completed Docs Not Archived

Search `docs/active/` for `✅ COMPLETE`, `Status: 100%`, `COMPLETE (100%)`. Any matches should be moved to `docs/completed/`.

### Check 4: Stale Active Docs

Active docs not modified in >14 days may be abandoned. Flag for review.

### Check 5: Cross-Reference Integrity

Links in INCOMPLETE_FEATURES.md point to existing files. BACKLOG.md items don't duplicate INCOMPLETE_FEATURES.md.

---

## Workflow

### 1. Read All Documents

Read all 5 core docs + glob `docs/active/*.md`.

### 2. Run Checks

Focused mode: run only the specified check. Full audit: run all 5.

### 3. Report Findings

```markdown
## Document Sync Report

**Date**: YYYY-MM-DD

### Sync Status

| Check                     | Status    | Details   |
| ------------------------- | --------- | --------- |
| Percentage alignment      | PASS/FAIL | [details] |
| Orphaned active docs      | PASS/FAIL | [details] |
| Completed not archived    | PASS/FAIL | [details] |
| Stale active docs         | PASS/FAIL | [details] |
| Cross-reference integrity | PASS/FAIL | [details] |

### Issues Found

[Critical issues, then warnings]

### Recommended Fixes

| Issue   | Fix      | Approval Needed |
| ------- | -------- | --------------- |
| [issue] | [action] | Yes/No          |
```

### 4. Offer Fixes (with approval)

For each issue, propose a specific fix. Apply only after user approval.

**Use `git mv`** for all file moves (NOT `mv` — preserves git history).

---

## Principles

1. **Content alignment, not file management** — That's `/organize`'s job.
2. **PRODUCTION_READINESS_ROADMAP is source of truth** — Other docs align TO it, not the reverse.
3. **`git mv` always** — Never use bare `mv` for file moves (Landmine #10 pattern).
4. **Focused mode is fast** — When coming from `/session-start`, fix the specific issue and exit.
5. **Milestone-driven** — Run after DDD milestones, not after every commit.

---

## Anti-Patterns

- Using `mv` instead of `git mv` for file moves
- Modifying files without explicit approval
- Running full audit when focused check was requested
- Duplicating `/organize` file-structure checks
- Duplicating `/wow-audit` process-health checks
- Deleting files (only move to completed/ or archive/)

---

## Skill Pipeline

```
/session-start → (detects violations) → /sync-docs → (fixes alignment) → resume work
Also: after major feature completion, before commit
```
