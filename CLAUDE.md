# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

<!-- FILL: Replace with your project's one-liner -->
**Project**: <!-- FILL: e.g., "Multi-tenant SaaS platform (React + TypeScript + Supabase)" -->
**Production**: <!-- FILL: e.g., "https://your-app.example.com (auto-deploys from `main`)" -->
**Staging**: <!-- FILL: e.g., "https://staging.your-app.example.com (auto-deploys from `develop`)" -->

**Branching**: `develop` = home base (the kitchen). `main` = production-only (the pass). Features branch from `develop`, PRs target `develop`. Only `/release` promotes develop → main.

---

## CRITICAL USER MANDATES (READ FIRST)

These mandates are always-on. Detailed implementation guidance auto-loads from `.claude/rules/`.

> **Do NOT use `EnterPlanMode`** when running the `/plan` skill. Plan mode disables Write/Edit, which the `/plan` skill needs to create DDD documents in `docs/active/`. Execute the skill directly.

### 1. Engineering Philosophy → `engineering-philosophy.md`

<!-- FILL: Replace with your team's engineering mandate. Example: -->
_"I want you to be pessimistic when it comes to the quality of the code. I need you to be demanding and perfectionist with the code. We need to take more time to build the perfect system that will never fail."_

### 2. Document-Driven Development → `document-driven-dev.md`

_"Document the plan to fix, the plan to test, and once approved we move to development. Keep updating the same documentation files with progress and completion percentage."_

**Workflow**: Plan → Document → Approve → Execute → Update → Archive

### 3. Production Safety → `production-safety.md`

<!-- FILL: Replace with your deployment context. Example: -->
_"Never push to main without my confirmation... pushing affects users in production."_

**Standard flow**: feature branch → PR → CI + preview → merge to `develop` → test on staging → `/release` to `main`
**Tiered merge to develop**: Low risk = auto-merge if CI + preview clean. Medium = CEO approval. High = trigger phrase.
**Production promotion**: Only via `/release` — CEO says "ship it" / "release it" / "push to production".

### 4. MCP Tools & Agents First → `mcp-tools.md`

_"Use of agents, MCPs, and frequent commits to GitHub are always encouraged"_

### 5. Performance Awareness

<!-- FILL: Replace with your performance context. Example: -->
<!-- "Users are on 1-5 Mbps. Critical path budget: < 300KB gzipped." -->
<!-- "Enterprise users expect sub-200ms API responses." -->
_"Every new dependency must justify its cost. Always lazy-load non-critical SDKs."_

### 6. Fail Loudly

No silent degradation. No swallowed errors. No mock data in production paths. If the backend is unreachable, crash explicitly — don't serve stale data without telling the user.

### 7. Mandatory Pushback

Challenge requests that risk data integrity, security, or correctness. "Delayed correct code > fast fragile code" is not a suggestion — it's the engineering standard.

### 8. UX-First Design

<!-- FILL: Replace with your UX litmus test. Example: -->
_"If a busy user can't figure it out under pressure, it's a bug — not a training issue."_

Run `/ux-design` before `/plan` for user-facing features. 8 principles: Visibility, Forgiveness, Minimalism, Consistency, Context-awareness, Error recovery, Speed of use, Learnability.

### 9. CEO-CTO Communication → `ceo-cto-communication.md`

_"You handle the noise, I handle the signal. Give me CEO-level briefs — I'll ask for details when I need them."_

**In conversation**: Lead with the signal — What / Why / Risk / Trade-off / Your call. Use analogies over jargon. Link to full details.
**In artifacts**: Full CTO detail stays intact — plans, code reviews, QA reports stay comprehensive for execution.

---

## SESSION START CHECKLIST

```
┌─────────────────────────────────────────────────────────┐
│  READ THESE FIRST (blocking):                           │
│  1. docs/INCOMPLETE_FEATURES.md - Any blocking items?   │
│  2. docs/TECHNICAL_DEBT.md - Active scalability concerns│
│  3. docs/guides/ORIENTATION.md - Re-read for complex work│
└─────────────────────────────────────────────────────────┘
```

---

## CORE DOCUMENTS (Source of Truth)

**All decisions must reference these** — keep them synchronized:

<!-- FILL: Adjust to your project's core docs. Default set: -->
1. **[INCOMPLETE_FEATURES.md](docs/INCOMPLETE_FEATURES.md)** - Check FIRST at session start
2. **[PRODUCTION_READINESS_ROADMAP.md](docs/PRODUCTION_READINESS_ROADMAP.md)** - Master plan
3. **[TECHNICAL_DEBT.md](docs/TECHNICAL_DEBT.md)** - Scalability concerns
4. **[BACKLOG.md](docs/BACKLOG.md)** - Future work
<!-- FILL: Add your 5th core doc if applicable (e.g., OFFLINE_SYSTEM_STATUS, API_STATUS, etc.) -->

