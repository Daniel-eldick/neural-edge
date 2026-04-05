# Preserved Checks Reference

Detailed reference for checks absorbed from killed skills (`/commit`, `/pre-deploy`, `/deploy`, `/merge`). This file supports progressive disclosure — the main SKILL.md references it, implementors dig in here.

---

## Console Noise Filter

Known noise sources to exclude when checking for console errors on preview and production:

| Source             | Pattern                                   | Why It's Noise                         |
| ------------------ | ----------------------------------------- | -------------------------------------- |
| <!-- FILL: your analytics tool --> | Analytics SDK URL or message patterns | Analytics SDK, non-critical            |
| Service Worker     | `SW`, `service-worker`, `workbox`         | Registration/update lifecycle messages |
| Browser Extensions | `chrome-extension://`, `moz-extension://` | Not our code                           |
| Favicon            | `favicon.ico` 404                         | Missing favicon on preview deploys     |
| React DevTools     | `Download the React DevTools`             | Development hint, not an error         |
| Vite HMR           | `[vite]`, `hmr`                           | Dev server only, never in production   |
| ResizeObserver     | `ResizeObserver loop`                     | Browser quirk, not actionable          |

**Rule**: After filtering these, console errors must be **zero**. Any remaining error is a real issue.

---

## Network Failure Filter

| Status      | Path Pattern                                  | Action                          |
| ----------- | --------------------------------------------- | ------------------------------- |
| 4xx/5xx     | your backend API paths | **STOP** — backend API failure |
| 4xx/5xx     | App routes (`/menu`, `/admin/*`)   | **STOP** — Page load failure    |
| 404         | `favicon.ico`, `apple-touch-icon.png`         | Ignore — cosmetic               |
| 401         | `_vercel/insights/*`                          | Ignore — Vercel analytics auth  |
| ERR_BLOCKED | Any `chrome-extension://`                     | Ignore — browser extension      |

---

## Sensitive File Detection

Flag if any of these appear in the PR diff:

| Pattern                                    | Risk                            |
| ------------------------------------------ | ------------------------------- |
| `.env`, `.env.*`                           | Credentials exposure            |
| `*.key`, `*.pem`, `*.p12`                  | Private keys                    |
| `credentials.json`, `service-account.json` | Service credentials             |
| `*secret*`, `*password*` in filenames      | Potential secrets               |
| `SERVICE_ROLE_KEY` in code        | Service role key (never commit) |

**Action**: If detected, **STOP** and warn. Never merge a PR containing secrets.

---

## Verification Language Detection

Scan the PR diff for hedging language that indicates insufficient testing:

| Forbidden Phrase       | Replacement                              |
| ---------------------- | ---------------------------------------- |
| "should work"          | "I ran [command] and the output was [X]" |
| "probably passes"      | "Test [name] passes with assertion [Y]"  |
| "looks correct"        | "I traced [rule] through [file:line]"    |
| "seems fine"           | "MCP query returned [Z]"                 |
| "I believe this works" | "[specific evidence]"                    |

**Action**: Flag in code review (Step 2). Not a hard stop — but worth noting.

---

## DDD Archival Check

Before merging, verify:

1. **No COMPLETE files in `docs/active/`** — If a planning doc is marked `COMPLETE` or `100%`, it must be in `docs/completed/` before merge.
2. **Cross-references updated** — If a doc was moved, grep for old paths.

```bash
# Check for COMPLETE files still in active/
grep -rl "COMPLETE\|100%" docs/active/ 2>/dev/null
```

**Action**: If found, the feature worktree missed the archival step. Fix before merge or flag to the user.

---

## Risk Classification

| Level      | Criteria                                               | QA Tier               |
| ---------- | ------------------------------------------------------ | --------------------- |
| **Low**    | Docs, CSS, config, copy, < 5 files, no behavior change | Quick                 |
| **Medium** | UI components, hooks, API integration, 5-15 files      | Full                  |
| **High**   | DB/RLS, auth, offline sync, service worker, > 15 files | Full + extra scrutiny |

---

## Dependabot Handling

Dependabot PRs get special treatment in batch mode:

1. **Clean merge**: If CI passes and no conflicts, merge normally
2. **Conflicts**: Comment `@dependabot rebase` instead of manual rebase
   ```bash
   gh pr comment <number> --body "@dependabot rebase"
   ```
3. **Major version bumps**: Review changelog before merging (treat as Medium risk)
4. **Security patches**: Prioritize — merge first in batch sequence

---

## Squash vs Merge Commit

| Condition                                            | Strategy     | Command                                |
| ---------------------------------------------------- | ------------ | -------------------------------------- |
| Dependabot (always)                                  | Squash       | `gh pr merge --squash --delete-branch` |
| Single commit with <= 3 files (small logical change) | Squash       | `gh pr merge --squash --delete-branch` |
| Multi-commit feature branches (preserve history)     | Merge commit | `gh pr merge --merge --delete-branch`  |

Default is merge commit. Squash keeps history clean for small changes. `--delete-branch` handles both local and remote branch cleanup.
