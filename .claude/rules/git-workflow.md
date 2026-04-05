---
description: Git workflow and commit conventions
globs:
  - '.git/**'
  - '.gitignore'
---

# Git Workflow - MANDATORY

**User Mandate**: _"Frequent commits to GitHub are always encouraged"_

## Key Principles

- Commit after each TodoWrite task completion
- Use Conventional Commits: `<type>(<scope>): <description>`
- Always run `npm run test:all` before committing
- Zero warnings policy (ESLint + TypeScript)

## Commit Types

| Type       | Description                         |
| ---------- | ----------------------------------- |
| `feat`     | New feature                         |
| `fix`      | Bug fix                             |
| `docs`     | Documentation only                  |
| `chore`    | Build/tooling changes               |
| `refactor` | Code change without behavior change |
| `test`     | Adding/updating tests               |
| `perf`     | Performance improvement             |

## Commit Message Format

```
<type>(<scope>): <short description>

<optional body with more details>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## Pre-Commit Checklist

1. Run `npm run test:all` (lint + unit + E2E)
2. Fix any ESLint warnings (zero tolerance)
3. Fix any TypeScript errors
4. Stage related files only
5. Write descriptive commit message

## Branch & PR Convention

- Features fork from `develop` (via `/worktree create` → `origin/develop`)
- Branch naming: `<type>/<short-description>` (e.g., `feat/dark-mode`, `fix/sync-retry`)
- PRs target `develop` (never `main` — use `/release` for that)
- Use git worktrees for parallel feature work (`/worktree create`)
- Push branch and open PR → triggers CI + Vercel preview deploy
- Merge handled by `/review-pr` in the main worktree (which lives on `develop`)

## Worktree Commit Guidance

- In feature worktrees: commit naturally using conventional format above
- No special skill needed — git-workflow rules handle format enforcement
- After `/qa` passes: commit, push, create PR targeting `develop`
- Merging to develop is the main worktree's responsibility (via `/review-pr`)
- Promoting develop → main is via `/release` only

## Hotfix Path (Emergency Only)

For production-critical fixes that can't wait for the develop → staging → release flow:

1. Fork from `main` (not develop)
2. Fix, test, PR targeting `main`
3. CEO approves with explicit trigger phrase
4. After merge to main: cherry-pick or merge the fix into `develop` too

## Branch Lifecycle — Tiered Policy

**Why**: A branch is a 41-byte pointer, not the work itself. After merge, commits live permanently in the target branch history. The PR page (diff, comments, CI results) is the real archive. GitHub offers one-click "Restore Branch" on any merged PR — indefinitely.

### Tier 1: Auto-Delete After Merge (default)

- GitHub repo setting "Automatically delete head branches" is **ON**
- After a PR merges to `develop` or `main`, the source branch is auto-deleted
- **No work is lost** — commits are in the merge target, PR is the permanent record
- This is what Google, GitHub, GitLab, and Atlassian all recommend

### Tier 2: Tag-Archive Before Deleting (unmerged but interesting)

For branches with unmerged work worth preserving as reference:

```bash
git tag archive/<branch-name> <branch-name>
git push origin archive/<branch-name>
# Branch can then be safely deleted — the tag preserves the exact snapshot
```

- Tags are immutable (can't be accidentally moved like branches)
- Tags signal "this is historical reference, not active work"
- Tags don't trigger CI scans or clutter branch lists

### Tier 3: Keep (active unmerged work)

- Branches with unshipped work that may be cherry-picked or revived stay as branches
- Review quarterly — if still unmerged after 6 months, graduate to Tier 2 (tag-archive)

### What NEVER changes

- **NEVER delete `develop` or `main`** — these are permanent
- **NEVER force-push to `develop` or `main`** — rewrite history = lost work for real
- Commits are the source of truth, not branch names

## Merge Protocol

See production-safety.md rule for merge restrictions.

**Remember**: Commits to feature branches are safe. Merging to `develop` deploys to staging. Only `/release` promotes to production (`main`).