---

## Quick Start

<!-- FILL: Replace with your project's commands -->
```bash
# FILL: Your install + dev command
npm install && npm run dev  # http://localhost:5173

# FILL: Your quality check command (must match quality-gate.sh hook)
npm run quality:check       # Format + lint + type-check + tests (REQUIRED before commits)
```

## Common Commands

<!-- FILL: Replace entirely with your project's command reference -->
```bash
# Development
# FILL: dev, build, preview commands

# Testing
# FILL: test commands (unit, e2e, full suite)

# Code Quality
# FILL: lint, type-check, format commands

# Database (if applicable)
# FILL: type generation, migration commands
```

## Architecture Overview

<!-- FILL: Replace this entire section with your project's architecture -->
<!-- Include: -->
<!-- - Provider/module hierarchy (if applicable) -->
<!-- - Data flow diagram (the core mental model) -->
<!-- - State management patterns -->
<!-- - Code splitting strategy -->
<!-- - Route structure -->

```
<!-- FILL: Your core data flow diagram -->
```

## Key Files

<!-- FILL: Replace with your project's key files -->
<!-- Example: -->
<!-- - [src/App.tsx](src/App.tsx) - Entry point -->
<!-- - [src/lib/api/](src/lib/api/) - API layer -->

## Important Conventions

### Working Style

- **Bug fixes and small tasks** (< 3 files): implement directly, no planning doc needed unless asked.
- **Features and multi-file work**: always follow DDD — plan, document, approve, then execute.
- Always run `git branch --show-current` before any git operation. Never assume which branch you're on.

<!-- FILL: Add project-specific conventions -->
<!-- Example: "Use `canceled` (single L) to match database enum values." -->

### Code Quality Tooling

<!-- FILL: Replace with your project's tooling -->
<!-- Example: -->
<!-- - **Prettier** formats all code -->
<!-- - **Husky + lint-staged** pre-commit hook -->
<!-- - **GitHub Actions CI**: `npm run quality:check` on every push/PR -->

### Test Configuration

<!-- FILL: Replace with your project's test config -->
<!-- Example: -->
<!-- - **Unit tests** (Vitest/Jest): environment, coverage thresholds -->
<!-- - **E2E tests** (Playwright/Cypress): browser projects, timeout, workers -->
<!-- - **Test IDs**: `data-testid="{component}-{element}-{modifier}"` -->

## Debugging

<!-- FILL: Add project-specific debugging tips -->
<!-- Example: -->
<!-- ```bash -->
<!-- # Browser console debug commands -->
<!-- window.debug.getStatus() -->
<!-- ``` -->

## Compaction Instructions

When context is compacted, always preserve:

1. Current git branch name (run `git branch --show-current` after compaction)
2. List of modified files and their purpose
3. Active planning document path (any `docs/active/*.md` being worked on)
4. Test results from commands already run
5. Never promote to main without explicit user confirmation (use `/release`)
6. Main worktree lives on `develop` branch — `main` is production-only
<!-- FILL: Add project-specific items to preserve across compaction -->

## Documentation

| Resource                                                 | Purpose                             |
| -------------------------------------------------------- | ----------------------------------- |
| [docs/guides/ORIENTATION.md](docs/guides/ORIENTATION.md) | System philosophy and mental models |
| [docs/README.md](docs/README.md)                         | Documentation hub                   |
| [docs/guides/](docs/guides/)                             | Specialized guides                  |
| [.claude/rules/](.claude/rules/)                         | Auto-loaded context rules           |
| [.claude/references/](.claude/references/)               | Curated external pattern references |

## Rules (Auto-Loaded by Context)

| Rule                   | Triggers                  | Details                                          |
| ---------------------- | ------------------------- | ------------------------------------------------ |
| engineering-philosophy | `src/**/*.ts(x)`          | Deep dive protocols, code review questions       |
| document-driven-dev    | `docs/**`                 | DDD workflow, completion triggers, archival      |
| production-safety      | deployment commands       | Risk assessment, PR merge protocol               |
| git-workflow           | git commands              | Conventional commits, pre-commit checklist       |
| testing                | `e2e/**`, `*.test.ts`     | Test commands, testid conventions                |
| mcp-tools              | MCP tool usage            | Tool selection, agent usage                      |
| ceo-cto-communication  | all communication         | CEO signal format, analogies, brief style        |
| autonomous-guardrails  | quality gate execution    | Anti-gaming rules for self-correction loops      |
| error-recovery         | tool/MCP failures         | Retry patterns, fallback table, escalation tiers |
| worktree-autorun       | WORKTREE.md present       | Auto-detect and execute worktree manifests       |
<!-- FILL: Add module-specific rules if activated (e.g., database-safety, admin-styling) -->

