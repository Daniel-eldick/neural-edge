# ORIENTATION.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is the **soul** of the system — the philosophy, mental models, and reasoning behind how we build. For commands and procedures, see the modular rules in `.claude/rules/` and guides in `docs/guides/`.

---

## 30-Second Orientation

**What is this?** A multi-layer AI trading bot that combines Freqtrade's execution engine with autonomous strategy optimization, real-time market intelligence signals, and (future) swarm prediction — all paper-trading only until the CEO says otherwise.

**Core Architecture:**

- **5-layer cake**: Freqtrade (execution) → Sensory (market intelligence) → Knowledge Graph (stub) → MiroFish Swarm (stub) → Autoresearch (optimization)
- **Signal-gated trading**: Minimum 3 uncorrelated signals must agree before any trade executes
- **Immutable evaluator**: The autoresearch loop optimizes strategy parameters, but can never modify the scoring function (`prepare.py`)
- **Paper-only**: `dry_run: true` is enforced at config level, hook level, and rule level

**Tech Stack**: Python 3.11+ + Freqtrade + pytest + ruff + mypy

**Mental Model**: Think of it as a chef (Freqtrade) who only cooks when enough taste-testers (sensory signals) agree the recipe works, and an overnight kitchen optimizer (autoresearch) that tweaks recipes but can't change the judging criteria.

---

## Engineering Philosophy

### The Mandate

**User Mandate:**

> _"I want you to be pessimistic when it comes to the quality of the code. I need you to be demanding and perfectionist with the code. We need to take more time to build the perfect system that will never fail."_

This is not optional. This is the foundation.

### What This Means in Practice

**Be Ruthlessly Critical.** Flag anything that _could_ fail under load, even if it works fine now. Don't wait for problems to manifest — anticipate them.

**Think at 10x Scale.** Every architectural decision must work at 10x current load. If an API call takes 50ms now, what happens when we're tracking 50 pairs instead of 5? If the sensory system handles 4 signals, what happens with 12?

**Challenge Everything.** Question patterns, assumptions, and "it works" solutions. The fact that code runs doesn't mean it's correct. The fact that tests pass doesn't mean the system is robust.

**Demand Proof.** Don't accept "should work" — verify with:

- `freqtrade backtesting` for strategy performance claims (Sharpe ratio, max drawdown, win rate)
- Integration tests with mocked failure modes for API reliability claims
- Unit tests at boundary conditions for risk/sizing claims

**Flag Technical Debt Immediately.** When you see code that works now but will fail at scale, document it in TECHNICAL_DEBT.md. Don't defer this — the debt compounds.

### Questions to Ask Constantly

- What happens when this fails? (not _if_, _when_)
- What happens when the exchange API is down for 30 minutes?
- Can the autoresearch loop game the evaluator indirectly?
- What if all 4 signal sources disagree? What if they all agree but are wrong?
- Are we respecting API rate limits at scale?

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

This is a paper-trading bot today. But the architecture must be ready for real money when the CEO authorizes it. `dry_run: true` is enforced at three levels: Freqtrade config, Claude Code rule (`paper-only-mandate.md`), and protect-files hook.

**User Mandate:**

> _"Never push to main without my confirmation... pushing affects users in production."_

### The Two-Layer Model

Think of it as: `develop` = the kitchen (prep, taste, adjust), `main` = the pass (only complete plates go to customers).

1. **Feature branches fork from `develop`** — via `/worktree create`
2. **PRs target `develop`** — Triggers CI + preview
3. **Merge to `develop`** — Tiered approval (Low = auto, Medium = CEO ok, High = trigger phrase)
4. **CEO tests on staging** — Staging deploys from `develop`
5. **Run `/release`** — Promotes develop → main when CEO says "ship it"

### The Invariant

```
NEVER push to main directly. Only /release can promote develop → main.
ALL changes flow: feature branch → PR → develop (staging) → /release → main (production).
```

This is non-negotiable. No exceptions. No "obviously safe" shortcuts.

---

## How to Think in This Codebase

### The 5-Layer Mental Model

Each layer is independent and can be disabled without affecting the others. Think of them as stackable upgrades:

1. **Layer 1 (Freqtrade)** — The execution engine. Always on. Handles candles, TA indicators, order placement.
2. **Layer 2 (Sensory)** — Market intelligence feeds. Can be disabled per-source via config. Strategy runs with TA-only if all sensors fail.
3. **Layer 3 (Knowledge Graph)** — Future. Stub only. Entity-relationship modeling for market events.
4. **Layer 4 (MiroFish Swarm)** — Future. Stub only. Multi-agent prediction via Docker sidecar.
5. **Layer 5 (Autoresearch)** — Autonomous optimization. Can be paused. Strategy continues with last-known-good parameters.

### Signal-First Workflow

When adding features, think signals:

1. **Source** — Where does the data come from? (API, calculation, model)
2. **Signal** — What structured output does it produce? (direction, confidence, timestamp)
3. **Aggregation** — How does it integrate with the convergence gate? (min 3 rule)
4. **Action** — How does it affect position sizing or trade decisions?

Never build a signal source without defining its failure mode (what happens when the API is down?).

### State Management

- **Strategy state** → Freqtrade manages via `IStrategy` interface
- **Signal state** → In-memory, per-tick (no persistence needed for paper trading)
- **Experiment state** → `results.tsv` (append-only log, git-tracked)
- **Configuration** → `config.json` + `.env` (never hardcode)

---

## The Core Documents

These documents MUST stay synchronized. If they conflict, stop and align them before proceeding.

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
3. **Production Safety** — Never push without confirmation. Even paper trading gets the full safety treatment.

The modular rules in `.claude/rules/` provide context-specific guidance. The guides in `docs/guides/` provide deep reference. This document provides the **why** behind all of it.

Welcome to the codebase.

---

[Back to CLAUDE.md](../../CLAUDE.md) | [Documentation Hub](../README.md)
