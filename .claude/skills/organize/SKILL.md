---
name: organize
description: Audit and reorganize docs/ and skills/ directories, preventing organizational drift. Use monthly/quarterly for maintenance.
allowed-tools: Read, Bash, Glob, Grep, Edit, Write
---

# Organize Skill

Systematic audit and reorganization of project documentation and skills directories.

## When to Use

- `/organize`, "organize docs", "clean up documentation"
- Monthly/quarterly maintenance
- After major feature completion (when multiple docs need archival)

## When NOT to Use

- For document content alignment (use `/sync-docs`)
- For process health checks (use `/wow-audit`)
- For code-level cleanup (use `/hygiene`)

**Ownership boundary**: `/organize` owns **file structure** (moving, archiving, naming). `/sync-docs` owns content alignment. `/wow-audit` owns process health.

---

## Modes

| Mode             | Description                    | Use Case             |
| ---------------- | ------------------------------ | -------------------- |
| `--plan-only`    | Creates plan without executing | Review before action |
| `--execute`      | Runs moves after approval      | Automated cleanup    |
| `--scope=docs`   | Only audit docs/ directory     | Documentation only   |
| `--scope=skills` | Only audit skills/ directory   | Skills organization  |
| `--scope=all`    | Audit both (default)           | Full cleanup         |

---

## Workflow

### 1. Scan Target Directories

Use Glob tool (not `find`):

```
Glob: docs/**/*.md
Glob: .claude/skills/*/SKILL.md
```

### 2. Detect Issues

#### Documentation Issues

| Issue Type               | Detection                                   | Action                    |
| ------------------------ | ------------------------------------------- | ------------------------- |
| **Completed in active/** | `✅ COMPLETE` or `100%` in `docs/active/`   | Move to `docs/completed/` |
| **Outdated in active/**  | File >3 months old, no updates              | Flag for review           |
| **Orphaned files**       | Files in `docs/` root not in a subdirectory | Move to appropriate dir   |
| **Broken references**    | Links to files that were moved/deleted      | List for manual fix       |

#### Skills Issues

| Issue Type           | Detection                        | Action             |
| -------------------- | -------------------------------- | ------------------ |
| **Missing SKILL.md** | Directory without SKILL.md       | Flag as incomplete |
| **Not in CLAUDE.md** | Skill not listed in skills table | Add to list        |

### 3. Generate Move Plan

For each issue, generate a `git mv` command with rationale:

```bash
git mv docs/active/FEATURE_X.md docs/completed/FEATURE_X.md
```

**Always use `git mv`** (NOT `mv` — preserves history, Landmine #10 pattern).

### 4. Request Approval

Show summary with risk assessment. Never execute without user approval.

**Approval Summary Template** (copy-paste for CEO pitch):

```markdown
## Organization Proposal — [Date]

**Moves**: [N] files | **Risk**: Low (file moves only, no content changes)

| #   | File   | From           | To                | Reason          |
| --- | ------ | -------------- | ----------------- | --------------- |
| 1   | [name] | `docs/active/` | `docs/completed/` | Marked COMPLETE |

**Cross-references to update after moves**: [N files or "none detected"]

**Reversible?** Yes — `git revert` restores all moves. Time: 30 seconds.

Ready to execute when you confirm.
```

### 5. Execute Moves (after approval)

Run `git mv` commands sequentially. Check cross-references for moved files using Grep.

### 6. Report

```markdown
## Organization Complete

**Actions Taken**: [list]
**Cross-references to update**: [list or "none"]
**Next Steps**: `/commit` to save changes
```

---

## Directory Rules

| Directory              | Purpose           | What Belongs                                            |
| ---------------------- | ----------------- | ------------------------------------------------------- |
| `docs/active/`         | Current work      | Planning docs, in-progress features                     |
| `docs/completed/`      | Finished work     | Completed features, resolved issues                     |
| `docs/archive/`        | Historical        | Old proposals, superseded docs                          |
| `docs/guides/`         | Living docs       | How-tos, onboarding, architecture                       |
| `docs/future/`         | Post-MVP planning | Feature proposals, vision docs, wireframes              |
| `docs/infrastructure/` | CI/CD & tooling   | GitHub Actions, MCP guides, deploy checklists           |
| `docs/reference/`      | Permanent refs    | Test accounts, deployment guide, business model         |
| `docs/security/`       | Audits & policies | Security audits, RLS queries, vulnerability assessments |
| `docs/architecture/`   | System design     | Scalability analysis, persona system vision             |
| `docs/business/`       | Business context  | Capacity status, commercial planning                    |
| `docs/testbooks/`      | Test procedures   | Manual QA runbooks, test checklists                     |
| `docs/backups/`        | Safety snapshots  | Pre-migration backups                                   |

---

## Principles

1. **`git mv` always** — Never bare `mv`. Preserves history.
2. **Don't touch content** — This skill moves files, not edits them.
3. **24-hour cool-off** — Don't move files modified in the last 24 hours (might be in-flight).
4. **Approval before action** — Show the plan, get confirmation, then execute.
5. **Check cross-references** — After moves, grep for old paths that need updating.

---

## Anti-Patterns

- Moving files without checking cross-references
- Using `mv` instead of `git mv`
- Auto-executing without user approval
- Moving files modified in last 24 hours
- Deleting files instead of archiving
- Changing file content during moves
- Duplicating `/sync-docs` content alignment checks

---

## Skill Pipeline

```
/organize (monthly) — standalone maintenance
After organize: commit to save moves
Related: /sync-docs (content), /wow-audit (process), /hygiene (code)
```
