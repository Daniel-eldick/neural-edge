# NeuralEdge

Research project for an AI apprentice trader that learns selectively from historical market replay and later paper trading.

**Start here: [Apprentice trader reference and plan](docs/active/APPRENTICE_TRADER_PLAN.md).**

Status: first offline replay foundation implemented. It includes causal observations, simulated accounting, risk enforcement and a SQLite journal. The AI trader, teacher and learning loop are still pending. Profitability is unproven.

- [Documentation index](docs/README.md)
- [Agent instructions](AGENTS.md)
- [Historical setup plan](docs/archive/NEURAL_EDGE_PROJECT_SETUP.md)

Run the offline replay with your synchronized OHLCV CSV:

```bash
python -m src.replay --csv candles.csv --journal run-001.sqlite
```

See the reference plan's **Offline replay usage** section for setup, CSV format and simulation limits. This command runs a fixed comparison policy, not the AI apprentice.

The existing Freqtrade config remains separate: its three-position limit and legacy sizing helper do not enforce the new replay limits. No live trading or background worker is enabled.
