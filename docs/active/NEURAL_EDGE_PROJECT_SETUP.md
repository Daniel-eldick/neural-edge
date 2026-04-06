# NeuralEdge — Project Setup & Weekend 1

**Status**: 🔧 DEVELOPMENT (53%) | **Tier**: 🟡 Standard | **Risk**: Low (greenfield, paper-only)
**Created**: 2026-04-05

## 1. What & Why

**Problem**: We want to build a multi-layer AI trading bot that combines traditional technical analysis with autonomous strategy optimization, real-time market intelligence, and (future) swarm prediction — but we need the project scaffold before we can build anything.

**Solution**: Create the NeuralEdge repo at `~/Projects/neural-edge/`, scaffold it with the simplrr-framework dev OS, configure for a Python + Freqtrade stack, and set up the 5-layer architecture stubs. Then build the Weekend 1 deliverables: Freqtrade running paper trades with a classic strategy + sensory system wired up + autoresearch loop optimizing overnight.

**Business value**: A working paper-trading bot by end of Weekend 1, with the full simplrr-framework workflow (DDD, skills, quality gates) governing development from day one.

## 2. Solution Design

### Architecture: The 5-Layer Cake

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
│  Layer 2: SENSORY SYSTEM (Weekend 1)                    │
│  News (Alpaca), on-chain (CryptoQuant), basic sentiment │
│  macro signals (funding rates, flows). FinGPT deferred. │
├─────────────────────────────────────────────────────────┤
│  Layer 1: FREQTRADE + COINGECKO (Weekend 1)             │
│  Execution, TA, risk management, paper trading          │
│  20+ exchanges via CCXT, backtesting, Telegram bot      │
└─────────────────────────────────────────────────────────┘
```

### Integration Strategy

| Upstream | Integration Method | Why |
|----------|-------------------|-----|
| simplrr-framework | `/simplrr-framework init` → fill markers | Dev OS scaffolding, `/framework-sync pull` for updates |
| Freqtrade | `pip install freqtrade` (requires `ta-lib` C library — compiled from source to `~/.local`) | Standalone app used as dependency — strategies are Python classes in `src/strategies/`. Docker alternative available for portability. |
| autoresearch | Reimplement pattern (not fork) | Only 10 files, it's a methodology not a library |
| MiroFish | Docker sidecar (Weekend 2+) | Full-stack app, call REST API for predictions |
| CoinGecko | REST API (via `pycoingecko`) | Market data, no fork needed |
| Alpaca News | REST API | Financial news feed |

### Key Design Decisions

1. **Freqtrade as pip dependency** — not a fork. Requires `ta-lib` C library (compiled from source to `~/.local` — Homebrew unavailable). Their `IStrategy` interface is the extension point. We write strategies, they handle exchange connectivity + risk + backtesting. Docker alternative (`docker-compose.yml`) provided for portability.
2. **Autoresearch reimplemented** — the core pattern is: locked evaluator + agent-editable strategy + git-tracked experiments + fixed time budget. We build this natively.
3. **Adapter pattern for future layers** — `src/adapters/swarm.py` and `src/adapters/knowledge_graph.py` are stubs with defined interfaces. When MiroFish/FinDKG time comes, we implement the interface without restructuring.
4. **No real money** — `dry_run: true` in Freqtrade config. This is non-negotiable until explicit CEO approval.

### Repo Structure

```
~/Projects/neural-edge/
├── .claude/                          # simplrr-framework dev OS
│   ├── rules/                        # 10 core framework rules (+ 2 trading-specific rules created in Phase 4)
│   ├── skills/                       # 23 core skills (no modules activated)
│   ├── hooks/                        # Git safety + quality gate (adapted for Python in Phase 0)
│   ├── references/
│   ├── settings.local.json           # MCP config (no Supabase/DevTools)
│   ├── landmines.md
│   └── coffee-notes.md
├── CLAUDE.md                         # Adapted for Python + Freqtrade + trading
├── .framework-manifest.json          # Framework tracking
├── docs/                             # DDD workflow
│   ├── active/
│   ├── completed/
│   ├── guides/
│   ├── INCOMPLETE_FEATURES.md
│   ├── TECHNICAL_DEBT.md
│   ├── BACKLOG.md
│   ├── PRODUCTION_READINESS_ROADMAP.md
│   └── README.md
├── memory/                           # Auto-memory
│   ├── MEMORY.md
│   ├── observations.md
│   ├── intuitions.md
│   └── knowledge-map.md
├── src/                              # Our code
│   ├── strategies/                   # Freqtrade strategy classes
│   │   ├── __init__.py
│   │   └── alpha_strategy.py         # Layer 1: Classic TA (RSI + EMA + volume)
│   ├── sensory/                      # Layer 2: Market intelligence
│   │   ├── __init__.py
│   │   ├── news.py                   # Alpaca News API integration
│   │   ├── on_chain.py               # CryptoQuant/Glasschain data
│   │   ├── sentiment.py              # Basic keyword sentiment (FinGPT fine-tuning deferred to BACKLOG)
│   │   └── macro.py                  # Funding rates, stablecoin flows
│   ├── signals/                      # Signal convergence engine
│   │   ├── __init__.py
│   │   ├── aggregator.py             # Min 3 signals gate
│   │   └── position_sizer.py         # Conviction-weighted sizing (1x/3x/10x)
│   ├── autoresearch/                 # Layer 5: Optimization loop
│   │   ├── __init__.py
│   │   ├── prepare.py                # LOCKED: evaluation metrics (Sharpe, drawdown)
│   │   ├── program.md                # Agent constitution
│   │   ├── optimizer.py              # The autonomous loop
│   │   └── results.tsv               # Experiment log
│   ├── adapters/                     # Future layer interfaces
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract adapter interface
│   │   ├── swarm.py                  # MiroFish adapter (stub)
│   │   └── knowledge_graph.py        # FinDKG adapter (stub)
│   └── core/                         # Shared utilities
│       ├── __init__.py
│       ├── config.py                 # Configuration management
│       └── risk.py                   # PTJ rules: max 1% risk, circuit breaker
├── user_data/                        # Freqtrade convention
│   ├── strategies/                   # Empty — config.json points strategy_path to src/strategies/ directly
│   ├── data/                         # Historical candle data
│   ├── backtest_results/
│   └── notebooks/
├── tests/                            # pytest suite
│   ├── conftest.py
│   ├── test_core/
│   ├── test_strategies/
│   ├── test_sensory/
│   ├── test_signals/
│   └── test_autoresearch/
├── config.json                       # Freqtrade config (dry_run: true)
├── docker-compose.yml                # Dev: Freqtrade (future: MiroFish sidecar)
├── pyproject.toml                    # Python packaging (ruff, mypy, pytest)
├── .env.example                      # API keys template
├── .gitignore
└── README.md
```

### CLAUDE.md Key Adaptations

| Section | Simplrr (original) | NeuralEdge (adapted) |
|---------|--------------------|--------------------|
| Stack | React + TS + Vite + Supabase | Python 3.11+ + Freqtrade + LLMs |
| Production | simplrr.app (Vercel) | Not deployed — paper trading only |
| Commands | npm run dev, npm test | freqtrade trade, pytest, ruff |
| Quality gate | npm run quality:check | ruff check + mypy + pytest |
| Architecture | Restaurant ordering flow | 5-layer trading architecture |
| MCP tools | Supabase + Chrome DevTools | None initially (future: exchange APIs?) |
| Modules | supabase, devtools, legal, content, perf | None initially |
| Mandate #5 (perf) | Lebanon 1-5 Mbps | API rate limits (CoinGecko 30/min, Alpaca 200/min) |
| Mandate #8 (UX) | Restaurant owner during lunch rush | "If the bot can't explain WHY it made a trade in one sentence, the signal logic is wrong" |
| Rules triggers | `src/**/*.ts(x)` | `src/**/*.py` |

### Hook Adaptations

| Hook | Simplrr | NeuralEdge |
|------|---------|-----------|
| `block-dangerous.sh` | Block push to main, force push, reset --hard | Same (universal git safety) |
| `protect-files.sh` | Block .env, package-lock.json | Block .env, `src/autoresearch/prepare.py` (immutable evaluator), `poetry.lock`/`uv.lock` |
| `quality-gate.sh` | `npx tsc --noEmit` | `ruff check . && mypy . && pytest -x --timeout=30` |

### Trading-Specific Rules to Add

1. **`paper-only-mandate.md`** — Block any config with `dry_run: false`. Only CEO can authorize real trading.
2. **`api-key-safety.md`** — Never hardcode API keys. All keys in `.env`. Block commits containing key patterns.

## 3. Tasks

### Phase 0: Repo Bootstrap (no tests — scaffolding only)

| # | Task | Status |
|---|------|--------|
| 1 | Create `~/Projects/` directory | [x] |
| 2 | Fork simplrr-framework template repo → `neural-edge` on GitHub | [x] |
| 3 | Clone to `~/Projects/neural-edge/` | [x] |
| 4 | Fill all CLAUDE.md markers for Python + Freqtrade + trading context | [x] |
| 5a | Adapt `quality-gate.sh`: replace `npx tsc --noEmit` with `ruff check . && mypy . && pytest -x --timeout=30` | [x] |
| 5b | Adapt `protect-files.sh`: replace `package-lock.json` block with `src/autoresearch/prepare.py` block | [x] |
| 5c | Adapt `block-dangerous.sh`: remove FILL comment (functional logic already correct) | [x] |
| 5d | Fill remaining adapter file markers (rules, settings, docs) | [x] |
| 6 | Create `.gitignore` adapted for Python (`.venv/`, `__pycache__/`, `.env`, `user_data/data/`, `results.tsv`) | [x] |
| 7 | Create `pyproject.toml` with dependencies (freqtrade, pytest, ruff, mypy, pycoingecko, requests) | [x] |
| 8 | Create Python project structure (`src/` with all `__init__.py` files, `tests/conftest.py`) | [x] |
| 9 | Install `ta-lib` C library (compiled from source to `~/.local`) — required by Freqtrade | [x] |
| 10 | Set up virtual environment + install dependencies (`uv venv --python 3.12` + `uv pip install -e ".[dev]"`) | [x] |
| 11 | Create Freqtrade config (`config.json` with `dry_run: true`, Binance paper trading) | [x] |
| 12 | Create `.env.example` with all expected API key placeholders (Alpaca, CryptoQuant, CoinGecko, OpenAI) | [x] |
| 13 | Create `README.md` — project overview, setup instructions, architecture diagram | [x] |
| 14 | Initialize git, first commit, push to GitHub | [x] |
| 15 | Create `develop` branch, set as default | [x] |
| 16 | Verify: `ruff check .` passes, `mypy .` passes, framework markers are filled | [x] |

### Phase 1: Layer 1 — Freqtrade + Classic Strategy (Saturday AM)

| # | Task | Test approach | Status |
|---|------|--------------|--------|
| 0 | Write failing tests for Alpha Strategy behavior | `tests/test_strategies/test_alpha_strategy.py` — strategy loads, generates signals on sample data, respects risk limits | [x] |
| 1 | Create `src/strategies/alpha_strategy.py` — IStrategy class with RSI + EMA crossover + volume confirmation | Test from task 0 passes: strategy generates buy/sell signals | [x] |
| 2 | Create `src/core/risk.py` — max 1% per trade, drawdown circuit breaker (10%), conviction sizing (1x/3x/10x) | `tests/test_core/test_risk.py` — position sizes respect limits, circuit breaker triggers | [x] |
| 3 | Wire strategy to Freqtrade — `strategy_path: src/strategies` in config.json, `freqtrade list-strategies` shows OK | Manual: `freqtrade backtesting --strategy AlphaStrategy` runs without error | [x] |
| 4 | Run first backtest — BTC/ETH/SOL Jun-Aug 2024, baseline: 1 trade, -0.14% (very conservative RSI<30 filter) | Backtest completed, results stored in `user_data/backtest_results/` | [x] |

### Phase 2: Layer 2 — Sensory System (Saturday PM)

| # | Task | Test approach | Status |
|---|------|--------------|--------|
| 0 | Write failing tests for sensory modules | `tests/test_sensory/` — each module returns structured signals, handles API errors gracefully | [ ] |
| 1 | Create `src/sensory/news.py` — Alpaca News API integration (crypto news, structured as signals) | Test: returns list of `NewsSignal` objects with sentiment score, passes on API error | [ ] |
| 2 | Create `src/sensory/on_chain.py` — CryptoQuant/Glasschain funding rates + exchange flows | Test: returns `OnChainSignal` with direction + confidence, handles rate limits | [ ] |
| 3 | Create `src/sensory/sentiment.py` — basic keyword sentiment scoring on news headlines (FinGPT fine-tuning deferred to BACKLOG) | Test: returns `SentimentSignal` with score [-1, 1], handles empty input | [ ] |
| 4 | Create `src/sensory/macro.py` — stablecoin flows, funding rate aggregation | Test: returns `MacroSignal`, handles missing data | [ ] |
| 5 | Create `src/signals/aggregator.py` — convergence gate (min 3 uncorrelated signals to trade) | Test: blocks trade on < 3 signals, allows on >= 3, weights by confidence | [ ] |
| 6 | Create `src/signals/position_sizer.py` — conviction-weighted sizing (weak=1x, moderate=3x, strong=10x, max 1% risk) | Test: sizing respects max risk, scales with signal strength | [ ] |
| 7 | Integrate sensory signals into AlphaStrategy — strategy queries sensory system before executing | Test: strategy consults signals aggregator, trades only when convergence gate passes | [ ] |

### Phase 3: Layer 5 — Autoresearch Loop (Sunday)

| # | Task | Test approach | Status |
|---|------|--------------|--------|
| 0 | Write failing tests for autoresearch loop | `tests/test_autoresearch/` — evaluator is immutable, loop tracks experiments, keeps improvements | [ ] |
| 1 | Create `src/autoresearch/prepare.py` — LOCKED evaluator: runs backtest, computes Sharpe ratio + max drawdown + win rate | Test: evaluator produces consistent metrics on same data, file is marked read-only | [ ] |
| 2 | Create `src/autoresearch/program.md` — agent constitution: rules, constraints, what can be changed | Manual verification: document reviewed by CEO | [ ] |
| 3 | Create `src/autoresearch/optimizer.py` — the loop: read program.md → modify strategy params → backtest → evaluate → keep/discard → log to results.tsv → repeat | Test: loop executes one cycle, logs result, reverts on worse performance | [ ] |
| 4 | Run overnight: let autoresearch optimize AlphaStrategy for 50+ iterations | Manual: review results.tsv for improvements, check git log for experiment branches | [ ] |

### Phase 4: Adapter Stubs + Polish (Sunday PM)

| # | Task | Test approach | Status |
|---|------|--------------|--------|
| 1 | Create `src/adapters/base.py` — abstract `PredictionAdapter` interface | Test: interface defines `predict()`, `health_check()`, `confidence()` | [ ] |
| 2 | Create `src/adapters/swarm.py` — MiroFish stub (returns neutral prediction + "not connected" health) | Test: stub returns valid response, health_check returns False | [ ] |
| 3 | Create `src/adapters/knowledge_graph.py` — FinDKG stub | Test: same pattern as swarm stub | [ ] |
| 4 | Create trading-specific rules: `paper-only-mandate.md`, `api-key-safety.md` | Verification: rules load correctly, protect-files hook blocks prepare.py edits | [ ] |
| 5 | Create `docker-compose.yml` — Freqtrade service (paper mode) | Manual: `docker compose up` starts Freqtrade | [ ] |
| 6 | Seed `docs/INCOMPLETE_FEATURES.md` — layers 3+4, real trading, more exchanges | N/A |
| 7 | Seed `docs/BACKLOG.md` — FinGPT fine-tuning, knowledge graph, Polymarket integration | N/A |
| 8 | Final verification: `ruff check . && mypy . && pytest` all pass | Automated |

**Scope guard**: 45 tasks across 5 phases. Stop if > 67.

## 4. Files & Blast Radius

This is a greenfield project — no existing files affected. All files are CREATE.

| File/Directory | Action | Layer | Regression Risk |
|---------------|--------|-------|----------------|
| `CLAUDE.md` | Create (from template) | Framework | Low (new project) |
| `.claude/rules/*.md` | Create (fill markers) | Framework | Low |
| `.claude/hooks/*.sh` | Create (adapt for Python) | Framework | Low |
| `src/strategies/alpha_strategy.py` | Create | Layer 1 | N/A |
| `src/sensory/*.py` | Create | Layer 2 | N/A |
| `src/signals/*.py` | Create | Signal engine | N/A |
| `src/autoresearch/*.py` | Create | Layer 5 | N/A |
| `src/adapters/*.py` | Create | Future stubs | N/A |
| `src/core/*.py` | Create | Shared | N/A |
| `tests/**` | Create | Testing | N/A |
| `config.json` | Create | Freqtrade config | N/A |
| `pyproject.toml` | Create | Packaging | N/A |
| `docker-compose.yml` | Create | Dev environment | N/A |

## 5. Test Plan

**CRITICAL-07 rule**: Every test must have a specific, measurable assertion.

**E2E specs**: None — this is a Python project, no browser E2E. Integration tests serve this purpose.

| What to verify | Type | Status |
|---------------|------|--------|
| AlphaStrategy generates buy signal on RSI < 30 + EMA crossover + volume spike | Unit | [x] |
| AlphaStrategy generates sell signal on RSI > 70 + EMA crossover down | Unit | [x] |
| Risk module caps position at 1% of portfolio | Unit | [x] |
| Risk module triggers circuit breaker at 10% drawdown | Unit | [x] |
| Position sizer scales 1x/3x/10x based on signal count | Unit | [ ] |
| Signal aggregator blocks trade on < 3 signals | Unit | [ ] |
| Signal aggregator allows trade on >= 3 uncorrelated signals | Unit | [ ] |
| News module returns structured `NewsSignal` on API success | Unit | [ ] |
| News module returns empty list on API error (no crash) | Unit | [ ] |
| On-chain module handles rate limits gracefully | Unit | [ ] |
| Sentiment module returns score in [-1, 1] range on valid input | Unit | [ ] |
| Sentiment module returns neutral (0) on empty input | Unit | [ ] |
| Autoresearch evaluator produces consistent Sharpe on same data | Unit | [ ] |
| Autoresearch loop keeps improving strategy, discards regressions | Integration | [ ] |
| Autoresearch loop logs every experiment to results.tsv | Integration | [ ] |
| `freqtrade list-strategies` shows AlphaStrategy with Status OK | Manual | [x] |
| `freqtrade backtesting --strategy AlphaStrategy` completes | Manual | [x] |
| `ruff check . && mypy . && pytest` all pass (quality gate) | Automated | [x] |
| Zero FILL markers remain in CLAUDE.md and adapter files | Automated | [x] |
| `protect-files.sh` hook blocks edits to `src/autoresearch/prepare.py` | Manual | [ ] |
| `config.json` with `dry_run: false` is flagged by `paper-only-mandate.md` rule | Manual | [ ] |

## 6. Rollback

**Risk**: Zero. This is a greenfield project. If anything goes wrong:
- Delete `~/Projects/neural-edge/` and start over
- No production system affected
- No database to corrupt
- Paper trading only — no financial risk

**Time to rollback**: 30 seconds (`rm -rf ~/Projects/neural-edge/`)

---

### Landmine Check

> Most Simplrr landmines are irrelevant (Supabase, offline, React). Relevant ones:

- **#1 (API keys)**: `.env` for all API keys, never hardcode. `.env.example` as template.
- **Autoresearch immutability**: `prepare.py` is the evaluator — must be protected by `protect-files.sh` hook.

### Engineering Check

- [x] What happens when this fails? → Paper trading, lose fake money. Sensory APIs fail gracefully (empty signals, not crashes).
- [x] N+1 query risk? → No database. API calls are batched by design.
- [x] Can this be feature-flagged? → Yes — each layer is an adapter. Disable = skip that signal source. `dry_run: true` is the ultimate flag.

## Progress Log

| Date | Update | % |
|------|--------|---|
| 2026-04-05 | Created plan | 0% |
| 2026-04-05 | Phase 0 complete — all 19 bootstrap tasks done. uv + Python 3.12 + ta-lib (compiled from source). Quality gate green. | 42% |
| 2026-04-06 | Phase 1 complete — AlphaStrategy (RSI+EMA+volume), risk.py (PTJ rules), 43 tests passing, first backtest run (1 trade, -0.14% on Jun-Aug 2024). Quality gate green. | 53% |
