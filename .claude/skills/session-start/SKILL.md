---
name: session-start
description: Initialize session with project context, last-session reconstruction, and documentation health dashboard.
allowed-tools: Read, Glob, Bash, mcp__database__get_advisors
---

# Session Start Skill

Answers two questions: **"What happened last session?"** and **"What should I work on right now?"**

## When to Use

- `/session-start`, "start session", "what's the status"
- Beginning of any new working session

## When NOT to Use

- Mid-session context switch (just read the relevant docs directly)
- Quick question that doesn't need full context loading
- Already know what you want to work on (just start)

---

## Workflow

### Phase 0: Context Reconstruction (~30 seconds)

Reconstruct what happened in the last session using signals that already exist. Run before system status checks.

**1. Recent Git Activity**

```bash
git log --oneline -10
git diff --stat HEAD~5
```

What was committed recently? What files were touched?

**2. Read Memory Signals**

```
Read: memory/observations.md    → Any recent observations?
Read: memory/intuitions.md      → Full read (small file, 15-30 entries).
                                  Surface any intuitions relevant to the detected work area.
```

**3. Synthesize Brief**

```
"Last session worked on [X]. Key decisions: [Y]. Open items: [Z].
Relevant intuitions: [list any that match current work area]."
```

Present the brief before moving to Phase 1. If git log shows no recent activity (new project, long gap), skip to Phase 1.

---

### Phase 1: System Status (MCP-Driven)

Execute checks in parallel:

**1. Run database advisors**

```
mcp__database__get_advisors({ type: "security" })
mcp__database__get_advisors({ type: "performance" })
```

Extract CRITICAL findings (blocking) and WARNING findings (non-blocking).

**2. Read 5 Core Documents**

```
Read: docs/INCOMPLETE_FEATURES.md
Read: docs/TECHNICAL_DEBT.md
Read: docs/PRODUCTION_READINESS_ROADMAP.md
Read: docs/OFFLINE_SYSTEM_STATUS.md
Read: docs/BACKLOG.md
```

**3. Check Active Work**

```
Glob: docs/active/*.md
```

For each file, extract status and % completion. Detect completion markers.

### Phase 2: Decision Tree (Converge to ONE Path)

```
Phase 0 detected clear continuation context?
  ├─ YES: Recent commits + active doc align
  │   → PATH 0: CONTINUE FROM LAST SESSION
  │
BLOCKING issues exist?
  ├─ YES: MCP CRITICAL OR ✅ COMPLETE files in active/
  │   → PATH 1: UNBLOCK SESSION
  │
  ├─ NO, but active work exists? (IN PROGRESS docs)
  │   → PATH 2: CONTINUE ACTIVE WORK
  │
  └─ NO active work
      → PATH 3: START NEW WORK
```

#### PATH 0: CONTINUE FROM LAST SESSION

Phase 0 context is clear — recent commits point to a specific active doc or work area. Recommend continuing directly. Show the Phase 0 brief and the active doc status. Skip the full system status scan unless user asks.

#### PATH 1: UNBLOCK SESSION

MCP advisors CRITICAL → recommend `/db-audit`.
Completed docs in active/ → recommend `/sync-docs`.

#### PATH 2: CONTINUE ACTIVE WORK

Show active docs with progress. Recommend continuing highest-% doc. Show HIGH priority items if user wants to switch.

#### PATH 3: START NEW WORK

Show HIGH priority items from TECHNICAL_DEBT.md. Show top backlog items. Recommend `/plan` or `/brainstorm`.

### Phase 3: Handoff

Route to the appropriate skill based on user's choice. Don't auto-start — present options, let user decide.

**Decision Matrix** — If Phase 1-2 surfaced specific signals, recommend the matching skill:

| If You Find                                            | Recommend                     | Why                                                        |
| ------------------------------------------------------ | ----------------------------- | ---------------------------------------------------------- |
| MCP advisor CRITICAL security finding                  | `/db-audit`                   | Security issues need dedicated audit before any other work |
| `✅ COMPLETE` file in `docs/active/`                   | `/organize` or manual archive | Completed docs blocking active/ signal clarity             |
| Active planning doc at 80%+                            | Continue implementation       | Almost done — finish before starting new work              |
| Active planning doc at < 30%, stale > 7 days           | Ask CEO: continue or shelve?  | May be abandoned — don't assume                            |
| Open PRs awaiting review                               | `/review-pr`                  | Unmerged PRs accumulate conflict risk                      |
| 5+ unreviewed observations in `memory/observations.md` | `/coffee-break`               | Observations backlog needs processing                      |
| No active work, HIGH items in TECHNICAL_DEBT.md        | `/plan` for top HIGH item     | Proactive debt reduction                                   |
| No active work, no HIGH debt                           | Show BACKLOG.md top 3         | Let CEO pick direction                                     |
| Recent deploy (last commit < 24h, touches `src/`)      | `/prod-audit quick`           | Verify production health after changes                     |

---

## Principles

1. **Converge to ONE path** — Don't present all three paths. Analyze and pick the right one.
2. **Blocking before new work** — CRITICAL issues and archival violations take priority.
3. **Specific, not vague** — "Continue SKILLS_REWORK.md (65%)" not "you have some active work".
4. **Delegate, don't duplicate** — Doc health checks → `/sync-docs`. DB issues → `/db-audit`. Don't inline their logic.
5. **Fast** — This is a 2-minute orientation, not a 15-minute audit.
6. **No hedging** — Say "Continue X" or "Start Y", not "you might want to consider..."

---

## Anti-Patterns

- Using bash parsing instead of reading structured docs with Read tool
- Showing violations without recommending a specific fix skill
- Ending with open-ended questions (always use decision tree with specific options)
- Blocking work without clear unblock path
- Duplicating `/sync-docs` functionality inline
- Using hedging language ("might want", "could", "perhaps")
- Presenting >3 decision paths (converge to ONE)
- Spending more than 2-3 minutes gathering context

---

## Skill Pipeline

```
/session-start → (routes to one of:)
  ├─ /db-audit (if CRITICAL DB issues)
  ├─ /sync-docs (if archival violations)
  ├─ /review-pr (if open PRs need merging)
  ├─ continue active work (resume implementation)
  ├─ /research (if current external knowledge needed)
  ├─ /plan (if starting new work)
  └─ /brainstorm (if problem unclear)
```
