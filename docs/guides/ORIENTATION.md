# ORIENTATION.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is the **soul** of the system — the philosophy, mental models, and reasoning behind how we build. For commands and procedures, see the modular rules in `.claude/rules/` and guides in `docs/guides/`.

---

## 30-Second Orientation

<!-- FILL: Replace with your project's 30-second pitch -->
**What is this?** <!-- FILL: e.g., "A multi-tenant SaaS platform." -->

**Core Architecture:**

<!-- FILL: Replace with 3-4 bullet points describing your core architecture -->
<!-- Example: -->
<!-- - **Multi-tenant**: Each customer isolated by `tenant_id` via RLS -->
<!-- - **Offline-first**: Operations survive network failures via local storage + background sync -->
<!-- - **API-first**: All functionality exposed via REST/GraphQL APIs -->

**Tech Stack**: <!-- FILL: e.g., "Vite + React + TypeScript + Supabase + TanStack Query" -->

**Mental Model**: <!-- FILL: 1-2 sentences capturing how to think about this system -->

---

## Engineering Philosophy

### The Mandate

**User Mandate:**

> _"I want you to be pessimistic when it comes to the quality of the code. I need you to be demanding and perfectionist with the code. We need to take more time to build the perfect system that will never fail."_

This is not optional. This is the foundation.

### What This Means in Practice

**Be Ruthlessly Critical.** Flag anything that _could_ fail under load, even if it works fine now. Don't wait for problems to manifest — anticipate them.

**Think at 10x Scale.** Every architectural decision must work at 10x current load. If a query takes 50ms now, what happens with 10x the data? If a process handles 10 operations, what happens with 100 concurrent?

**Challenge Everything.** Question patterns, assumptions, and "it works" solutions. The fact that code runs doesn't mean it's correct. The fact that tests pass doesn't mean the system is robust.

**Demand Proof.** Don't accept "should work" — verify with:

- `EXPLAIN ANALYZE` for query performance
- Automated security/performance audit tools
- Actual load testing, not theoretical reasoning

**Flag Technical Debt Immediately.** When you see code that works now but will fail at scale, document it in TECHNICAL_DEBT.md. Don't defer this — the debt compounds.

### Questions to Ask Constantly

- What happens when this fails? (not _if_, _when_)
- Is this an N+1 query waiting to happen?
- Will this cause a memory leak over weeks of operation?
- What's the worst-case performance scenario?
- Are we creating a distributed systems footgun?

### The Preference

The user prefers **delayed, correct code** over **fast, fragile code**.

If you see a red flag: stop, document the concern with specific failure scenarios, propose a fix, and request time for a deep dive session.

---

## Document-Driven Development

### The Origin Principle

Coding without a test plan is coding blind. Tests with wrong success criteria are worse than no tests — they provide false confidence.

### The Principle

**Plan → Document → Approve → Execute → Update → Archive**

Never write code without:

1. A planning document in `docs/active/` with a comprehensive fix plan AND test plan
2. User approval ("go for it" confirmation)
3. Real-time progress updates (% completion, timestamps)

### Why This Works

The magic is in the approval step. You can't get approval without explaining your test plan. Explaining your test plan forces you to think through edge cases. Thinking through edge cases catches bugs before they're written.

### The Anti-Patterns

- "Fix quickly, document later" — No. You will forget crucial context.
- "Plan in chat only" — No. Chat disappears. Documents persist.
- "Skip test plan" — No. This is how critical bugs slip through.
- "Code before approval" — No. You might build the wrong thing.

---

## Production Safety

### The Context

<!-- FILL: Replace with your deployment context -->
<!-- Example: "CI/CD auto-deploys from two branches: `main` (production) and `develop` (staging). Any push to `main` immediately affects live users." -->

**User Mandate:**

> _"Never push to main without my confirmation... pushing affects users in production."_

### The Two-Layer Model

Think of it as: `develop` = the kitchen (prep, taste, adjust), `main` = the pass (only complete plates go to customers).

