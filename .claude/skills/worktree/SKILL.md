---
name: worktree
description: Parallel feature workspaces using git worktrees. Create, list, sync, and remove workspaces. Use when the user wants to work on multiple features simultaneously.
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# Worktree Skill

Manage parallel feature workspaces using git worktrees. The user thinks in **features, not branches** — resolve their intent to git operations invisibly.

## When to Use

- `/worktree`, "I want to work on X", "set up a workspace for X"
- "What am I working on?", "show my workspaces"
- "Sync everything with main"
- "X is merged, clean it up"

## When NOT to Use

- Single-feature work (no parallelism needed)
- User explicitly wants to switch branches in-place

---

## Operations

### 1. Create — "I want to work on X"

The user names a feature. You resolve it to a branch and set up a full workspace.

**Steps:**

1. **Pre-flight: fetch latest develop** (MANDATORY):

   ```bash
   git fetch origin develop
   ```

2. **Resolve feature to branch**:

   ```bash
   git branch -a | grep -i "<feature-keywords>"
   ```

   - **One match**: Use it
   - **Multiple matches**: Present picker via `AskUserQuestion` with matching branches + "Create new branch from develop" option
   - **No match**: Create new branch from `origin/develop`: `feat/<feature-name-kebab>`

3. **Derive folder name** from branch:
   - Strip prefix (`feat/`, `fix/`, `chore/`)
   - Take first 2-3 segments
   - Prefix with repo name: `../<Project>-<name>/`
   - Examples: `feat/demo-sandbox-merge` → `../<Project>-demo-sandbox/`, `fix/sync-retry` → `../<Project>-sync-retry/`

4. **Create worktree** (ALWAYS from `origin/develop` for new branches):

   ```bash
   # New branch: fork from origin/develop, NOT HEAD
   git worktree add -b <branch> ../<Project>-<name> origin/develop

   # Existing branch: use the branch as-is
   git worktree add ../<Project>-<name> <branch>
   ```

   **WHY origin/develop**: HEAD accumulates locally-merged features. GitHub squash-merge creates new SHAs for those features, so stowaway commits on HEAD can't reconcile — causing merge conflicts on every PR. `origin/develop` is always the clean truth after squash-merges. (Postmortem: March 24, 2026)

5. **Copy dependencies (macOS CoW)**:

   ```bash
   cp -c -r node_modules ../<Project>-<name>/node_modules
   ```

   If `cp -c` fails, fall back to regular `cp -r`.

6. **Safety net** (catches package.json drift between branches):

   ```bash
   cd ../<Project>-<name> && npm install --prefer-offline --ignore-scripts
   ```

   Use `--ignore-scripts` because Husky's `prepare` script fails in worktrees (no `.git` directory). This is harmless — worktrees don't need their own git hooks.

7. **Assign port** — count existing worktrees, assign next:

   ```bash
   git worktree list | wc -l
   ```

   Main = 5173, 1st worktree = 5174, 2nd = 5175, 3rd = 5176.

8. **Open editor**:

   ```bash
   open -a "Antigravity" ../<Project>-<name>   # or: code ../<Project>-<name>
   ```

   Try `Antigravity` first (macOS `open -a`), fall back to `code` CLI.

9. **Report**:

   ```
   Setting up workspace...

   ✓ Created folder: ../<Project>-<name>/
   ✓ Branch: <branch-name>
   ✓ Dependencies installed
   ✓ VS Code opening...

   Dev server: npm run dev -- --port <port>

   ┌──────────────────────────────────────────┐
   │ Next: Open Claude Code in that window.   │
   │ Run /session-start to pick up where      │
   │ you left off on this feature.            │
   └──────────────────────────────────────────┘
   ```

---

### 2. List — "What am I working on?"

Show all active workspaces with branch, port, and PR status.

**Steps:**

1. **Get worktrees**:

   ```bash
   git worktree list
   ```

2. **Get open PRs** (for branch → PR mapping):

   ```bash
   gh pr list --json number,headRefName,url --limit 20
   ```

