# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Project**: NeuralEdge — Multi-layer AI trading bot (Python 3.11+ + Freqtrade + autoresearch optimization)
**Production**: Not deployed — paper trading only (`dry_run: true` is non-negotiable until explicit CEO approval)
**Staging**: N/A (local development + Docker)

**Branching**: `develop` = home base (the kitchen). `main` = production-only (the pass). Features branch from `develop`, PRs target `develop`. Only `/release` promotes develop → main.

---

## CRITICAL USER MANDATES (READ FIRST)

These mandates are always-on. Detailed implementation guidance auto-loads from `.claude/rules/`.

> **Do NOT use `EnterPlanMode`** when running the `/plan` skill. Plan mode disables Write/Edit, which the `/plan` skill needs to create DDD documents in `docs/active/`. Execute the skill directly.

### 1. Engineering Philosophy → `engineering-philosophy.md`

_"I want you to be pessimistic when it comes to the quality of the code. I need you to be demanding and perfectionist with the code. We need to take more time to build the perfect system that will never fail."_

### 2. Document-Driven Development → `document-driven-dev.md`

_"Document the plan to fix, the plan to test, and once approved we move to development. Keep updating the same documentation files with progress and completion percentage."_

**Workflow**: Plan → Document → Approve → Execute → Update → Archive

### 3. Production Safety → `production-safety.md`

_"Never push to main without my confirmation... pushing affects users in production."_

**Paper-only mandate**: `dry_run: true` in Freqtrade config. No real money trades without explicit CEO authorization. The `paper-only-mandate.md` rule flags any config with `dry_run: false`.

**Standard flow**: feature branch → PR → CI + preview → merge to `develop` → test on staging → `/release` to `main`
**Tiered merge to develop**: Low risk = auto-merge if CI + preview clean. Medium = CEO approval. High = trigger phrase.
**Production promotion**: Only via `/release` — CEO says "ship it" / "release it" / "push to production".

### 4. MCP Tools & Agents First → `mcp-tools.md`

_"Use of agents, MCPs, and frequent commits to GitHub are always encouraged"_

### 5. Performance Awareness

_"Every new dependency must justify its cost. Respect API rate limits: CoinGecko 30 req/min, Alpaca 200 req/min. Batch API calls by design — no N+1 patterns against external services."_

### 6. Fail Loudly

No silent degradation. No swallowed errors. No mock data in production paths. If an API is unreachable, crash explicitly or return an empty signal with a logged warning — don't serve stale data without telling the user.

### 7. Mandatory Pushback

Challenge requests that risk data integrity, security, or correctness. "Delayed correct code > fast fragile code" is not a suggestion — it's the engineering standard.

### 8. UX-First Design

_"If the bot can't explain WHY it made a trade in one sentence, the signal logic is wrong."_

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

1. **[INCOMPLETE_FEATURES.md](docs/INCOMPLETE_FEATURES.md)** - Check FIRST at session start
2. **[PRODUCTION_READINESS_ROADMAP.md](docs/PRODUCTION_READINESS_ROADMAP.md)** - Master plan
3. **[TECHNICAL_DEBT.md](docs/TECHNICAL_DEBT.md)** - Scalability concerns
4. **[BACKLOG.md](docs/BACKLOG.md)** - Future work

---

## Quick Start

```bash
# Prerequisites (macOS)
brew install ta-lib                    # C library required by Freqtrade

# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Quality gate (REQUIRED before commits — must match quality-gate.sh hook)
ruff check . && mypy . && pytest -x --timeout=30
```

## Common Commands

```bash
# Development
freqtrade trade --dry-run --config config.json           # Paper trading
freqtrade test-strategy --strategy AlphaStrategy         # Validate strategy loads
freqtrade backtesting --strategy AlphaStrategy           # Run backtest

# Testing
pytest                                # Run all tests
pytest -x --timeout=30               # Fail fast, 30s timeout
pytest --cov                         # With coverage report
pytest tests/test_strategies/        # Single directory
pytest tests/test_sensory/test_news.py -k "test_api_error"  # Single test by name

# Code Quality
ruff check .                         # Lint
ruff format .                        # Auto-format
mypy .                               # Type checking

# Docker
docker compose up                    # Freqtrade in paper mode (future: + MiroFish sidecar)
```

## Architecture Overview

### The 5-Layer Cake