1. **Feature branches fork from `develop`** — via `/worktree create`
2. **PRs target `develop`** — Triggers CI + preview deploy
3. **Test on preview URL** — Verify changes work on the preview deployment
4. **Merge to `develop`** — Tiered approval (Low = auto, Medium = CEO ok, High = trigger phrase)
5. **CEO tests on staging** — Staging deploys from `develop`
6. **Run `/release`** — Promotes develop → main when CEO says "ship it"
7. **Post-release health check** — Automated verification, auto-revert if errors

### Risk Levels

| Level      | Criteria                                          | Examples                                 |
| ---------- | ------------------------------------------------- | ---------------------------------------- |
| **Low**    | UI-only, no data changes, well-tested             | CSS fixes, copy changes, read-only pages |
| **Medium** | New features, API changes, logic changes          | New dashboard, form validation, hooks    |
| **High**   | Database migrations, auth changes, critical paths | Schema changes, security policies, sync  |

### The Invariant

```
NEVER push to main directly. Only /release can promote develop → main.
ALL changes flow: feature branch → PR → develop (staging) → /release → main (production).
```

This is non-negotiable. No exceptions. No "obviously safe" shortcuts.

---

## How to Think in This Codebase

<!-- FILL: Replace this entire section with your project's mental models -->
<!-- Include: -->
<!-- - Provider/component hierarchy diagram -->
<!-- - Database-first workflow (if applicable) -->
<!-- - Key domain concepts -->
<!-- - State management patterns -->

### Database-First Workflow

When adding features:

1. **Schema** — Write the schema change
2. **Types** — Regenerate types from the schema
3. **Logic** — Create data access layer / hooks
4. **UI** — Build components using the logic layer
5. **Tests** — Write tests for the user flow

Never build UI before the schema is finalized. The types drive everything.

### State Management Pattern

<!-- FILL: Replace with your state management approach -->
<!-- Example: -->
<!-- - **Server state** → TanStack Query (with stale time) -->
<!-- - **App state** → React Context -->
<!-- - **Form state** → React Hook Form with Zod -->
<!-- - **URL state** → React Router params -->

Don't mix state types. Each has its purpose.

---

## The Core Documents

These documents MUST stay synchronized. If they conflict, stop and align them before proceeding.

<!-- FILL: Adjust document list to match your project's core docs -->
1. **INCOMPLETE_FEATURES.md** — Check FIRST at every session. Contains blocking items.
2. **PRODUCTION_READINESS_ROADMAP.md** — Single source of truth for overall status.
3. **TECHNICAL_DEBT.md** — Code that works now but will fail at scale.
4. **BACKLOG.md** — Future features and deferred optimizations.

### Session Start Checklist

1. Check INCOMPLETE_FEATURES.md for blocking items
2. Check TECHNICAL_DEBT.md for active concerns
3. If documents conflict on status or percentages, fix the conflict before doing any other work

---

## MCP Tools Philosophy

**User Mandate:**

> _"Use of agents, MCPs, and frequent commits to GitHub are always encouraged"_

### Prefer MCP Over Bash

<!-- FILL: Replace with your project's MCP tool mapping -->
| Operation       | Use This            | Not This          |
| --------------- | ------------------- | ----------------- |
| Database query  | Database MCP        | CLI via bash      |
| Security audit  | Audit MCP tool      | Manual inspection |
| Browser testing | DevTools MCP        | Manual clicking   |

MCP tools provide structured output, better error handling, and audit trails.

### When to Use Agents

- **Explore Agent** — Codebase exploration, "where is...", "how does..."
- **Plan Agent** — Feature breakdown, implementation roadmaps
- **Task Agent** — Complex multi-step work (3+ steps)

Use agents proactively. They're not a last resort — they're a first choice for complex work.

---

## Summary

This codebase is built on three pillars:

1. **Pessimistic Engineering** — Assume things will fail. Plan for 10x scale. Demand proof.
2. **Document-Driven Development** — Plan before coding. Test plan before approval. Archive everything.
3. **Production Safety** — Never push without confirmation. Real users depend on this.

The modular rules in `.claude/rules/` provide context-specific guidance. The guides in `docs/guides/` provide deep reference. This document provides the **why** behind all of it.

Welcome to the codebase.

---

[Back to CLAUDE.md](../../CLAUDE.md) | [Documentation Hub](../README.md)
