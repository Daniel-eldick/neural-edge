# Technical Debt & Scalability Concerns

**Purpose**: Systematic tracking of code that works now but will fail at scale
**Mandate**: "Build the perfect system that will never fail"
**Review Frequency**: Before every major feature and monthly
**Last Updated**: <!-- FILL: Date of last update -->

---

## Current Status

| Severity | Active | Resolved |
| -------- | ------ | -------- |
| CRITICAL | 0      | 0        |
| HIGH     | 0      | 0        |
| MEDIUM   | 0      | 0        |
| LOW      | 0      | 0        |

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

_No items yet. Add entries as technical debt is discovered._

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
