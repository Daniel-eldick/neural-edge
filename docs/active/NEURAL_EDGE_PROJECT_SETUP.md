# NeuralEdge — Project Setup & Weekend 1

**Status**: 🔧 DEVELOPMENT (58%) | **Tier**: 🟡 Standard | **Risk**: Low (greenfield, paper-only)
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

### Autoresearch Interface Contract (Phase 3)

The autoresearch loop has two locked boundaries: the evaluator (`prepare.py`) and the editable parameter space. These are defined here so Phase 3 implementation has no ambiguity.

**`src/autoresearch/prepare.py` — locked evaluator interface**

```python
from dataclasses import dataclass
from src.strategies.alpha_strategy import AlphaStrategy

@dataclass(frozen=True)
class EvalMetrics:
    sharpe_ratio: float        # primary score, higher = better
    max_drawdown_pct: float    # secondary, lower = better
    win_rate: float            # tertiary, higher = better
    total_trades: int          # sanity check — reject runs with < 20 trades
    total_return_pct: float    # absolute return
    timestamp: str             # ISO-8601 of eval run

def evaluate(strategy_cls: type[AlphaStrategy], config_path: str = "config.json") -> EvalMetrics:
    """Run a backtest on the fixed evaluation window and return metrics.

    The evaluation window, pair list, and timeframe are hardcoded constants
    inside this file and MUST NOT be parameterized — that's the whole point
    of the locked evaluator (optimizer can't game the scoring by picking
    favorable windows).
    """
```

**Locked constants inside `prepare.py`** (not editable by the optimizer):
- `EVAL_START = "20240601"`, `EVAL_END = "20240831"` (Jun-Aug 2024 — same window as Phase 1 baseline)
- `EVAL_PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]`
- `EVAL_TIMEFRAME = "1h"`
- `MIN_TRADES_FOR_VALID_EVAL = 20`

**Editable parameter space** (defined in `program.md`, enforced by `optimizer.py`):

| Parameter | Type | Range | Rationale |
|-----------|------|-------|-----------|
| `rsi_period` | int | [7, 21] | Standard RSI lookback range |
| `rsi_oversold` | int | [20, 35] | Entry threshold |
| `rsi_overbought` | int | [65, 80] | Exit threshold |
| `ema_fast` | int | [8, 21] | Fast EMA for crossover |
| `ema_slow` | int | [21, 55] | Slow EMA (must be > ema_fast, enforced by optimizer) |
| `volume_mult` | float | [1.0, 3.0] | Volume spike multiplier vs rolling average |

**Out of scope for the optimizer** (hard-coded in `alpha_strategy.py`, cannot be mutated):
- Position sizing rules (`src/core/risk.py` — PTJ 1% max, circuit breaker)
- Stop-loss logic
- The structure of the strategy (entry = state, exit = crossover — Phase 1 hardening decision)

The optimizer mutates parameters in-place on a copy of the strategy class and runs `prepare.evaluate()` on the mutant. No file editing, no AST rewriting. This prevents the optimizer from ever touching `prepare.py` directly (defense in depth alongside the `protect-files.sh` hook).

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

