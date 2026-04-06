# Technical Debt & Scalability Concerns

**Purpose**: Systematic tracking of code that works now but will fail at scale
**Mandate**: "Build the perfect system that will never fail"
**Review Frequency**: Before every major feature and monthly
**Last Updated**: 2026-04-06

---

## Current Status

| Severity | Active | Resolved |
| -------- | ------ | -------- |
| CRITICAL | 0      | 0        |
| HIGH     | 0      | 0        |
| MEDIUM   | 0      | 0        |
| LOW      | 1      | 0        |

---

## Priority Legend

- 🔴 **CRITICAL**: Will cause production outages at scale (fix immediately)
- 🟡 **HIGH**: Performance degradation at scale (fix before scaling)
- 🟢 **MEDIUM**: Technical debt that should be addressed (fix during refactoring)
- 🔵 **LOW**: Nice-to-have improvements (address opportunistically)

---

## Active Technical Debt

**What belongs here**: Code that works now but will fail under load, cause outages, or block future work
**What goes in BACKLOG**: Features, premature optimizations, test infrastructure

### 🔵 LOW-01: api_client cache is unbounded and never swept

**Date Identified**: 2026-04-06
**Priority**: 🔵 **LOW** (in-process memory, bounded by distinct endpoint/param combinations)
**Status**: ⏸️ **OPEN**

**Issue**: [src/core/api_client.py:164-166](src/core/api_client.py#L164-L166) uses a plain `dict` for the TTL cache. Entries expire logically (TTL check on lookup) but are never physically evicted. Over a long-running process (weeks), the dict grows to hold one entry per distinct `(provider, url, sorted_params)` tuple the bot has ever queried.

**Risk**: At current scale (5 trading pairs, ~4 sensory modules, 1m candles) the growth is bounded to a few hundred entries and the leak is invisible. At 10x scale (50 pairs, intraday sweeps of distinct query params, multi-week uptime) the cache could grow into the tens of thousands of entries and slowly consume heap. No crash — just gradual RSS creep that would show up in monitoring before it hurts.

**File**: [src/core/api_client.py:214-243](src/core/api_client.py#L214-L243)
**Current Mitigation**: None. Process restart clears the cache. Entries are cheap (a JSON payload + a float timestamp) so the problem is slow-burn, not acute.

**Fix Plan**:
1. Sweep expired entries opportunistically on every write (cheap: iterate over the cache once, drop anything where `expires_at <= now`). O(n) per write but amortised fine while n stays small.
2. Add a hard `max_entries` cap (e.g. 10_000) that evicts the oldest entry (LRU via `collections.OrderedDict`) when the cap is reached. This is the belt to the sweep's braces.
3. Add a unit test that populates the cache beyond the cap and asserts the oldest entry was evicted.

**Why deferred**: The cache is an optimisation, not a correctness contract (as documented in the `api_client` module docstring). Shipping the sweep + LRU now would add ~30 lines and one extra dependency on `OrderedDict` semantics. At current bot scale the leak is invisible; addressing it before Phase 2 completes would be premature optimisation. Revisit if we run a multi-week paper-trading session or see RSS growth in monitoring.

<!-- Example entry:

### 🟡 HIGH-01: Description of the Issue

**Date Identified**: Month Day, Year
**Priority**: 🟡 **HIGH** (brief risk statement)
**Status**: ⏸️ **OPEN**

**Issue**: What's wrong — specific, not vague.

**Risk**: What happens at 10x load? What's the failure scenario?
**File**: `src/path/to/file.ts:line-range`
**Current Mitigation**: Any stopgap in place?

**Fix Plan**:
1. Step 1
2. Step 2

**Estimated Effort**: X hours
-->

---

## Resolved (Archive Summary)

_Resolved entries are moved here with a one-line summary. Full details preserved in `docs/archive/`._

<!-- Example:
| Issue | Resolved | Summary |
|-------|----------|---------|
| HIGH-01: N+1 query in dashboard | Jan 15, 2026 | Batched into single query. 50ms → 5ms. |
-->
