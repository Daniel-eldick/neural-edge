---
description: Code quality standards and engineering philosophy
globs:
  # FILL: Add glob patterns for your source code files
  # Examples: 'src/**/*.ts', 'src/**/*.tsx', 'app/**/*.py', 'lib/**/*.rb'
  - 'src/**'
---

# Engineering Philosophy - CRITICAL

<!-- FILL: Replace with your team's quality mandate. Example: -->
**User Mandate**: _"I want you to be pessimistic when it comes to the quality of the code. I need you to be demanding and perfectionist with the code. We need to take more time to build the perfect system that will never fail."_

## Code Quality Standards (Non-Negotiable)

**You MUST**:

1. **Be Ruthlessly Critical** - Flag anything that _could_ fail under load, even if it works fine now
2. **Think Scale** - Every architectural decision must work at 10x current load
3. **Challenge Everything** - Question patterns, assumptions, and "it works" solutions
4. **Demand Proof** - Don't accept "should work" - verify with tests, benchmarks, or MCP queries
   <!-- FILL: Add your project's verification tools. Examples: -->
   <!-- - Database: `mcp__supabase__execute_sql` for actual row counts, query plans -->
   <!-- - Security: `mcp__supabase__get_advisors({ type: "security" })` for audits -->
   <!-- - Performance: Lighthouse, bundle analyzer, profiling tools -->
   - **Example**: "This query is fast" → Prove it with `EXPLAIN ANALYZE`
   - **Example**: "Security is solid" → Verify with automated audit tools
5. **Flag Technical Debt** - Document scalability concerns immediately in TECHNICAL_DEBT.md

## User Experience Standards (Non-Negotiable)

<!-- FILL: Replace with your domain's UX litmus test. Examples: -->
<!-- Food service: "If a busy operator can't figure it out during a lunch rush, it's a bug." -->
<!-- SaaS: "If a user can't complete the task in under 3 clicks, it's a bug." -->
<!-- CLI: "If a developer needs to read the docs to use this command, it's a bug." -->
_"If a busy user can't figure it out under pressure, it's a bug — not a training issue."_

Every user-facing feature must be designed from the user's perspective. Technical perfection that confuses the user is a failure. Run `/ux-design` before `/plan` for any feature with a user-facing component.

## When Reviewing Code, Always Ask

- What happens at 10x load?
- What happens when this fails? (not if, when)
- Is this an N+1 query waiting to happen?
- Will this cause a memory leak over weeks?
- What's the worst-case performance?
- Are we creating a distributed systems footgun?

## Deep Dive Sessions - Schedule Proactively

<!-- FILL: Replace with your project's critical audit areas. Examples: -->
1. Database query performance audits (check for N+1 patterns)
2. Concurrent load analysis (stress test with 50+ simultaneous operations)
3. Storage lifecycle and memory management
4. Real-time/streaming scalability
5. Failure mode analysis (infrastructure down, network flaps, crashes)

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
