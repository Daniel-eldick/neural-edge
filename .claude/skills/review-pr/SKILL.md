---
name: review-pr
description: >-
  Reviews a PR from the main worktree (on develop): code diff analysis, CI
  verification, Vercel preview QA via Chrome DevTools MCP, risk assessment,
  merge with confirmation, worktree cleanup. The main worktree's single
  command for merging PRs to develop.
disable-model-invocation: true
allowed-tools: Read, Bash, Glob, Grep, TodoWrite, AskUserQuestion, Task,
  mcp__chrome-devtools__take_snapshot, mcp__chrome-devtools__take_screenshot,
  mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__click,
  mcp__chrome-devtools__fill, mcp__chrome-devtools__wait_for,
  mcp__chrome-devtools__list_console_messages,
  mcp__chrome-devtools__list_network_requests,
  mcp__chrome-devtools__emulate, mcp__chrome-devtools__evaluate_script,
  mcp__chrome-devtools__new_page
---

# Review PR Skill

The main worktree's single command for merging PRs to `develop`. Reviews a PR, verifies CI and preview, assesses risk, merges with confirmation, and cleans up the worktree.

**Context**: This skill runs from the **main worktree** (the "brain"), which lives on the `develop` branch. Feature worktrees (the "hands") handle implementation, testing, and pushing PRs targeting `develop`. This skill handles everything after the PR is opened. PRs targeting `main` are blocked — use `/release` to promote develop → main.

## When to Use

- `/review-pr`, `/review-pr 85`, `/review-pr feat/dark-mode`
- `/review-pr all` (batch mode — process all open PRs)
- After a feature worktree pushes a PR
- When ready to merge one or more PRs to develop

## When NOT to Use

- You're in a feature worktree (use `/code-review` and `/qa` there)
- No PR exists yet (push from the feature worktree first)
- Quick docs-only commit to develop (just commit directly — zero production risk)
- PR targets `main` (use `/release` to promote develop → main instead)

---

## Step 1: RESOLVE

Find the PR and load context.

```bash
# By number
gh pr view <number> --json title,author,files,commits,headRefName,url,state,isDraft

# By branch name
gh pr list --head <branch> --json number,title,headRefName,url,isDraft

# Auto-detect (no argument)
gh pr list --json number,title,headRefName,url,isDraft,createdAt --limit 10
```

**Draft PR check**: If `isDraft` is `true`, report "PR #X is a draft — skipping" and **STOP**. Do not review or merge draft PRs.

**Present**:

```
PR #85: feat/dark-mode — "Add dark mode toggle to admin"
Author: Daniel | Files: 12 | Commits: 3
Branch: feat/dark-mode → develop
```

### Base Branch Guard

```bash
gh pr view <number> --json baseRefName --jq '.baseRefName'
```

- **`develop`** → Continue (standard review)
- **`main`** → **STOP**: "PR #X targets `main`. PRs should target `develop`. Use `/release` to promote develop → main."

**Load diff for review**:

```bash
gh pr diff <number>
```

---

## Step 2: CODE REVIEW (lightweight)

This is a **second review** — the feature worktree already ran `/code-review`. Focus on integration concerns, not line-by-line analysis.

**Check for**:

1. **Sensitive files** — `.env`, `.key`, credentials, secrets in the diff (see `references/preserved-checks.md` for full patterns)
2. **DDD reconciliation**: If a `docs/active/*.md` plan exists for this feature (check WORKTREE.md progress log or match by branch/feature name):
   - Read the plan document
   - Check: are all task checkboxes complete (`[x]`)?
   - If 100% complete: update status to `✅ COMPLETE`, move to `docs/completed/`, update cross-references
   - If not complete: note remaining tasks in the PR summary, flag to CEO
   - If no plan exists: skip (not all work requires DDD)
3. **Verification language** — diff contains "should work", "probably passes", "seems fine" → flag
4. **Spec compliance** — changes match the planning doc intent
5. **Scale concerns** — anything that won't work at 10x load
6. **Landmine scan** (High-risk PRs only) — read `.claude/landmines.md`, cross-check relevant patterns against the diff. This is the safety net if `/code-review` was skipped in the feature worktree. Report any matches as findings.

**If issues found**: Report them and ask whether to proceed or stop.

---

## Step 3: CI GATE

All CI checks must pass before proceeding.

```bash
gh pr checks <number>
```

- **All pass**: Continue to Step 4
- **Running**: Poll every 30 seconds, max 10 minutes
  ```bash
  # Poll loop
  gh pr checks <number> --watch
  ```
- **Failed**: **STOP**. Report which check failed. Do not proceed.

---

## Step 4: PREVIEW QA (via Chrome DevTools MCP)

### Resolve Preview URL

```bash
# FILL: Replace the grep pattern with your CI/CD preview URL pattern
# Example (Vercel): grep -o 'https://your-project[^ )]*vercel.app[^ )]*'
# Example (Netlify): grep -o 'https://deploy-preview-[0-9]*--your-site.netlify.app'
gh pr view <number> --json comments --jq '.comments[].body' | grep -o 'PREVIEW_URL_PATTERN' | head -1
```