3. **Present table**:

   ```
   Active Workspaces
   ┌────────────────────┬──────────────────┬──────┬───────┐
   │ Workspace          │ Branch           │ Port │ PR    │
   ├────────────────────┼──────────────────┼──────┼───────┤
   │ ★ main (here)      │ main             │ 5173 │ —     │
   │ demo-sandbox       │ feat/demo-san... │ 5174 │ #68   │
   │ whatsapp-agent     │ feat/ai-agent... │ 5175 │ #63   │
   └────────────────────┴──────────────────┴──────┴───────┘
   ```

   - Mark current worktree with ★
   - Port assigned by position (5173 + index)
   - Show PR number if branch has an open PR, "—" otherwise

---

### 3. Sync — "Sync everything with develop"

Rebase all worktrees on latest origin/develop.

**Steps:**

1. **Fetch latest**:

   ```bash
   git fetch origin develop
   ```

2. **For each worktree** (skip develop):

   ```bash
   cd <worktree-path> && git rebase origin/develop
   ```

3. **Report per-worktree**:

   ```
   Syncing N workspaces with origin/develop...

   ✓ demo-sandbox — rebased, 0 conflicts
   ✓ whatsapp-agent — rebased, 0 conflicts

   All workspaces current.
   ```

   If conflicts:

   ```
   ✗ demo-sandbox — CONFLICTS in 2 files
     → cd ../<Project>-demo-sandbox/ to resolve
     → Then: git rebase --continue
   ```

   On conflict, abort the rebase to leave the worktree clean:

   ```bash
   git rebase --abort
   ```

   Then report the conflict and let the user resolve manually.

---

### 4. Remove — "X is merged, clean it up"

Clean up a workspace after its PR is merged.

**Steps:**

1. **Resolve feature to worktree** (same fuzzy match as Create)

2. **Safety check** — verify PR is merged:

   ```bash
   gh pr list --state merged --head <branch> --json number,mergedAt
   ```

   If NOT merged, warn:

   ```
   ⚠ PR for <branch> is not merged yet.
   Are you sure you want to remove this workspace?
   ```

   Use `AskUserQuestion` with "Yes, remove anyway" / "No, keep it".

3. **Remove worktree**:

   ```bash
   git worktree remove ../<Project>-<name>
   ```

4. **Optionally delete branch** (if merged):

   ```bash
   git branch -d <branch>
   ```

5. **Report**:

   ```
   ✓ PR #68 confirmed merged
   ✓ Removed ../<Project>-demo-sandbox/
   ✓ Deleted branch feat/demo-sandbox-merge

   N workspace(s) remaining.
   ```

---

## Conventions

| Convention        | Rule                                                                |
| ----------------- | ------------------------------------------------------------------- |
| Folder naming     | `../<Project>-<name>/` (sibling to main repo)                         |
| Port assignment   | 5173 (main) + worktree index                                        |
| Branch resolution | `git branch -a \| grep -i` with AskUserQuestion picker on ambiguity |
| Dependencies      | CoW copy (`cp -c -r`) + `npm install --prefer-offline` safety net   |
| Context recovery  | Existing `/session-start` + `docs/active/` planning docs per branch |

## Principles

1. **Feature-first language** — User says feature names, never branch names
2. **Git is invisible** — User never needs to know git commands
3. **Safe by default** — Warn before removing unmerged work
4. **Step-by-step feedback** — Checkmarks for every operation
5. **Leverage native tooling** — Claude Code `--worktree`, `--resume` handle session management

---

## Skill Pipeline

```
MAIN WORKTREE: /plan → /sign-off → /worktree create → ...
                                          ↓
FEATURE WORKTREE:              implement → /code-review → /qa → commit → push → PR
                                                                                 ↓
MAIN WORKTREE:                                                        /review-pr → cleanup
                                                                                     ↓
                                                                        /worktree remove (auto)
```

**Two removal contexts**:

- **Merged work**: `/review-pr` Step 7 automatically removes the worktree after merge
- **Abandoned work**: `/worktree remove` standalone — user decides to discard a feature branch
