# simplrr-framework

A stack-agnostic development operating system for [Claude Code](https://claude.com/claude-code). Turns Claude into a CTO — with Document-Driven Development, quality gates, memory, safety hooks, and 23+ skills for the full software lifecycle.

**Not an app framework. Not a boilerplate.** This is the meta-layer: the process, discipline, and institutional knowledge that makes AI-assisted development predictable and safe.

## What's Inside

```
.claude/rules/      10 rules (auto-loaded by context — DDD, git, safety, quality)
.claude/skills/     23 core skills (session-start → release pipeline, + framework-sync)
.claude/hooks/       3 hooks (git safety, file protection, quality gate)
docs/               Documentation infrastructure (living docs, guides, archive lifecycle)
memory/             Persistent memory system (MEMORY.md, observations, intuitions, knowledge map)
CLAUDE.md           The constitution — mandates, architecture, conventions
```

### The Pipeline

```
/session-start → /investigate → /brainstorm → /ux-design → /plan → /sign-off
    → /worktree create → implement → /code-review → /qa → commit → push
    → PR → /review-pr → /deploy → /release
```

Every step has a skill. Every skill has quality gates. Every gate has guardrails against gaming.

### Optional Modules

Activate during setup based on your stack:

| Module | What it adds | When to enable |
|--------|-------------|----------------|
| **supabase** | `/db-audit`, `/scaling-check`, database-safety rule | Using Supabase |
| **devtools** | `/prod-audit` via Chrome DevTools MCP | Web apps with browser testing |
| **legal** | `/legal-compliance` + 9 jurisdiction reference files | Products with compliance needs |
| **content** | `/content` for brand-aligned content generation | Products with marketing needs |
| **perf** | `/perf-audit` + bundle-size optimization lens | Frontend performance matters |

## Lifecycle Skills

### `/simplrr-framework init` — New Project

Interactive wizard for greenfield projects. Asks about your stack, team, and risk tolerance. Creates the full framework structure with `[FILL]` markers for project-specific values.

### `/simplrr-framework integrate` — Existing Project

Investigation-style analysis of an existing codebase. Identifies what you already have, what's missing, and creates a migration plan. Non-destructive — never overwrites existing files.

### `/framework-sync push` — Contribute Back

Extracts framework improvements from a project and pushes them to this template repo. Built-in contamination filter prevents project-specific content from leaking into the universal framework.

### `/framework-sync pull` — Get Updates

Checks for framework updates and applies them to your project. Smart merge for adapter files preserves your customizations while incorporating template improvements.

## Quick Start

### New Project

1. Clone this repo (or use as GitHub template)
2. Run `/simplrr-framework init` in Claude Code
3. Fill in the `[FILL]` markers in `CLAUDE.md`, rules, and hooks
4. Start building with `/session-start`

### Existing Project

1. Copy `.claude/`, `docs/`, `memory/`, and `CLAUDE.md` into your project
2. Run `/simplrr-framework integrate` in Claude Code
3. Follow the migration plan it generates
4. Activate relevant modules

## Core Principles

1. **Document-Driven Development** — Plan before you code. Every feature has a planning doc that tracks progress from 0% to 100%. Archive when done.

2. **Quality Gates at Every Step** — `/code-review`, `/qa`, `/sign-off` are not optional. They have anti-gaming guardrails to prevent the AI from inflating its own scores.

3. **CEO/CTO Communication Model** — The human gets signal (What/Why/Risk/Trade-off). The AI keeps the noise (full technical detail in artifacts). Translation layer, not reduction.

4. **Production Safety** — Tiered deployment with explicit human gates. Low risk auto-merges. High risk requires trigger phrases. Production promotion requires explicit approval.

5. **Persistent Memory** — Lessons learned, intuitions, and observations survive across sessions. The AI gets smarter about YOUR project over time.

6. **Config Over Code** — Enable/disable features via configuration. Never delete working code — flag it.

## File Classifications

The `.framework-manifest.json` classifies every file:

| Type | Description | Sync behavior |
|------|-------------|---------------|
| **core** | Universal process files | Always accepted from upstream |
| **adapter** | Template files with `[FILL]` markers | Contamination check before accepting |
| **module** | Optional add-ons | Activated per-project |

## Requirements

- [Claude Code](https://claude.com/claude-code) CLI
- Git
- A project to work on

## License

Private. Internal use only.