## Skills (Optional Workflow Tools)

Skills in `.claude/skills/*/SKILL.md`. Use for structured workflows; direct action is fine for simple tasks.

### Brain/Hands Worktree Model

```
MAIN WORKTREE (brain — on `develop` branch — plans, reviews, merges)
├── /session-start        → orient + decide what to work on
├── /investigate          → deep codebase research + knowledge map maintenance
├── /research             → investigate current standards, tools, best practices
├── /brainstorm           → ideate if problem unclear
├── /ux-design            → design UX for user-facing features
├── /plan                 → create planning document
├── /sign-off             → approve plan before building
├── /worktree create      → spawn feature worktree (from develop)
├── /deploy               → push commits to develop (staging)
├── /review-pr            → review PR + merge to develop + cleanup
├── /release              → promote develop → main (production) with CEO gate
└── periodic: /sync-docs, /hygiene, /organize, /wow-audit

FEATURE WORKTREE (hands — builds, tests, pushes)
├── implement             → write the code
├── /test                 → run tests with failure analysis
├── /diagnose             → debug errors and failures
├── /code-review          → analytical quality gate
├── /qa                   → integration quality gate
├── /sign-off             → approve implementation (optional, for high-risk)
├── commit                → natural (git-workflow rules handle format)
└── push + create PR      → natural (gh pr create, targeting develop)
```

### Skills Table

| Skill               | Where   | Purpose                                                                  |
| ------------------- | ------- | ------------------------------------------------------------------------ |
| `/session-start`    | Main    | Initialize session with project context + last-session reconstruction    |
| `/investigate`      | Any     | Tiered internal codebase research + living knowledge map                 |
| `/research`         | Main    | Structured internet research with confidence-tagged findings             |
| `/brainstorm`       | Main    | Interactive ideation before planning                                     |
| `/ux-design`        | Main    | UX conception for user-facing features                                   |
| `/plan`             | Main    | Create planning documents (DDD workflow)                                 |
| `/sign-off`         | Both    | Quality gate — plan approval (main) or implementation approval (feature) |
| `/worktree`         | Main    | Create, list, sync parallel workspaces                                   |
| `/deploy`           | Main    | Push commits to develop (staging) — all files go directly                |
| `/review-pr`        | Main    | PR review + merge to develop + worktree cleanup                          |
| `/release`          | Main    | Promote develop → main (production) with CEO gate + health check         |
| `/code-review`      | Feature | Analytical code quality gate                                             |
| `/qa`               | Feature | Integration quality gate (automated + manual)                            |
| `/test`             | Any     | Smart test runner with failure analysis                                  |
| `/diagnose`         | Any     | Error analysis and fix suggestions                                       |
| `/sync-docs`        | Main    | Document synchronization check                                           |
| `/organize`         | Main    | Audit docs/ and skills/ directories                                      |
| `/hygiene`          | Main    | Monthly code-level cleanup                                               |
| `/wow-audit`        | Main    | Ways of Working process review                                           |
| `/coffee-break`     | Main    | Review observations + graduate to intuitions/memory/backlog              |
| `/self-optimize`    | Any     | **EXPERIMENTAL**: Autonomous optimization loop (autoresearch pattern)    |
<!-- FILL: Add module skills if activated (e.g., /db-audit, /prod-audit, /legal-compliance, /content, /perf-audit, /scaling-check) -->

**Pipeline**: `/session-start` → `/investigate` → `/research` → `/brainstorm` → `/ux-design` → `/plan` → `/sign-off` → `/worktree create` → implement → `/code-review` → `/qa` → commit → push → PR → `/review-pr` → merge to develop → CEO tests staging → `/release` → production
**Periodic**: `/sync-docs` (after major work), `/organize` + `/hygiene` (monthly), `/wow-audit` (quarterly)
**On-demand**: `/investigate` (any time — codebase questions, pre-change understanding, drift detection), `/self-optimize` (when time allows — experimental autonomous optimization)
**Observations**: When you notice patterns, smells, or potential issues during work — append to `memory/observations.md`. CEO reviews periodically.
**Memory architecture**: System 1 (fast files: MEMORY.md, intuitions.md, rules/) + System 2 (slow skills: /investigate, /research, /plan). Bridge: observations.md → /coffee-break → graduation to System 1 files.

## Status

See [PRODUCTION_READINESS_ROADMAP.md](docs/PRODUCTION_READINESS_ROADMAP.md) for current status.
