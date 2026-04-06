# NeuralEdge

Multi-layer AI trading bot with autonomous strategy optimization. Paper trading only.

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

## Key Constraints

- **Paper trading only** — `dry_run: true` until explicitly authorized
- **Immutable evaluator** — `src/autoresearch/prepare.py` cannot be modified by the optimization loop
- **Signal convergence** — Minimum 3 uncorrelated signals required before any trade
- **Risk limits** — Max 1% per trade, 10% drawdown circuit breaker

## Tech Stack

- **Python 3.11+** — Core language
- **Freqtrade** — Trading engine (via pip, not fork)
- **CoinGecko** — Market data
- **Alpaca** — News feed
- **CryptoQuant** — On-chain data
- **pytest + ruff + mypy** — Quality tooling
