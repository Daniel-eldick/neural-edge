---
name: deploy
description: >-
  Push commits from develop to origin. All files go directly — develop IS the
  staging area. No risk classification needed.
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion
---

# Deploy Skill

Push commits from `develop` to origin. All files go directly — `develop` IS the staging area where the CEO tests on multiple devices before promoting to production via `/release`.

**Context**: This skill runs from the **main worktree** (which lives on the `develop` branch). It fills the gap between "commit" and testing on staging.

## When to Use

- `/deploy` — after committing on develop, ready to push to staging
- "ship this", "push this", "deploy these changes"

## When NOT to Use

- You're on a feature branch (just `git push origin <branch>`)
- No commits exist yet (commit first)
- You want to promote develop → main (use `/release`)
- You want to merge a PR (use `/review-pr`)

---

## Step 1: GUARDS

### Guard 1: On develop branch?

```bash
git branch --show-current
```

- **Not develop** → Exit: "You're on branch `X`. `/deploy` only works on `develop`. Use `git push origin X` for feature branches, or `/release` for develop → main."

### Guard 2: Unpushed commits exist?

```bash
git log origin/develop..HEAD --oneline
```

- **No output** → Exit: "Nothing to deploy. All commits are already pushed."
- **Has commits** → Continue. Save the count as `N`.

---

## Step 2: PUSH

### Present

```
Pushing N commit(s) to develop → staging deploys automatically.

Files:
- [list changed files from git diff --name-only origin/develop..HEAD]
```

### Execute

```bash
git push origin develop
```

### Report

```
Pushed N commit(s) to develop. Staging deploying at staging.example.com.
```

---

## Edge Cases

| Edge Case             | Behavior                                            |
| --------------------- | --------------------------------------------------- |
| On feature branch     | Exit: "Push normally or use `/release`."            |
| On main branch        | Exit: "Switch to develop. Main is production-only." |
| No unpushed commits   | Exit: "Nothing to deploy."                          |
| Remote ahead of local | `git push` will fail naturally — user needs to pull |

---

## Principles

1. **Zero git knowledge required** — User commits, runs `/deploy`, done.
2. **No risk classification** — Develop IS the staging area. Everything goes.
3. **Main worktree only** — Feature worktrees push branches directly.
4. **Never touches main** — Only `/release` can promote develop → main.

---

## Skill Pipeline

```
commit → /deploy → push to develop (staging)
                         ↓
                   CEO tests on staging.example.com
                         ↓
                   /release → promote to main (production)
```

**Upstream**: Commit on develop (the trigger)
**Downstream**: `/release` (when CEO is ready to promote to production)