```
┌─────────────────────────────────────────────────────────┐
│  Layer 5: AUTORESEARCH LOOP                             │
│  Autonomous strategy optimization (Karpathy pattern)    │
│  Immutable evaluator: Sharpe ratio on paper P&L         │
├─────────────────────────────────────────────────────────┤
│  Layer 4: MIROFISH SWARM (Weekend 2+ — stub only)       │
│  Multi-agent prediction via Docker sidecar              │
├─────────────────────────────────────────────────────────┤
│  Layer 3: KNOWLEDGE GRAPH (Future — stub only)          │
│  FinDKG/Graphiti for entity-relationship modeling       │
├─────────────────────────────────────────────────────────┤
│  Layer 2: SENSORY SYSTEM                                │
│  News (Alpaca), on-chain (CryptoQuant), sentiment,      │
│  macro signals. Signal aggregator (min 3 gate).         │
├─────────────────────────────────────────────────────────┤
│  Layer 1: FREQTRADE + COINGECKO                         │
│  Execution engine, TA (RSI + EMA + volume), risk mgmt,  │
│  paper trading, backtesting, 20+ exchanges via CCXT     │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
Market Data (CoinGecko) ──→ Freqtrade (candles, TA indicators)
                                │
Sensory System ─────────────────┤
├── News (Alpaca API)           │
├── On-chain (CryptoQuant)      ├──→ Signal Aggregator (min 3 gate)
├── Sentiment (keyword-based)   │         │
└── Macro (funding rates)       │         ▼
                                │    Position Sizer (1x/3x/10x, max 1% risk)
                                │         │
                                │         ▼
                                └──→ AlphaStrategy.populate_entry/exit_trend()
                                          │
                                          ▼
                                     Freqtrade Execution (dry_run: true)
                                          │
                                          ▼
                                     Autoresearch Loop
                                     (backtest → evaluate → tweak → repeat)
```

### Integration Strategy

| Upstream | Method | Extension Point |
|----------|--------|----------------|
| Freqtrade | pip dependency (not fork) | `IStrategy` subclass in `src/strategies/` |
| CoinGecko | REST API via `pycoingecko` | Market data feed |
| Alpaca News | REST API | `src/sensory/news.py` |
| CryptoQuant | REST API | `src/sensory/on_chain.py` |
| Autoresearch | Reimplemented pattern (10 files) | Locked evaluator + agent-editable strategy |
| MiroFish | Docker sidecar REST API (stub) | `src/adapters/swarm.py` |
| FinDKG | Future stub | `src/adapters/knowledge_graph.py` |

## Key Files

- [src/strategies/alpha_strategy.py](src/strategies/alpha_strategy.py) - Freqtrade IStrategy: RSI + EMA crossover + volume confirmation
- [src/sensory/](src/sensory/) - Layer 2: news, on-chain, sentiment, macro signal providers
- [src/signals/aggregator.py](src/signals/aggregator.py) - Convergence gate (min 3 uncorrelated signals to trade)
- [src/signals/position_sizer.py](src/signals/position_sizer.py) - Conviction-weighted sizing (1x/3x/10x, max 1% risk)
- [src/core/risk.py](src/core/risk.py) - PTJ rules: max 1% per trade, 10% drawdown circuit breaker
- [src/autoresearch/prepare.py](src/autoresearch/prepare.py) - **LOCKED** evaluator (Sharpe ratio, drawdown, win rate) — protected by hook
- [src/autoresearch/optimizer.py](src/autoresearch/optimizer.py) - The optimization loop: modify → backtest → evaluate → keep/discard
- [src/autoresearch/program.md](src/autoresearch/program.md) - Agent constitution (what the optimizer can/cannot change)
- [src/adapters/](src/adapters/) - Future layer stubs (MiroFish swarm, FinDKG knowledge graph)
- [config.json](config.json) - Freqtrade config (`dry_run: true`, Binance paper trading)
- [pyproject.toml](pyproject.toml) - Dependencies: freqtrade, pytest, ruff, mypy, pycoingecko, requests

## Important Conventions

### Working Style

- **Bug fixes and small tasks** (< 3 files): implement directly, no planning doc needed unless asked.
- **Features and multi-file work**: always follow DDD — plan, document, approve, then execute.
- Always run `git branch --show-current` before any git operation. Never assume which branch you're on.
- **Adapter pattern for future layers**: stubs define interfaces now so implementing later doesn't require restructuring.
- **Config over code**: enable/disable signal sources via configuration. Disable = skip that signal, don't delete the module.

