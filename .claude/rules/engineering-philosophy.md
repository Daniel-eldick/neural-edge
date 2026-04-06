---
description: Code quality standards and engineering philosophy
globs:
  - 'src/**/*.py'
---

# Engineering Philosophy - CRITICAL

**User Mandate**: _"I want you to be pessimistic when it comes to the quality of the code. I need you to be demanding and perfectionist with the code. We need to take more time to build the perfect system that will never fail."_

## Code Quality Standards (Non-Negotiable)

**You MUST**:

1. **Be Ruthlessly Critical** - Flag anything that _could_ fail under load, even if it works fine now
2. **Think Scale** - Every architectural decision must work at 10x current load
3. **Challenge Everything** - Question patterns, assumptions, and "it works" solutions
4. **Demand Proof** - Don't accept "should work" - verify with tests, benchmarks, or MCP queries
   - **Strategy claims**: "This strategy is profitable" → Prove it with `freqtrade backtesting` (Sharpe ratio, max drawdown, win rate)
   - **Signal claims**: "This API is reliable" → Verify with integration tests that mock failure modes (rate limits, timeouts, malformed responses)
   - **Risk claims**: "Position sizing is safe" → Prove it with unit tests at boundary conditions (max drawdown, 0 balance, extreme conviction scores)
5. **Flag Technical Debt** - Document scalability concerns immediately in TECHNICAL_DEBT.md

## User Experience Standards (Non-Negotiable)

_"If the bot can't explain WHY it made a trade in one sentence, the signal logic is wrong."_

Every user-facing feature must be designed from the user's perspective. Technical perfection that confuses the user is a failure. Run `/ux-design` before `/plan` for any feature with a user-facing component.

## When Reviewing Code, Always Ask

- What happens at 10x load?
- What happens when this fails? (not if, when)
- Is this an N+1 query waiting to happen?
- Will this cause a memory leak over weeks?
- What's the worst-case performance?
- Are we creating a distributed systems footgun?

## Deep Dive Sessions - Schedule Proactively

1. API rate limit compliance (CoinGecko 30/min, Alpaca 200/min — what happens at the limit?)
2. Strategy backtest integrity (is the evaluator measuring what we think it's measuring?)
3. Signal aggregator convergence (do correlated signals slip through the "uncorrelated" gate?)
4. Autoresearch loop safety (can the optimizer game the evaluator indirectly?)
5. Failure mode analysis (exchange API down, news feed stale, all signals disagreeing)

## If You See Red Flags

- Stop immediately
- Document the concern with specific failure scenarios
- Propose a fix with code
- Request time for deep dive session

**This is not optional.** The user prefers delayed, correct code over fast, fragile code.

## Future-Proofing Filter

Before removing anything (code, indexes, configs, docs, feature flags), ask:

| Keep if...                              | Remove if...                        |
| --------------------------------------- | ----------------------------------- |
| Costs < 1% of its resource budget       | Actively causing bugs or confusion  |
| Painful to recreate under load/pressure | Has zero future use AND costs space |
| Belongs to a feature being built        | Truly dead (no callers, no plans)   |

**Default is KEEP.** The cost of re-creating under pressure always exceeds the cost of maintaining something cheap. Disk and RAM are cheaper than engineer time and production incidents.

## Development Approach - Modular, Agile, Flexible

- **We don't build 100% upfront** - Foundation first, then evolve per feature
- **Each new capability = incremental change** to the base model, not a rewrite
- **Config over code** - Enable/disable features via configuration, never delete working code
- **Long-term thinking** - Architecture decisions consider scale, but implementation is iterative
