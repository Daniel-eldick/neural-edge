# Incident Response Runbook

**Created**: <!-- FILL: Date -->
**Owner**: <!-- FILL: Name and role -->
**Applies to**: <!-- FILL: Production URL -->

---

## 1. Detection — How Do We Know?

<!-- FILL: Replace with your monitoring stack -->
| Signal | Source | Response Time |
| ------ | ------ | ------------- |
| Uptime monitor ping | <!-- FILL: e.g., BetterStack, Pingdom --> | X min |
| Error spike | <!-- FILL: e.g., Sentry, Datadog --> | Real-time |
| User reports issue | <!-- FILL: e.g., support channel --> | Minutes |
| Deploy fails | CI/CD notifications | Minutes |
| Backend outage | <!-- FILL: e.g., status page URL --> | Check manually |

---

## 2. Triage — What's Broken?

Run through this checklist top-to-bottom. Stop at the first match.

### Step 1: External services down?

<!-- FILL: Replace with your external dependencies -->
- [ ] **Backend provider**: Check status page
  - If degraded → nothing we can do. Skip to Section 4 (Communication).
- [ ] **Hosting provider**: Check status page
  - If degraded → nothing we can do. Skip to Section 4 (Communication).

### Step 2: Recent deploy broke something?

- [ ] Check deployment dashboard
  - Was there a deploy in the last hour?
  - Does the error correlate with the deploy time?
  - If yes → **Rollback** (Section 3, Option A)

### Step 3: Is it our code?

- [ ] Open production app in browser → DevTools Console
  - Red errors? Failed network requests?
  - Network tab: 4xx/5xx responses?
- [ ] Check backend logs
  - Auth errors? Permission violations? Function failures?
- [ ] `git log --oneline -10` — review recent changes

### Step 4: Is it isolated?

- [ ] Can other users/tenants work normally?
  - If only one is affected → check their config and data
  - Query the database to verify their state

### Step 5: Unknown

- [ ] Ask the reporter for a screenshot or screen recording
- [ ] Try reproducing on a different device/network
- [ ] Check if the issue is intermittent or consistent

---

## 3. Rollback — Fix It Fast

### Option A: Instant Rollback (fastest)

<!-- FILL: Replace with your hosting provider's rollback procedure -->
<!-- Example for Vercel: -->
<!-- 1. Go to Vercel Dashboard → Project → Deployments -->
<!-- 2. Find last known-good deployment -->
<!-- 3. Click ... → Promote to Production -->
<!-- 4. Confirm -->

**Risk**: None. Previous deployment is still available.

### Option B: Git Revert via PR (3-5 minutes)

```bash
# Identify the bad commit on main
git log --oneline -5 origin/main

# Create revert
git checkout -b fix/revert-bad-commit origin/main
git revert <bad-commit-sha>
git push origin fix/revert-bad-commit

# Create emergency PR
gh pr create --base main --title "fix: revert [description]" --body "Emergency revert of [commit]. Cause: [brief description]."
```

**Use when**: Instant rollback isn't available or the issue spans multiple deploys.

### Option C: Database Restore (if data is affected)

<!-- FILL: Replace with your database backup/restore procedure -->
<!-- Example: -->
<!-- 1. Run backup restore script -->
<!-- 2. Verify data integrity -->
<!-- 3. Restart dependent services -->

**Use when**: Data corruption or accidental deletion. Last resort.

---

## 4. Communication — Keep People Informed

### Templates

**To users (if they're affected):**

> We're aware of [brief description]. Our team is working on it. We expect resolution within [time estimate]. We'll update you when it's fixed.

**Internal (to team):**

> **Incident**: [description]
> **Impact**: [who's affected, how severely]
> **Status**: [investigating / identified / fixing / resolved]
> **ETA**: [when we expect resolution]

---

## 5. Post-Mortem — Learn From It

After every non-trivial incident, document:

```markdown
## Post-Mortem: [Incident Title]

**Date**: [date]
**Duration**: [how long]
**Impact**: [who was affected, how]

### Timeline

| Time | Event |
|------|-------|
| HH:MM | [what happened] |

### Root Cause

[1-2 paragraphs. Be specific.]

### What Went Well

- [things that helped]

### What Went Wrong

- [things that made it worse or delayed resolution]

### Action Items

| # | Action | Owner | Due |
|---|--------|-------|-----|
| 1 | [specific fix] | [who] | [when] |

### Prevention

How do we make sure this never happens again?
```

Add to `.claude/landmines.md` if the incident reveals a pattern that could recur.

---

## Quick Reference

| Situation | Do This |
|-----------|---------|
| App is down for everyone | Instant rollback (Option A) |
| App is broken for one user | Check their data, check recent deploys |
| Data looks wrong | **STOP**. Don't deploy. Investigate first. |
| External service is down | Communicate to users. Wait. |
| Not sure what's wrong | Follow triage checklist top-to-bottom |

---

[Back to CLAUDE.md](../../CLAUDE.md) | [Documentation Hub](../README.md)