**Mocking convention**: All sensory unit tests use the [`responses`](https://github.com/getsentry/responses) library to mock `requests`-based HTTP calls. This is the default for any `requests` user and keeps mocking consistent across providers. Added to `pyproject.toml` dev dependencies in Task 0.

**Scope note**: Also create `tests/test_sensory/__init__.py` and `tests/test_signals/__init__.py` in Task 0 for consistency with `test_strategies/` and `test_core/`.

**TDD red-state convention (Task 0 → Tasks 2-5)**: Behaviour tests against unimplemented stubs are marked with `@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="Phase 2 Task N: ...")` so the `quality-gate.sh` hook stays green on develop. When a Task implements its module, the xfailed tests start passing → `strict=True` flips XPASS to FAIL → forces the implementer to remove the marker (self-healing red state). Frozen-dataclass immutability tests are NOT xfailed — the dataclass contracts are already locked in the Task 0 skeletons.

| # | Task | Test approach | Status |
|---|------|--------------|--------|
| 0 | Write failing tests for sensory modules + add `responses` to dev dependencies | `tests/test_sensory/` — each module returns structured signals, handles API errors gracefully, all HTTP calls mocked via `responses` | [x] |
| 1 | Create `src/core/api_client.py` — shared HTTP wrapper with TTL cache (keyed by `(provider, endpoint, params)`) + per-provider rate-limit token bucket (CoinGecko 30/min, Alpaca 200/min, CryptoQuant per plan). All sensory modules MUST route through this client. | `tests/test_core/test_api_client.py` — cache hit returns without HTTP call (verified with `responses.assert_all_requests_are_fired=False`), rate limiter blocks 31st request in 60s window, TTL expiry forces refetch | [x] |
| 2 | Create `src/sensory/news.py` — Alpaca News API integration via `api_client` (crypto news, structured as signals) | Test: returns list of `NewsSignal` objects with sentiment score, returns empty list on API error (no crash), no direct `requests.get` calls | [ ] |
| 3 | Create `src/sensory/on_chain.py` — CryptoQuant/Glasschain funding rates + exchange flows via `api_client` | Test: returns `OnChainSignal` with direction + confidence; on 429 rate-limit response, returns empty list and logs warning (verify with caplog) | [ ] |
| 4 | Create `src/sensory/sentiment.py` — basic keyword sentiment scoring on news headlines (FinGPT fine-tuning deferred to BACKLOG) | Test: returns `SentimentSignal` with score in `[-1, 1]` range on non-empty headline list, returns `SentimentSignal(score=0.0)` on empty input | [ ] |
| 5 | Create `src/sensory/macro.py` — stablecoin flows, funding rate aggregation via `api_client` | Test: returns `MacroSignal` on valid data, returns empty list when all underlying endpoints fail | [ ] |
| 6 | Create `src/signals/aggregator.py` — convergence gate (min 3 uncorrelated signals to trade) | Test: blocks trade on < 3 signals, allows on >= 3, weights by confidence, dedupes correlated signals | [ ] |
| 7 | Create `src/signals/position_sizer.py` — conviction-weighted sizing (weak=1x, moderate=3x, strong=10x, max 1% risk) | Test: sizing respects max risk, scales with signal strength | [ ] |
| 8 | Integrate sensory signals into AlphaStrategy — aggregator called inside `populate_entry_trend` (NOT per tick — once per candle close, cached via `api_client`) | Integration test: strategy consults aggregator, trades only when convergence gate passes; end-to-end test with 4 mocked sensory responses → aggregator → strategy → expected entry/exit decision | [ ] |

### Phase 3: Layer 5 — Autoresearch Loop (Sunday)

**See Solution Design § Autoresearch Interface Contract** for the locked `prepare.py` signature, the editable parameter space, and out-of-scope items. Phase 3 implements that contract — do not deviate from it.

| # | Task | Test approach | Status |
|---|------|--------------|--------|
| 0 | Write failing tests for autoresearch loop + `tests/test_autoresearch/__init__.py` | `tests/test_autoresearch/` — evaluator is immutable, loop tracks experiments, keeps improvements, optimizer cannot bypass evaluator | [ ] |
| 1 | Create `src/autoresearch/prepare.py` — LOCKED evaluator per interface contract: `evaluate(strategy_cls, config_path) -> EvalMetrics`. Uses hardcoded `EVAL_START/END/PAIRS/TIMEFRAME`. Invokes Freqtrade backtesting programmatically (see: `freqtrade.optimize.backtesting.Backtesting`, not subprocess — subprocess is fallback if programmatic API is unstable). | Test: evaluator produces consistent metrics on identical strategy + data (byte-equal `EvalMetrics` across 2 runs); evaluator raises `ValueError` if `total_trades < MIN_TRADES_FOR_VALID_EVAL`; file is blocked from editing by `protect-files.sh` (manual verification) | [ ] |
| 2 | Create `src/autoresearch/program.md` — agent constitution: enumerates the editable parameter space (copy from Solution Design table), hard constraints (`ema_slow > ema_fast`), and forbidden actions (no edits to `prepare.py`, `risk.py`, `alpha_strategy.py` structure) | Manual verification: document reviewed by CEO; matches the Solution Design table exactly | [ ] |
| 3 | Create `src/autoresearch/optimizer.py` — the loop: parse `program.md` → sample a mutation from parameter space → clone `AlphaStrategy` → apply params to clone → call `prepare.evaluate(clone)` → compare `sharpe_ratio` vs current best → keep on improvement, discard on regression → append row to `results.tsv` → repeat. Uses in-memory mutation on a cloned class, never file edits. | Test: one cycle executes and logs a row to `results.tsv`; regression is discarded (best unchanged); monkey-patching `prepare.evaluate` raises / is detected (see Test Plan — optimizer tampering test); `ema_slow > ema_fast` constraint is enforced (invalid mutations rejected before backtest) | [ ] |
| 4 | Run overnight: let autoresearch optimize AlphaStrategy for 50+ iterations | Manual: review `results.tsv` for improvements; sanity-check that the best params aren't wildly overfit (e.g., `rsi_oversold=34` with 19 trades → suspicious) | [ ] |

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

**Scope guard**: 43 tasks across 5 phases (Phase 0: 16, Phase 1: 5, Phase 2: 9, Phase 3: 5, Phase 4: 8). Stop if > 65.

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

**CRITICAL-07 rule**: Every test must have a specific, measurable assertion. "Handles gracefully" is not an assertion — specify the exact behavior (empty list? typed exception? logged warning?).

**E2E specs**: None — this is a Python project, no browser E2E. Integration tests serve this purpose.

**HTTP mocking**: All sensory unit tests use the `responses` library. No `unittest.mock.patch` on `requests` — too fragile.

| What to verify | Type | Status |
|---------------|------|--------|
| AlphaStrategy generates buy signal on RSI < 30 + EMA crossover + volume spike | Unit | [x] |
| AlphaStrategy generates sell signal on RSI > 70 + EMA crossover down | Unit | [x] |
| Risk module caps position at 1% of portfolio | Unit | [x] |
| Risk module triggers circuit breaker at 10% drawdown | Unit | [x] |
| `api_client` TTL cache: 2nd identical request within TTL returns without HTTP call | Unit | [x] |
| `api_client` rate limiter: 31st CoinGecko request in 60s window blocks (raises or sleeps) | Unit | [x] |
| `api_client` TTL expiry forces refetch after window | Unit | [x] |
| Position sizer scales 1x/3x/10x based on signal count | Unit | [ ] |
| Position sizer respects `MAX_RISK_PER_TRADE` hard cap even with override | Unit | [x] |
| Signal aggregator blocks trade on < 3 signals | Unit | [ ] |
| Signal aggregator allows trade on >= 3 uncorrelated signals | Unit | [ ] |
| Signal aggregator dedupes correlated signals from same provider family | Unit | [ ] |
| News module returns structured `NewsSignal` on API success (mocked via `responses`) | Unit | [ ] |
| News module returns empty list on API error (500/timeout, no crash) | Unit | [ ] |
| On-chain module returns empty list + logs warning on 429 rate-limit response (verify with `caplog`) | Unit | [ ] |
| Sentiment module returns score in `[-1, 1]` range on valid input | Unit | [ ] |
| Sentiment module returns `SentimentSignal(score=0.0)` on empty input | Unit | [ ] |
| Macro module returns empty list when all underlying endpoints fail | Unit | [ ] |
| **Integration**: Full pipeline with 4 mocked sensory responses → aggregator (≥3 converge) → AlphaStrategy → expected buy signal produced | Integration | [ ] |
| **Integration**: Full pipeline with 2 mocked signals → aggregator blocks → no trade | Integration | [ ] |
| Autoresearch evaluator produces byte-equal `EvalMetrics` on same strategy + data (determinism) | Unit | [ ] |
| Autoresearch evaluator raises `ValueError` when `total_trades < MIN_TRADES_FOR_VALID_EVAL` | Unit | [ ] |
| Autoresearch optimizer: monkey-patching `prepare.evaluate` in-process raises or is detected (tamper check) | Unit | [ ] |
| Autoresearch optimizer enforces `ema_slow > ema_fast` constraint (invalid mutations rejected pre-backtest) | Unit | [ ] |
| Autoresearch loop keeps improving strategy, discards regressions | Integration | [ ] |
| Autoresearch loop logs every experiment to `results.tsv` (one row per iteration) | Integration | [ ] |
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

**Phase 3 data side-effect note**: `src/autoresearch/results.tsv` accumulates one row per optimization iteration. If the parameter space or evaluation window in `prepare.py` changes after the optimizer has already been run, prior rows become invalid (different search surface / different scoring). In that case: `rm src/autoresearch/results.tsv` before re-running, and git-commit the wipe so experiment history is unambiguous. The file is in `.gitignore` by Phase 0 task 6, so accidental commits are already blocked.

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
| 2026-04-05 | Phase 0 complete — all 16 bootstrap tasks done. uv + Python 3.12 + ta-lib (compiled from source). Quality gate green. | 42% |
| 2026-04-06 | Phase 1 complete — AlphaStrategy (RSI+EMA+volume), risk.py (PTJ rules), 43 tests passing, first backtest run (1 trade, -0.14% on Jun-Aug 2024). Quality gate green. | 53% |
| 2026-04-06 | Phase 1 hardening — `/code-review` → `/qa` pipeline. 3 MEDIUM findings fixed: (1) alpha_strategy docstrings now match code (entry = EMA *state*, exit = EMA *crossover* — asymmetry documented as intentional); (2) `CONVICTION_MULTIPLIERS` wrapped in `MappingProxyType` so runtime mutation raises `TypeError`; (3) `PositionSizer.calculate()` enforces a hard cap — override above `MAX_RISK_PER_TRADE` can no longer exceed `portfolio * 0.01 * max_multiplier` (defense in depth against the future optimizer). +2 tests (45 total). Quality gate green. | 53% |
| 2026-04-06 | Sign-off round 1 (Standard, 7.0/10 GO WITH NOTES) → plan hardening for Phases 2-4: (1) added `api_client.py` shared HTTP wrapper with TTL cache + rate-limit token bucket as Phase 2 Task 1 (prevents N+1 against CoinGecko/Alpaca); (2) added Autoresearch Interface Contract to Solution Design — locked `prepare.py` signature, `EvalMetrics` dataclass, hardcoded eval window, explicit editable parameter space table; (3) sensory tests now mandate `responses` library; (4) added integration tests (full pipeline) + optimizer tamper test + constraint test to Test Plan; (5) Rollback notes `results.tsv` wipe policy; (6) reconciled task counts (43 total). Task count: 42 → 43 (+1 caching task). | 53% |
| 2026-04-06 | Sign-off round 2 (Standard, 8.7/10 GO — scores: Accuracy 9, Completeness 9, Clarity 9, Blast Radius 8, Test Quality 9, Rollback 8). All 8 spot-checks confirmed. 0 must-fix, 5 non-blocking suggestions deferred to later iteration. | 53% |
| 2026-04-06 | Phase 2 Task 0 complete — `responses>=0.25.0` added to dev deps; `tests/test_sensory/__init__.py` + `tests/test_signals/__init__.py` created; 4 failing test files (`test_news.py`, `test_on_chain.py`, `test_sentiment.py`, `test_macro.py`) pinning dataclass contracts + behavioural assertions (17 tests total); minimal module skeletons in `src/sensory/{news,on_chain,sentiment,macro}.py` exposing frozen dataclasses with functions raising `NotImplementedError` so mypy stays green while pytest correctly reports the 17 unimplemented behaviours as red. Quality gate: ruff ✅, mypy ✅ (26 files), pytest 49 passed + 17 failed (all NotImplementedError — the expected TDD red state). Ready for Task 1 (api_client). | 55% |
| 2026-04-06 | Phase 2 Task 0 hardening via `/code-review` — found HIGH finding H1: the 17 red-state tests broke the `quality-gate.sh` always-green invariant on develop. Self-corrected with `@pytest.mark.xfail(raises=NotImplementedError, strict=True, reason="Phase 2 Task N: ...")` on all 17 behaviour tests; kept the 4 frozen-dataclass immutability tests unmarked (they pass green). Self-healing: when Tasks 2-5 land, xfail → XPASS → strict mode forces marker removal. Also fixed M3 (renamed `test_fetch_news_..._on_timeout` → `..._on_connection_error` with honest docstring — `responses` can't distinguish connection errors from timeouts at mock layer) and L2 (added Task 3 logger-name guidance comment so `caplog` filter `logger="src.sensory.on_chain"` matches). Quality gate: ruff ✅, mypy ✅, pytest **49 passed + 17 xfailed** (exit 0). Fresh-eyes G2 re-review: APPROVED — all 7 verification checks passed with concrete evidence, no regressions. Ready for Task 1 (api_client). | 55% |
| 2026-04-06 | Sign-off round 3 (Standard, 8.86/10 GO — scores: Accuracy 9, Completeness 9, Clarity 9, Blast Radius 9, Test Quality 9, Rollback 8, Implementation Readiness 9). All 9 spot-checks confirmed. 0 must-fix, 6 non-blocking suggestions (sensory-during-backtest behaviour, `api_client` public surface naming, rate-limit-behaviour choice, Phase 3 tamper detection mechanism, Task 8 regression check, Task 8 position-sizer call sub-bullet) — addressed inline during Task 1 design. | 55% |
| 2026-04-06 | Phase 2 Task 1 complete — `src/core/api_client.py`: `APIClient.get(*, provider, url, params, ttl_seconds, headers)` single entry point; TTL cache keyed by `(provider, url, sorted_params)`; sliding-window token bucket per provider (CoinGecko 30/min, Alpaca 200/min, CryptoQuant 10/min conservative default); **raises `RateLimitError`** on bucket-empty (no silent sleeps — the Fail Loudly mandate wins over convenience). Threading.Lock guards state but is released across HTTP I/O so one slow call can't stall concurrent sensory callers. Clock + session injected for deterministic tests. 5 tests in `tests/test_core/test_api_client.py`: cache hit no-wire, TTL expiry forces refetch, 31st CoinGecko call raises pre-wire, 60s window roll refills bucket, unknown provider raises `APIClientError`. Ruff renamed `RateLimitExceeded` → `RateLimitError` (N818). Quality gate: ruff ✅, mypy ✅ (28 files), pytest **54 passed + 17 xfailed** (exit 0), zero regressions. Ready for Task 2 (sensory/news.py). | 58% |
| 2026-04-06 | Phase 2 Task 1 hardening via `/code-review` → `/qa`. 4 LOW findings fixed: (1) `DEFAULT_USER_AGENT = "neural-edge/0.1"` merged into every request so vendor access logs attribute traffic back to us (caller headers still win on conflict); (2) `logging` wired in — DEBUG on cache hit + HTTP GET, WARNING on rate-limit hit so operators can spot over-calling without reading the source; (3) 4 new HTTP error-path tests (`test_http_500_propagates_as_http_error`, `test_connection_error_propagates`, `test_timeout_propagates`, `test_failed_request_does_not_populate_cache`) pin the contract that transport failures propagate unchanged and failed requests never poison the cache; (4) `docs/TECHNICAL_DEBT.md` LOW-01 entry documenting the unbounded-cache slow burn with a concrete fix plan (opportunistic sweep + OrderedDict LRU cap), linked from the `api_client` module docstring. `/qa` Full tier: all 11 checks PASS or SKIP with documented reasons. Quality gate: ruff ✅, mypy ✅ (28 files), pytest **58 passed + 17 xfailed** (exit 0). | 58% |