**If your preview deploys require auth bypass** (e.g., Vercel Deployment Protection):

```
# FILL: Add your bypass token if applicable
<preview-url>?x-vercel-protection-bypass=YOUR_TOKEN&x-vercel-set-bypass-cookie=samesitenone
```

For Vercel: the `x-vercel-set-bypass-cookie=samesitenone` param is critical — without it, sub-resources (JS/CSS) get 401s.

### Tiered Verification

**Quick tier** (docs, CSS, config, < 5 files):

1. Navigate to preview URL
2. Take snapshot
3. Check console — must be zero errors (filter known noise)
4. Check network — no 4xx/5xx on app requests

**Full tier** (UI changes, hooks, DB/auth, > 5 files):

1. All Quick checks, plus:
2. Test the specific feature flow described in the PR
3. Navigate affected pages
4. Verify dark mode if admin components changed

**Known noise filter**: See `references/preserved-checks.md` for the full list (analytics SDK, service worker, browser extensions, favicon).

**Console errors must be zero** after filtering known noise. Network 4xx/5xx on app requests is a **STOP**.

---

## Step 5: SUMMARY + RISK

### Migration Auto-Detection

Before classifying risk, check for database changes:

```bash
# Check if PR includes database migrations
gh pr diff <number> | grep '^+++ b/database/migrations/' && echo "DB_MIGRATION=true"
```

If migrations are detected: **force risk to High** regardless of file count, and add "Database changes: Yes" to the summary.

### Present Deployment Summary

```
## Deployment Summary

| Field            | Value                    |
|------------------|--------------------------|
| PR               | #85 — Add dark mode      |
| Files changed    | 12                       |
| Risk             | Medium (UI + hooks)      |
| Database changes | No                       |
| CI               | All checks passed        |
| Preview QA       | Clean (0 errors)         |
| Commits          | 3                        |

### Risk Classification

| Level  | Criteria                                                    |
|--------|-------------------------------------------------------------|
| Low    | Docs, CSS, config, skill/rule files, < 5 files, no src/    |
| Medium | UI components, hooks, API integration                       |
| High   | DB/RLS, auth, offline sync, service worker (auto-detected)  |
```

---

## Step 6: MERGE (tiered approval)

### 6a. Merge Conflict Check

Before attempting to merge, verify the PR is mergeable:

```bash
gh pr view <number> --json mergeable --jq '.mergeable'
```

- **`MERGEABLE`**: Proceed to 6b.
- **`CONFLICTING`**: **STOP**. Report "PR has merge conflicts. Rebase or resolve conflicts in the feature worktree before merging."
- **`UNKNOWN`**: Wait 30 seconds and retry once. If still `UNKNOWN`, warn and proceed (GitHub may be computing).

### 6b. Tiered Approval

Merge authorization depends on risk level. This replaces the blanket "wait for trigger phrase" model.

**Low risk** (docs, CSS, config, skill/rule files, Dependabot patches — see Low-Risk Criteria below):

- **Auto-merge**. No approval needed.
- Notify CEO after merge:
  ```
  Auto-merged PR #86 — "Fix README typo" (Low risk, CI clean, preview clean)
  Files: 1 | Commits: 1 | Strategy: squash
  ```

**Medium risk** (UI components, hooks, API integration):

- Show deployment summary (Step 5).
- Wait for CEO approval — any affirmative ("go ahead", "merge it", "looks good", "ok").

**High risk** (DB/RLS, auth, offline sync, service worker):

- Show deployment summary + risk details.
- Wait for explicit trigger phrase: "merge it" / "ship it" / "deploy" / "merge to main".
- **NEVER merge on**: silence, ambiguous approval.

### Low-Risk Criteria (ALL must be true for auto-merge)

1. Files changed are exclusively: `.md`, `.css`, `.json` (config), skill files (`.claude/`), rule files
2. No files in `src/`, database migrations dir, `public/sw.js`, `.github/workflows/`
3. Less than 5 files changed
4. No behavior change (no TypeScript/JavaScript modifications)
5. CI passes AND preview QA clean
6. PR is not a draft

**Dependabot**: Auto-merge if CI passes AND not a major version bump. Major bumps = Medium risk.

### 6c. Execute Merge

**Standard merge** (single PR):

```bash
# Squash: Dependabot PRs, OR single commit with <= 3 files
gh pr merge <number> --squash --delete-branch

# Merge commit: multi-commit feature branches (preserve commit history)
gh pr merge <number> --merge --delete-branch
```

`--delete-branch` handles both local and remote branch deletion.

**Local merge** (batched PRs — 2+ approved PRs from same base):

When processing multiple approved PRs in batch mode, prefer local merge to avoid squash-merge SHA drift:

```bash
# Merge locally (preserves branch context, avoids SHA conflicts between PRs)
git checkout develop && git pull origin develop
git merge --no-ff <branch-1>
git merge --no-ff <branch-2>
# ... repeat for each approved PR
git push origin develop
```

**When to use local merge**: 2+ PRs are all approved, CI-green, and preview-clean. Sequential GitHub merges would cause each subsequent PR's base to go stale (squash-merge creates new SHAs). Local merge avoids this entirely. (Postmortem: March 24, 2026)

