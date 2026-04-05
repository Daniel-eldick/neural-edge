---
name: perf-audit
description: Frontend performance audit with bundle analysis, network profiling, and Core Web Vitals. Use for periodic performance reviews or after major changes.
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, TodoWrite, Task, mcp__chrome-devtools__take_snapshot, mcp__chrome-devtools__take_screenshot, mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__new_page, mcp__chrome-devtools__list_pages, mcp__chrome-devtools__select_page, mcp__chrome-devtools__list_network_requests, mcp__chrome-devtools__get_network_request, mcp__chrome-devtools__list_console_messages, mcp__chrome-devtools__performance_start_trace, mcp__chrome-devtools__performance_stop_trace, mcp__chrome-devtools__performance_analyze_insight, mcp__chrome-devtools__emulate, mcp__chrome-devtools__resize_page, mcp__chrome-devtools__wait_for
---

# Performance Audit Skill

Systematic frontend performance analysis using Chrome DevTools MCP, build output analysis, and codebase inspection. Produces an actionable findings report with prioritized fixes.

## When to Use

- `/perf-audit`, "audit performance", "check web vitals", "bundle size check"
- After major feature releases or dependency updates
- Monthly performance health check
- When Lighthouse score drops or users report slowness
- Before onboarding tenants with high traffic expectations

## When NOT to Use

- Database query performance (use `/db-audit`)
- Debugging a specific runtime error (use `/diagnose`)
- Real-time monitoring (use observability tools)
- Simple "is it working" check (use `/prod-audit`)

---

## Performance Budgets (Hard Limits)

<!-- FILL: Set budgets appropriate for your target audience's network conditions -->

| Metric                          | Budget  | Current | Status  |
| ------------------------------- | ------- | ------- | ------- |
| Critical path JS (gzipped)      | < 250KB | TBD     | MEASURE |
| Critical path CSS (gzipped)     | < 25KB  | TBD     | MEASURE |
| Total critical path (gzipped)   | < 300KB | TBD     | MEASURE |
| Largest single chunk (gzipped)  | < 100KB | TBD     | MEASURE |
| LCP (desktop)                   | < 2.5s  | TBD     | MEASURE |
| LCP (mobile, slow 4G)           | < 4.0s  | TBD     | MEASURE |
| FCP                             | < 1.8s  | TBD     | MEASURE |
| TBT                             | < 200ms | TBD     | MEASURE |
| CLS                             | < 0.1   | TBD     | MEASURE |
| Network requests (initial page) | < 30    | TBD     | MEASURE |
| Duplicate API calls             | 0       | TBD     | MEASURE |

---

## Workflow

### Phase 1: Build Analysis (Offline — No Browser Needed)

Run production build and capture chunk sizes:

```bash
<!-- FILL: your build command, e.g., npm run build 2>&1 | tail -50 -->
```

**Check against budgets:**

1. **Main chunk**: Must be < 100KB gzipped
2. **Critical path total**: Sum of all critical-path chunks < budget
3. **Lazy chunks**: Non-critical pages should NOT appear in critical path
4. **Chunk count**: Flag if > 50 individual icon/component chunks (HTTP/2 overhead)

**Record in TodoWrite**: Each chunk over budget as a separate finding.

### Phase 2: Dependency Audit

Quick checks for common bloat:

```bash
# Check for unused dependencies in package.json
<!-- FILL: your depcheck command with appropriate ignores -->
npx depcheck --ignores="@types/*,eslint*,prettier,typescript" 2>/dev/null | head -30
```

**Key checks:**

- [ ] Any build tools in runtime dependencies? (dead weight in bundle)
- [ ] Duplicate internal packages?
- [ ] Are analytics/tracking SDKs lazy-loaded or on critical path?
- [ ] Are icon libraries tree-shaken or importing entire packages?

### Phase 3: Chrome DevTools MCP — Network Profiling

Navigate to the target page and capture network data:

```
1. Navigate to production page (or localhost if testing locally)
2. List all network requests — count and categorize
3. Get detailed headers for the 5 largest JS chunks
4. Check Cache-Control headers on hashed assets
5. Count duplicate API calls (same URL, same params)
```

**Duplicate detection heuristic:**

<!-- FILL: Update with your app's common API patterns -->
- Same API endpoint + same filters appearing 2+ times
- HEAD requests that duplicate data from existing queries
- Entity data fetched by both slug and ID

**Record findings with evidence**: Request count, sizes, duplicate URLs.

### Phase 4: Chrome DevTools MCP — Performance Trace

Run traces on the target page:

```
1. Desktop trace (reload + autoStop):
   - Record LCP, CLS, INP
   - Check NetworkDependencyTree insight
   - Check RenderBlocking insight

2. Mobile emulated trace (Slow 4G + 4x CPU throttle):
   - Emulate: { networkConditions: "Slow 4G", cpuThrottlingRate: 4 }
   - Record same metrics
   - Compare to desktop
```

**Analyze insights:**

- `NetworkDependencyTree` — Find the longest chain
- `RenderBlocking` — Any blocking resources besides critical scripts?
- `ThirdParties` — External scripts impacting load time?
- `CLSCulprits` — What's causing layout shifts?
- `LCPBreakdown` — TTFB vs resource load vs render delay?

### Phase 5: Codebase Quick Checks

Targeted grep/read for known patterns:

```
1. Query deduplication: Search for hooks that query same endpoint with different cache keys
2. Font loading: Check index.html for font loading strategy
3. Lazy loading: Verify non-critical pages use dynamic imports
4. Image optimization: Check for missing loading="lazy" on images
5. Analytics SDK: Verify tracking tools are lazy-loaded
6. Chunking strategy: Review build config for splitting opportunities
```

### Phase 6: Generate Report

Create findings document at `docs/active/PERF_AUDIT_[DATE].md`:

```markdown
# Performance Audit — [DATE]

**Auditor**: Claude Code
**Target**: [URL or page path]
**Mode**: [Full / Quick / Bundle-only]

## Summary

| Metric   | Budget   | Measured | Status    |
| -------- | -------- | -------- | --------- |
| [metric] | [budget] | [value]  | [OK/OVER] |

## Findings

### [P1] [Title] — [CRITICAL/HIGH/MEDIUM/LOW]

**Evidence**: [Specific numbers, screenshots, or command output]
**Impact**: [Estimated improvement]
**Fix**: [Specific code change or approach]
**Risk**: [Zero / Low / Medium]
**Files**: [Affected files]

### [P2] ...

## Optimization Roadmap

| Priority | Fix   | Impact   | Effort   | Risk   |
| -------- | ----- | -------- | -------- | ------ |
| 1        | [fix] | [impact] | [effort] | [risk] |

## Baseline for Next Audit

[Record current numbers so next audit can compare]
```

---

## Modes

### Full Audit (Default)

All 6 phases. Use for monthly reviews or after major changes.

### Quick Audit

Phases 1 + 2 only (build analysis + dependency audit). No browser needed.
Use for quick pre-commit size checks.

### Targeted Audit

Specify a single concern:

- `bundle` — Phase 1 only
- `network` — Phases 3-4 only
- `queries` — Phase 5 (query deduplication focus)
- `fonts` — Phase 5 (font loading focus)

---

## Known Optimization Opportunities

<!-- FILL: Populate after your first audit. Example patterns: -->
<!--
1. **Manual chunks under-coverage**: Only X/Y UI packages captured → rest pile into main chunk
2. **Duplicate API calls**: Multiple queries for same data
3. **No cache headers**: Missing Cache-Control for hashed assets (immutable)
4. **Font loading**: External fonts via blocking <link> — consider self-hosting
5. **Eager loading**: Heavy components loaded on critical path but only used in lazy routes
-->

---

## Principles

1. **Measure, don't guess** — Every finding must have a number from build output, DevTools, or MCP
2. **Budget-driven** — Compare against explicit budgets, not "it feels fast"
3. **Zero-risk first** — Prioritize optimizations that don't change behavior
4. **Network context matters** — Consider your users' actual connection speeds
5. **Regression prevention** — Record baselines so next audit can detect regressions
6. **Critical path focus** — Only the initial load matters for Lighthouse. Lazy chunks are free until loaded

## Anti-Patterns

- Optimizing lazy-loaded chunks before fixing critical path
- Adding bundle analyzer as a permanent dependency (use temporarily, then remove)
- Splitting chunks so small they cause HTTP/2 overhead (< 5KB is too small)
- Removing code for performance without checking if it's used (use `depcheck`, not guessing)
- Running Lighthouse in dev mode (always test production builds or production URL)
- Comparing DevTools local traces to Lighthouse scores (different methodologies)

---

## Skill Pipeline

```
/perf-audit → findings doc → /plan (if changes needed) → /sign-off → implement → commit → push → PR → /review-pr (in develop)
                                                                                                            ↓
                                                                                                  /perf-audit (verify)
```

**Periodic**: Monthly, or after major feature work, or after dependency updates.

---

## Summary + Next Step (CEO Footer)

After presenting the findings report, close with a 3-line summary:

```
**Summary**: [1 sentence — performance status in plain language]
**Status**: Within budget / X metrics over budget
**Next step**: [specific action — e.g., "/plan for bundle optimization" or "no action — all within budget"]
```