### Code Quality Tooling

- **ruff** — Linting and formatting (replaces flake8 + black + isort)
- **mypy** — Static type checking (strict mode)
- **pytest** — Test runner with 30s timeout
- **Claude Code hooks** — `.claude/hooks/quality-gate.sh` runs `ruff check . && mypy . && pytest` before commits
- **Protected files hook** — `.claude/hooks/protect-files.sh` blocks edits to `.env` and `src/autoresearch/prepare.py`

### Test Configuration

- **Framework**: pytest
- **Location**: `tests/` (mirrors `src/` structure: `test_strategies/`, `test_sensory/`, `test_signals/`, `test_autoresearch/`)
- **Coverage tax**: Touch a source file with < 60% coverage AND the change is logic (not config)? Add at least one test.
- **No E2E** — Python project, no browser. Integration tests serve this purpose.
- **Zero tolerance**: All tests pass before commit. No skipped tests without documented reason.

### Autoresearch Immutability

`src/autoresearch/prepare.py` is the evaluator — the "judge" that scores strategy performance. It is **LOCKED**:
- Protected by `protect-files.sh` hook (blocks Edit/Write)
- The optimization loop can modify strategy parameters but **never** the evaluation criteria
- This follows Karpathy's autoresearch pattern: immutable `prepare.py` ensures the optimizer can't game its own scoring

## Debugging

```bash
# Freqtrade diagnostics
freqtrade test-strategy --strategy AlphaStrategy    # Verify strategy loads
freqtrade backtesting --strategy AlphaStrategy      # Run historical backtest
freqtrade show-config                               # Dump resolved config

# Check API connectivity
python -c "from pycoingecko import CoinGeckoAPI; print(CoinGeckoAPI().ping())"

# Autoresearch experiment history
cat src/autoresearch/results.tsv                    # TSV log of all optimization runs
```

## Compaction Instructions

When context is compacted, always preserve:

1. Current git branch name (run `git branch --show-current` after compaction)
2. List of modified files and their purpose
3. Active planning document path (any `docs/active/*.md` being worked on)
4. Test results from commands already run
5. Never promote to main without explicit user confirmation (use `/release`)
6. Main worktree lives on `develop` branch — `main` is production-only
7. Paper-only mandate: `dry_run: true` — no real trading without CEO approval
8. `src/autoresearch/prepare.py` is LOCKED — never edit the evaluator

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
| engineering-philosophy | `src/**/*.py`             | Deep dive protocols, code review questions       |
| document-driven-dev    | `docs/**`                 | DDD workflow, completion triggers, archival      |
| production-safety      | deployment commands       | Risk assessment, PR merge protocol               |
| git-workflow           | git commands              | Conventional commits, pre-commit checklist       |
| testing                | `tests/**`, `*.test.py`   | Test commands, coverage tax                      |
| mcp-tools              | MCP tool usage            | Tool selection, agent usage                      |
| ceo-cto-communication  | all communication         | CEO signal format, analogies, brief style        |
| autonomous-guardrails  | quality gate execution    | Anti-gaming rules for self-correction loops      |
| error-recovery         | tool/MCP failures         | Retry patterns, fallback table, escalation tiers |
| worktree-autorun       | WORKTREE.md present       | Auto-detect and execute worktree manifests       |

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

**Pipeline**: `/session-start` → `/investigate` → `/research` → `/brainstorm` → `/ux-design` → `/plan` → `/sign-off` → `/worktree create` → implement → `/code-review` → `/qa` → commit → push → PR → `/review-pr` → merge to develop → CEO tests staging → `/release` → production
**Periodic**: `/sync-docs` (after major work), `/organize` + `/hygiene` (monthly), `/wow-audit` (quarterly)
**On-demand**: `/investigate` (any time — codebase questions, pre-change understanding, drift detection), `/self-optimize` (when time allows — experimental autonomous optimization)
**Observations**: When you notice patterns, smells, or potential issues during work — append to `memory/observations.md`. CEO reviews periodically.
**Memory architecture**: System 1 (fast files: MEMORY.md, intuitions.md, rules/) + System 2 (slow skills: /investigate, /research, /plan). Bridge: observations.md → /coffee-break → graduation to System 1 files.

## Status

See [PRODUCTION_READINESS_ROADMAP.md](docs/PRODUCTION_READINESS_ROADMAP.md) for current status.
