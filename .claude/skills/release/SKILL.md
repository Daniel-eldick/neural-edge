---
name: release
description: >-
  Promote develop → main (production). 7-step flow with CEO gate, CI pre-check,
  local merge, post-deploy health check, and auto-revert on failure.
allowed-tools: Bash, Read, Glob, Grep, AskUserQuestion, WebFetch
---

# Release Skill

Promote `develop` → `main` (production). The CEO's "ship it" button. Only way code reaches production.

**Context**: This skill runs from the **main worktree** (on the `develop` branch). It's the single gate between staging and production. Think of it as the pass — only complete plates go to customers.

## When to Use

- `/release` — ready to push staging to production
- "release this", "push to production", "promote to main"

## When NOT to Use

- You're on a feature branch (use `/deploy` from develop, or push the branch directly)
- You want to push to staging (use `/deploy`)
- You want to merge a PR (use `/review-pr`)
- Develop has no commits ahead of main (nothing to release)

---

## Step 1: GUARDS

### Guard 1: On develop branch?

```bash
git branch --show-current
```

- **Not develop** → Exit: "You're on branch `X`. `/release` only works from `develop`."

### Guard 2: Develop ahead of main?

```bash
git fetch origin main
git log origin/main..origin/develop --oneline
```

- **No output** → Exit: "Nothing to release. `develop` and `main` are at the same point."
- **Has commits** → Continue. Save the count and list.

---

## Step 2: CI PRE-CHECK

Verify CI passes on the latest `develop` commit before proceeding.

```bash
gh run list --branch develop --limit 5 --json status,conclusion,headBranch,event,name
```

- **Latest run passed** → Continue
- **Latest run failed** → **STOP**: "CI is failing on develop. Fix before releasing."
- **No runs found** → Warn: "No CI runs found for develop. Consider pushing to trigger CI first."

---

## Step 3: DIFF SUMMARY

Show what's being promoted.

```bash
# Commit list
git log origin/main..origin/develop --oneline

# File summary
git diff origin/main..origin/develop --stat
```

Present:

```
## Release Summary

Commits: N commits from develop → main

[commit list]

Files changed: M files
[stat summary]
```

---

## Step 4: RISK CLASSIFICATION

Classify based on file types in the diff.

```bash
git diff --name-only origin/main..origin/develop
```

| Level      | Criteria                                               |
| ---------- | ------------------------------------------------------ |
| **Low**    | Only docs, config, skills, CSS, `.md` files            |
| **Medium** | UI components, hooks, API integration, tests           |
| **High**   | DB migrations, RLS, auth, offline sync, service worker |

Check for database migrations specifically:

```bash
git diff --name-only origin/main..origin/develop | grep '^database/migrations/' && echo "DB_MIGRATION=true"
```

If migrations detected → force High risk.

---

## Step 5: CEO GATE

Present the full summary and wait for explicit approval.

```
## Ready to Release

| Field       | Value                              |
|-------------|------------------------------------|
| Commits     | N from develop → main              |
| Files       | M changed                          |
| Risk        | Low / Medium / High                |
| DB changes  | Yes / No                           |
| CI          | Passed on develop                  |

**This will deploy to production immediately.**

Say "ship it", "release it", or "push to production" to proceed.
```

**NEVER release on**: silence, ambiguous approval, "ok" without context. Only explicit release phrases.

---

## Step 6: EXECUTE

Local merge from develop into main. NOT a PR — direct promotion.

```bash
# 1. Switch to main and update
git checkout main && git pull origin main

# 2. Merge develop into main (no-ff preserves branch history)
git merge --no-ff develop -m "release: promote develop to main"

# 3. Push to main (triggers Vercel production deploy)
git push origin main

# 4. Return to develop
git checkout develop
```

**Important**: Step 3 (`git push origin main`) is blocked by the hook. `/release` uses a marker file to bypass — the ONLY authorized path to main.

**Hook bypass**: Each step MUST be a separate Bash tool call (hook intercepts before execution).

```bash
# Step A (separate tool call): Create release marker
touch /tmp/.claude-release-push
```

```bash
# Step B (separate tool call): Push to main — hook sees marker, allows it
git push origin main
```

```bash
# Step C (separate tool call): Clean up marker (belt and suspenders)
rm -f /tmp/.claude-release-push
```

**Security properties**:

- Marker is in `/tmp/` — cleared on reboot
- Single-use — hook deletes it on first check
- Only bypasses push-to-main — force push, reset --hard, clean -f still blocked
- Only created by `/release` after CEO explicitly says "ship it"

---

## Step 7: POST-DEPLOY

### Wait for Vercel

```bash
# Wait 60 seconds for Vercel to deploy
sleep 60

# Check deployment status
gh api repos/{owner}/{repo}/deployments --jq '.[0] | {state: .state, environment: .environment, created_at: .created_at}' 2>/dev/null
```

### Health Check

Via Chrome DevTools MCP:

1. Navigate to `https://your-app.example.com/`
2. Take snapshot
3. Check console for errors (filter known noise from `references/preserved-checks.md`)
4. Check network for 4xx/5xx on app requests

### On Success

```
Released N commits to production. Vercel deployed successfully.
Health check: Clean (0 errors).
```

### On Failure (console errors or network failures)

```
Production errors detected after release!

Errors:
- [error details]

Recommending revert. Say "revert" to undo.
```

If CEO says "revert":

```bash
git checkout main && git pull origin main
git revert HEAD --no-edit
git push origin main
git checkout develop
```

Report: "Reverted release. Production restored to previous state."

---

## Edge Cases

| Edge Case                 | Behavior                                              |
| ------------------------- | ----------------------------------------------------- |
| Develop behind main       | Exit: "Develop is behind main. Run `git pull` first." |
| CI not run on develop     | Warn, but don't block (CEO decides)                   |
| Merge conflicts           | **STOP**: "Merge conflict. Resolve on develop first." |
| Hook blocks push          | Expected — use release marker bypass                  |
| Vercel deploy timeout     | Warn, proceed with health check                       |
| Health check finds errors | Report + offer revert. CEO decides.                   |
| On feature branch         | Exit: "Switch to develop first."                      |

---

## Principles

1. **CEO gate is non-negotiable** — No release without explicit "ship it" / "release it" / "push to production".
2. **Local merge, not PR** — Direct promotion preserves the clean develop→main flow.
3. **Health check is mandatory** — Every release gets a post-deploy verification.
4. **Revert is always available** — If production breaks, one command to undo.
5. **Only way to main** — No other skill or workflow can push to main. Period.
6. **CI must pass first** — Don't release broken code, even with CEO approval.

---

## Skill Pipeline

```
/deploy → push to develop (staging)
              ↓
        CEO tests on staging.example.com
              ↓
        /release (you are here) → promote to main (production)
              ↓
        health check → clean? → done
                     → errors? → revert
```

**Upstream**: `/deploy` (pushes to develop/staging)
**Downstream**: `/prod-audit` (deeper post-release health check if needed)
