# Skills Manual

Complete reference for all skills available in this framework. Skills are structured workflows that enforce quality and consistency. Direct action is fine for simple tasks — use skills when structure adds value.

---

## The Pipeline

```
/session-start → /investigate → /research → /brainstorm → /ux-design → /plan → /sign-off
    → /worktree create → implement → /code-review → /qa → commit → push → PR
    → /review-pr → merge to develop → CEO tests staging → /release → production
```

**Not every step is needed.** A trivial bug fix might be: implement → commit → push → `/review-pr`. The pipeline is the maximum ceremony — scale down for simpler work.

---

## Core Skills (21)

### Planning & Design

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `/session-start` | Initialize session with project context, last-session reconstruction, doc health check | Every new session |
| `/investigate` | Tiered codebase research (Quick/Investigate/Audit) + living knowledge map | Before modifying unfamiliar code, "how does X work?" |
| `/research` | Structured internet research with confidence-tagged findings (3 gears) | Need current external knowledge, technology evaluation |
| `/brainstorm` | Interactive ideation workshop (design thinking phases) | Problem unclear, multiple valid approaches, new feature with business implications |
| `/ux-design` | UX conception: user context, journey maps, wireframes, 8 principles | Before `/plan` for any user-facing feature |
| `/plan` | Create planning documents in `docs/active/` (Quick/Standard/Full tiers) | Any non-trivial work (3+ files or unclear scope) |
| `/sign-off` | Quality gate for plans (risk-proportionate review, self-correction loop) | After `/plan`, before implementation |

### Implementation & Quality

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `/worktree` | Parallel feature workspaces (create, list, sync, remove) | Working on multiple features simultaneously |
| `/code-review` | Strict pre-commit quality gate (evidence-based findings + verdict) | Before committing in feature worktrees |
| `/qa` | Pre-merge quality gate (automated checks + manual verification) | After implementation, before pushing |
| `/test` | Smart test runner with failure analysis | Running tests, debugging test failures |
| `/diagnose` | Error analysis: stack trace parsing, root cause, fix suggestions | Tests fail, builds break, runtime errors |

### Deployment & Operations

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `/deploy` | Push commits to `develop` (staging) | Direct commits to develop (no PR needed) |
| `/review-pr` | PR review + merge to `develop` + worktree cleanup | After a feature worktree pushes a PR |
| `/release` | Promote `develop` → `main` (production) with CEO gate + health check | CEO says "ship it" / "release it" |

### Maintenance & Auditing

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `/sync-docs` | Check and fix document synchronization across core docs | After major work, periodic alignment |
| `/organize` | Audit and reorganize `docs/` and `skills/` directories | Monthly/quarterly maintenance |
| `/hygiene` | Monthly code-level cleanup (dead code, stale patterns, drift) | Monthly or after major feature work |
| `/wow-audit` | Ways of Working process review (10 heuristic checks) | Quarterly process improvement |
| `/coffee-break` | Review observations notepad, graduate entries to memory/backlog | Periodically, when observations accumulate |

### Experimental

| Skill | Purpose | When to Use |
|-------|---------|-------------|
| `/self-optimize` | Autonomous optimization loop (modify → measure → keep/discard → repeat) | When time allows, with a specific lens config |

---

## Module Skills (activated by `/simplrr-framework init`)

These skills live in `.claude/skills/_modules/` and are copied to `.claude/skills/` when their module is activated.

### Supabase Module

| Skill | Purpose |
|-------|---------|
| `/db-audit` | Database security and performance audit using Supabase advisors |
| `/scaling-check` | Capacity assessment against Supabase metrics and thresholds |

**Also activates**: `database-safety.md` rule

### DevTools Module

| Skill | Purpose |
|-------|---------|
| `/prod-audit` | Production console & network health audit via Chrome DevTools MCP |

### Legal Module

| Skill | Purpose |
|-------|---------|
| `/legal-compliance` | 3-mode legal compliance (Audit, Gate, Counsel) with jurisdiction reference files |

**Also activates**: 9 reference files (GDPR, CCPA, WCAG, PCI-DSS, etc.)

### Content Module

| Skill | Purpose |
|-------|---------|
| `/content` | Generate on-brand content using marketing/brand context files |

### Performance Module

| Skill | Purpose |
|-------|---------|
| `/perf-audit` | Frontend performance audit with bundle analysis and Core Web Vitals |

**Also activates**: `bundle-size.md` lens for `/self-optimize`

---

## Periodic Schedule

| Frequency | Skills |
|-----------|--------|
| Every session | `/session-start` |
| After major work | `/sync-docs` |
| Monthly | `/hygiene` + `/organize` |
| Quarterly | `/wow-audit` |
| Before scaling | `/scaling-check` (if Supabase module active) |
| After deploys | `/prod-audit` (if DevTools module active) |
| As needed | `/investigate`, `/self-optimize` |

---

## Skill Tiers (Quality Gates)

Three skills act as quality gates with tiered rigor:

| Skill | Tiers | Pass Threshold |
|-------|-------|----------------|
| `/plan` | Quick (🟢) / Standard (🟡) / Full (🔴) | Risk-matched — auto-detected from scope |
| `/sign-off` | Quick / Standard / Full (matches plan tier) | Quick ≥7, Standard ≥7.5, Full ≥8 |
| `/code-review` | Standard scoring dimensions | Must pass with no CRITICAL findings |

---

## Anti-Patterns

- Running `/plan` for a 1-line bug fix (just do it)
- Skipping `/sign-off` on a Full-tier plan (the risk is real)
- Running `/release` without CEO confirmation (non-negotiable)
- Using `/investigate` for external knowledge (use `/research`)
- Skipping `/code-review` before committing (the safety net)

---

[Back to CLAUDE.md](../../CLAUDE.md) | [Documentation Hub](../README.md)
