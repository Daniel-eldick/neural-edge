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

## Results cockpit

The local cockpit displays saved experiments in one browser page, with returns, drawdown,
trade records, and recorded replay equity. It is a dated snapshot; the AI agent, Jev,
teacher/memory, start/pause controls and online hosting are not connected yet.

```bash
.venv/bin/python -m src.cockpit --archive user_data/backtest_results/backtest-result-2026-04-06_04-41-23.zip
open user_data/cockpit/index.html
```

For new completed replay runs, use `--journal run-001.sqlite`. Both input flags can be
repeated. No inputs produces an honest empty state. Regenerate after each completed run;
browser refresh alone does not update the snapshot. Input files are opened read-only.
Missing, corrupt, failed or incomplete runs fail explicitly rather than showing a false
success. The journal chart samples at most approximately 1,000 observations; its displayed
range is not a substitute for the run's drawdown statistic. Decision details show the last
50 records. No saved API configuration is included in the page.
