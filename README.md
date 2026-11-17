# NeuralEdge

> **Status: archived on 2026-11-18.** No trading edge was found. Nothing is scheduled
> and nothing is spending. See the
> [archive decision](docs/completed/ARCHIVE_DECISION_2026-11-18.md) for the evidence
> and what would justify reopening.

Experimental multi-layer AI trading bot. Paper trading only. Only Layer 1 (a basic
strategy and a risk module) was built; the layers above it are stubs.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 5: AUTORESEARCH LOOP                             │
│  Autonomous strategy optimization (Karpathy pattern)    │
├─────────────────────────────────────────────────────────┤
│  Layer 4: MIROFISH SWARM (stub)                         │
├─────────────────────────────────────────────────────────┤
│  Layer 3: KNOWLEDGE GRAPH (stub)                        │
├─────────────────────────────────────────────────────────┤
│  Layer 2: SENSORY SYSTEM                                │
│  News · On-chain · Sentiment · Macro                    │
├─────────────────────────────────────────────────────────┤
│  Layer 1: FREQTRADE + COINGECKO                         │
│  Execution · TA · Risk management · Paper trading       │
└─────────────────────────────────────────────────────────┘
```

## Setup

```bash
# Prerequisites (macOS)
brew install ta-lib

# Create environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure API keys
cp .env.example .env
# Edit .env with your keys

# Run paper trading
freqtrade trade --dry-run --config config.json
```

## Development

```bash
# Quality gate (required before commits)
ruff check . && mypy . && pytest -x --timeout=30

# Run tests
pytest                                    # All tests
pytest tests/test_strategies/             # Single directory
pytest -k "test_rsi_buy_signal"           # Single test

# Lint + format
ruff check .                              # Lint
ruff format .                             # Auto-format
mypy .                                    # Type checking

# Backtesting
freqtrade backtesting --strategy AlphaStrategy
```

## What exists and what does not

- **Paper trading only** — `dry_run: true`. This was never changed.
- **Strategy** — `src/strategies/alpha_strategy.py`. Backtested over two years it took
  14 trades and made nothing (see the archive decision).
- **Risk module** — `src/core/risk.py` is tested but not connected to the strategy, so
  its 1% and drawdown limits are not enforced by `config.json`.
- **Backtester** — `python -m src.backtest.run --data-dir DATA --out OUT`, or the manual
  `Strategy backtest` workflow. Public data, no keys.
- **Hosted research loop** — `deploy/research/`. Paused; its engine is not in this repo.
- **Not built** — sensory signals, the 3-signal convergence gate, the autoresearch
  evaluator (`src/autoresearch/prepare.py`), swarm and knowledge-graph layers.

## Tech Stack

- **Python 3.11+** — Core language
- **Freqtrade** — Trading engine (via pip, not fork)
- **CoinGecko** — Market data
- **Alpaca** — News feed
- **CryptoQuant** — On-chain data
- **pytest + ruff + mypy** — Quality tooling
