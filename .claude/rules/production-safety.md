---
description: Production deployment safety protocol
alwaysApply: false
---

# Production Safety Protocol - CRITICAL

**User Mandate**: _"Never push to main without my confirmation... pushing affects users in production."_

**Background**: CI/CD auto-deploys from `main` (production) and `develop` (staging). The `develop` branch is the home base — all work flows through develop first. `main` is production-only, promoted from develop via `/release` when the CEO says "ship it."

## The Two-Layer Model

```
┌─────────────────────────────────────────────────────────┐
│  DEVELOP (staging — the kitchen)                        │
│  Feature branches → PR → CI → preview → merge          │
│  CEO tests on staging before promoting                  │
│                                                         │
│  MAIN (production — the pass)                           │
│  Only updated via /release (CEO says "ship it")         │
│  No direct pushes. No PRs targeting main. Period.       │
└─────────────────────────────────────────────────────────┘
```

## Workflow

### In Feature Worktrees (hands — build, test, push)

1. **Branch from `develop`** — via `/worktree create` (forks from `origin/develop`)
2. **Commit to feature branch** — Safe, doesn't affect staging or production
3. **Push branch and open PR targeting `develop`** — Triggers CI + preview deploy

### In Main Worktree (brain — review, merge, release)

4. **Run `/review-pr`** — Reviews PR diff, verifies CI, tests preview, assesses risk
5. **Merge to `develop`** — Tiered approval:

   **Low risk** (docs, CSS, config, skills — no source code, no DB, < 5 files):
   - Auto-merge if CI passes AND preview QA is clean
   - Notify CEO after merge

   **Medium risk** (UI components, hooks, API integration):
   - Show deployment summary
   - Wait for CEO approval (any affirmative: "go ahead", "merge it", "ok")

   **High risk** (DB, auth, critical system components):
   - Show deployment summary + risk details
   - Wait for explicit trigger phrase: "merge it" / "ship it" / "deploy"
   - **NEVER merge on**: silence, ambiguous approval

6. **CEO tests on staging** — staging environment (CI/CD deploys from `develop`)
7. **Run `/release`** — Promotes develop → main when CEO says "ship it" / "release it"
8. **Post-release** — Health check, auto-revert if errors detected

## Local Merge for Batched PRs

When merging 2+ approved PRs in a batch, prefer local merge + single push to develop:

```bash
git checkout develop && git pull origin develop
git merge --no-ff feat/branch-1
git merge --no-ff feat/branch-2
git push origin develop
```

**Why**: Sequential squash-merges can cause overhead. Local merge eliminates this.

## Risk Assessment Guidelines

| Risk Level | Criteria                                          | Examples                                    |
| ---------- | ------------------------------------------------- | ------------------------------------------- |
| **Low**    | UI-only, no data changes, well-tested             | CSS fixes, copy changes, new read-only page |
| **Medium** | New features, API changes, logic changes          | New dashboard, form validation, hooks       |
| **High**   | Database migrations, auth changes, critical infra | Schema changes, security policies, sync     |

## What I Will Do

- Commit frequently (to feature branches)
- Push branches and open PRs targeting `develop`
- Test on preview deployments
- Classify risk and apply tiered merge authorization for PRs → develop
- Auto-merge Low-risk PRs when CI + preview pass
- Show summary and wait for approval on Medium-risk PRs
- Show summary and wait for trigger phrase on High-risk PRs
- **NEVER** push directly to `main` (only `/release` can promote develop → main)
- **NEVER** open PRs targeting `main` (use `/release` instead)
- **NEVER** assume silence means approval (Medium/High risk)
- **NEVER** auto-merge anything that touches source code or database schemas

## Hotfix Path (Emergency Only)

For production-critical fixes that can't wait for the normal develop → staging → release flow:

1. Fork from `main` (not develop)
2. Fix, test, PR targeting `main`
3. CEO approves with explicit trigger phrase
4. After merge to main: cherry-pick or merge the fix into `develop` too
