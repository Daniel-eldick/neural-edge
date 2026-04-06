---
description: Testing guidelines and commands
globs:
  - 'tests/**'
  - '**/*test*.py'
---

# Testing Guide

## Test Commands

```bash
# Unit Tests
pytest                    # Run all tests
pytest -x --timeout=30    # Fail fast, 30s timeout
pytest --cov              # With coverage

# Full Suite (REQUIRED before commits)
ruff check . && mypy . && pytest -x --timeout=30
```

## Running Single Tests

```bash
# Single file
pytest tests/test_strategies/test_alpha_strategy.py

# Single test by name
pytest -k "test_rsi_buy_signal"

# Single directory
pytest tests/test_sensory/

# Verbose output
pytest -v tests/test_signals/test_aggregator.py
```

## Test Types

| Type        | Location                | Purpose                              |
| ----------- | ----------------------- | ------------------------------------ |
| Unit        | `tests/test_*/`         | Strategy logic, signals, risk, utils |
| Integration | `tests/test_*/`         | Sensory API mocking, aggregator flow |
| Manual      | Freqtrade CLI           | `freqtrade backtesting`, `test-strategy` |

## Coverage Tax

When you touch a source file with < 60% coverage AND the change is logic (not config), add at least one test for the code you touched. Coverage grows organically — like cleaning your station as you cook.

**Exempt from coverage tax**:

- Config/settings changes
- Documentation, skill files
- Files already at >= 60% coverage
- `__init__.py` files

**Check coverage**: `pytest --cov`

## Zero Tolerance Policy

- All tests must pass before commit
- No skipped tests without documented reason
- No console warnings in test output