**After local merge**: Delete branches manually:

```bash
git branch -d <branch>
git push origin --delete <branch>
```

---

## Step 7: CLEANUP

After merge, clean up and verify production.

### 7a. Worktree Cleanup

```bash
# Check if branch has a worktree
git worktree list | grep <branch-name>

# If worktree exists: remove it
git worktree remove ../<Project>-<name>
```

Note: `--delete-branch` in Step 6c already deleted the local and remote branch. No separate branch cleanup needed.

### 7b. Pull Latest

```bash
git pull origin develop
```

### 7c. Wait for Vercel Deploy

Vercel needs 30-90 seconds to deploy after merge. Poll before health check:

```bash
# Check Vercel deployment status (repeat every 30s, max 3 minutes)
gh api repos/{owner}/{repo}/deployments --jq '.[0] | {state: .state, environment: .environment, created_at: .created_at}' 2>/dev/null
```

- **State = `success`**: Proceed to health check.
- **State = `pending`/`in_progress`**: Wait 30 seconds, retry. Max 6 retries (3 minutes).
- **Timeout (3 minutes)**: Warn CEO "Vercel deploy may still be in progress — health check results could reflect the previous deployment." Proceed with health check anyway.

### 7d. Post-Merge Health Check

Quick production verification:

1. Navigate to `https://your-app.example.com/` via Chrome DevTools MCP
2. Take snapshot
3. Check console for errors (apply noise filter from `references/preserved-checks.md`)
4. Check network for 4xx/5xx on app requests
5. Report: clean or issues found

### 7e. Rollback (if health check fails)

If the health check finds console errors (after noise filter) or failed network requests:

**For Medium/High risk PRs** (CEO-approved merge):

- Report the errors with evidence (console messages, network failures)
- Offer: "Production errors detected after merge. Recommend reverting: `git revert HEAD --no-edit && git push origin main`"
- Wait for CEO confirmation before executing the revert

**For Low risk PRs** (auto-merged):

- Auto-revert without asking (the auto-merge trust implies auto-revert trust)
- Report: "Auto-reverted PR #86 — console errors detected post-deploy. Errors: [details]"

**After any revert**: Recommend `/prod-audit` for deeper investigation.

---

## Batch Mode: `/review-pr all`

Process all open PRs sequentially in risk order.

### Flow

1. **List all open PRs with status** (exclude drafts):

   ```bash
   gh pr list --json number,title,headRefName,labels,additions,deletions,files,isDraft --limit 20
   ```

   Filter out PRs where `isDraft` is `true` before building the triage table.

2. **Classify risk** for each PR (Low → Medium → High). Check for `database/migrations/` in diff to auto-escalate.

3. **Present triage table**:

   ```
   | #  | PR                    | Risk   | CI     | Action      |
   |----|-----------------------|--------|--------|-------------|
   | 1  | #86 — Fix typo        | Low    | Pass   | Auto-merge  |
   | 2  | #85 — Dark mode       | Medium | Pass   | Review      |
   | 3  | #84 — RLS update      | High   | Pass   | Review      |
   | —  | #83 — WIP feature     | —      | —      | Draft (skip)|
   ```

4. **Process each PR** through Steps 1-7

5. **Between merges**: Check main CI before proceeding

   ```bash
   gh run list --branch main --limit 1 --json status,conclusion
   ```

   If main CI fails: **STOP**. Report. Do not continue.

6. **Dependabot PRs**: If a Dependabot PR has conflicts, comment `@dependabot rebase` instead of merging.

7. **Summary after all merges**:

   ```
   ## Merge Session Summary

   | PR  | Result  | Risk   |
   |-----|---------|--------|
   | #86 | Merged  | Low    |
   | #85 | Merged  | Medium |
   | #84 | Skipped | High (CI failed) |

   Main branch: X commits ahead. Production deploying.
   ```

---

## Principles

1. **Risk-proportionate approval** — Low risk auto-merges. Medium needs CEO approval. High needs explicit trigger phrase. Safety scales with risk.
2. **CI must pass** — Failed CI is an absolute stop. No "it's probably fine".
3. **Preview must be clean** — Zero console errors after noise filter. No "it was there before".
4. **Risk-proportionate review** — Low-risk PRs get Quick QA. High-risk get Full QA + landmine scan.
5. **One at a time** (batch mode) — Merge, verify main CI, then next PR.
6. **Clean up after yourself** — Worktree removal is part of the merge, not a separate step.
7. **Rollback is part of shipping** — If post-merge health check fails, revert immediately. Don't hope it fixes itself.

---

## Skill Pipeline

```
FEATURE WORKTREE: implement → /code-review → /qa → commit → push → open PR (→ develop)
                                                                        ↓
MAIN WORKTREE (develop):                                    /review-pr (you are here)
                                                                        ↓
                                                              merge to develop → cleanup
                                                                        ↓
                                                              /release → promote to main (production)
```

**Periodic**: `/review-pr all` when multiple PRs accumulate.
**Related**: `/prod-audit` (deeper post-merge health check), `/worktree` (workspace management).
