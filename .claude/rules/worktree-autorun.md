---
description: Detects WORKTREE.md execution manifests in feature worktrees and drives autopilot execution
alwaysApply: true
---

# Worktree Autopilot

If `WORKTREE.md` exists at the repo root, you are in a feature worktree with an execution manifest.

## On Session Start (automatic)

1. Read `WORKTREE.md` immediately
2. Check the Task Manifest — identify the next incomplete task (first `[ ]`)
3. Check the Progress Log — understand what the previous session accomplished
4. Resume execution from where the previous session left off
5. Follow the Execution Protocol defined in the manifest

## Execution Rules

- Follow the pipeline EXACTLY as written in WORKTREE.md
- Run quality gates per-task (`npm run quality:check` + `/code-review`)
- Run targeted E2E (Playwright CLI, Chromium only) after ALL tasks complete
- Commit after each task passes quality gates (conventional format)
- Update WORKTREE.md after each task: mark `[x]`, add commit hash, append to Progress Log
- **Plan doc awareness**: After each task commit, check if a corresponding `docs/active/*.md` plan exists for this feature (match by branch name or feature name in WORKTREE.md header). If found, note the plan doc path in the WORKTREE.md Progress Log so `/review-pr` can reconcile at merge time. Direct editing of plan docs from feature worktrees is optional — the merge-time DDD reconciliation in `/review-pr` is the safety net.
- STOP and notify CEO on: 3 failed `/code-review` iterations, any blocker, unclear requirements, or circuit breaker trigger
- Never skip `/code-review` — it's the safety net for autopilot
- Never modify WORKTREE.md's Execution Protocol section — only update Task Manifest status and Progress Log

## When WORKTREE.md Does NOT Exist

Normal behavior. You're in the main worktree (or a worktree without a manifest). Follow standard `/session-start` flow.
