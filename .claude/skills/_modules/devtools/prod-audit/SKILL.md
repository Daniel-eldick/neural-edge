---
name: prod-audit
description: Production console & network health audit via Chrome DevTools MCP. Systematically tests all pages and order lifecycle, captures findings. Use after deploys, for periodic health checks, or when something feels off.
allowed-tools: Read, Bash, Glob, Grep, Write, Edit, TodoWrite, mcp__chrome-devtools__take_snapshot, mcp__chrome-devtools__take_screenshot, mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__click, mcp__chrome-devtools__fill, mcp__chrome-devtools__fill_form, mcp__chrome-devtools__hover, mcp__chrome-devtools__press_key, mcp__chrome-devtools__type_text, mcp__chrome-devtools__wait_for, mcp__chrome-devtools__list_console_messages, mcp__chrome-devtools__get_console_message, mcp__chrome-devtools__list_network_requests, mcp__chrome-devtools__get_network_request, mcp__chrome-devtools__list_pages, mcp__chrome-devtools__select_page, mcp__chrome-devtools__new_page, mcp__chrome-devtools__evaluate_script, mcp__chrome-devtools__emulate, mcp__chrome-devtools__handle_dialog
---

# Production Audit Skill

Systematic production health audit using Chrome DevTools MCP. Navigates every page, tests core user lifecycle, captures all console errors, warnings, network failures, and performance issues.

## When to Use

- `/prod-audit` — after deploys, periodic health checks, "something feels off"
- After `/review-pr` merges a PR
- Weekly/monthly production health check
- User reports unexpected behavior

## When NOT to Use

- Testing local dev changes (use `/qa` instead)
- Automated regression testing (use `/test` for Vitest/Playwright)
- Database-specific audits (use `/db-audit`)

---

## Modes

| Mode               | Syntax               | Flows       | Mutates?        |
| ------------------ | -------------------- | ----------- | --------------- |
| **Full** (default) | `/prod-audit`        | All 9       | Yes (demo only) |
| **Quick**          | `/prod-audit quick`  | 1-4 only    | No              |
| **Targeted**       | `/prod-audit flow:5` | Single flow | Depends on flow |

## Target Tenant

<!-- FILL: Replace with your demo/test tenant for safe mutation testing -->
- **Default**: `demo-tenant` (safe for mutations)
- **Override**: `/prod-audit tenant:slug-name`
- **Safety**: If targeting a non-demo tenant AND mode includes mutation flows (3, 5, 6), WARN the user and require confirmation before proceeding. Suggest Quick mode for real tenants.

---

## Workflow

### Phase 1: Setup

1. Read testbook: `docs/testbooks/PROD_AUDIT_TESTBOOK.md`
2. Determine mode (Full/Quick/Targeted) and target tenant from arguments
3. Navigate to <!-- FILL: your production URL, e.g., https://yourapp.example.com/ -->
4. Take initial snapshot to verify site is up
5. Record baseline console state:
   ```
   list_console_messages({ types: ["error", "warn"] })
   ```
6. Create TodoWrite with one item per flow being tested

### Phase 2: Customer Flows (Flows 1-3)

Execute each flow per the testbook step tables.

**Flow 1: Homepage**

- Navigate to `/`
- Take snapshot — verify main content renders
- Capture console + network

**Flow 2: Main User Page**

<!-- FILL: Replace with your app's primary user-facing page -->
- Navigate to `/demo-tenant/main-page`
- Wait for content to load
- Take snapshot — verify content renders correctly
- Capture console + network

**Flow 3: Core User Action** (Full/Targeted only)

<!-- FILL: Replace with your app's primary user action (e.g., creating an order, submitting a form) -->
- Perform the primary user action
- Wait for confirmation/success
- Capture console + network

**After EACH flow**:

```
list_console_messages({ types: ["error"] })         → must be zero
list_console_messages({ types: ["warn"] })           → document all
list_network_requests({ resourceTypes: ["fetch", "xhr"] })  → check for 4xx/5xx
```

### Phase 3: Admin Flows (Flows 4-6)

**Flow 4: Admin Login**

<!-- FILL: Replace with your admin URL pattern and test credentials -->
- Navigate to admin area
- If auth redirect occurs: use test account (from test helpers)
- Fill email + password via `fill_form`, click Sign In
- Wait for dashboard to load
- Capture console + network
- **Ask user about SW errors** (MCP can't see service worker context)

**Flow 5: Core Admin Action** (Full/Targeted only)

<!-- FILL: Replace with your app's primary admin workflow -->
- Perform admin lifecycle action
- Capture console + network after EACH status change

**Flow 6: Admin Destructive Action** (Full/Targeted only)

<!-- FILL: Replace with your app's cancel/delete/archive workflow -->
- Perform destructive action on test data
- Verify status changes correctly
- Capture console + network

### Phase 4: Admin Pages Walkthrough (Flows 7-9)

<!-- FILL: Replace with your admin page routes -->

**Flow 7: Primary Admin Pages**

- Navigate to each primary admin page
- Wait for data load, take snapshot
- Capture console + network for each

**Flow 8: Secondary Admin Pages**

- Navigate to each secondary admin page
- Capture console + network for each

**Flow 9: Reporting/History Pages**

- Navigate to analytics/reporting pages
- Navigate to history/archive pages
- Capture console + network for each

### Phase 5: Report

1. Create findings doc: `docs/active/PROD_AUDIT_FINDINGS_[YYYY-MM-DD].md`
2. Use the findings template (below)
3. Categorize all captured issues:
   - **Errors**: console.error, uncaught exceptions, error boundaries
   - **Warnings**: console.warn, deprecation notices, framework warnings
   - **Network**: failed fetch/XHR (4xx/5xx), CORS issues, timeouts
   - **Performance**: requests >2s, payloads >500KB
4. Fill summary table with PASS/FAIL per flow
5. List action items with severity and suggested fixes
6. **If all flows PASS**: move findings to `docs/completed/`
7. **If any FAIL**: keep in `docs/active/` for follow-up

---

## Findings Doc Template

```markdown
# Production Audit Findings — [DATE]

**Target**: [tenant slug] | **Mode**: Full/Quick/Targeted
**URL**: <!-- FILL: your production URL -->/[slug]
**Auditor**: Claude Code | **Duration**: ~XX min

## Summary

| #   | Flow                 | Status | Errors | Warnings | Network |
| --- | -------------------- | ------ | ------ | -------- | ------- |
| 1   | Homepage             | /   | 0      | 0        | 0       |
| 2   | Main User Page       | /   | 0      | 0        | 0       |
| 3   | Core User Action     | /   | 0      | 0        | 0       |
| 4   | Admin Login          | /   | 0      | 0        | 0       |
| 5   | Core Admin Action    | /   | 0      | 0        | 0       |
| 6   | Admin Destructive    | /   | 0      | 0        | 0       |
| 7   | Primary Admin Pages  | /   | 0      | 0        | 0       |
| 8   | Secondary Pages      | /   | 0      | 0        | 0       |
| 9   | Reporting/History    | /   | 0      | 0        | 0       |

**Overall**: CLEAN / WARNINGS ONLY / ERRORS FOUND

## Detailed Findings

### Flow N: [Name] — [PASS/FAIL]

**Console Errors** (count):
[none or list actual messages with stack traces]

**Console Warnings** (count):
[none or list]

**Network Issues** (count):
[none or list with URL, status code, response snippet]

**Screenshot**: [if relevant — capture error states with take_screenshot]

## Action Items

| #   | Finding       | Severity         | Flow | Suggested Fix |
| --- | ------------- | ---------------- | ---- | ------------- |
| 1   | [description] | Error/Warn/Perf  | [#]  | [what to do]  |

## Environment

- Browser: Chrome (DevTools MCP)
- Date/Time: [timestamp]
- Production commit: [if determinable]
```

---

## Console Capture Strategy

At each checkpoint, run these DevTools MCP calls:

```
# Errors — MUST be zero for PASS
list_console_messages({ types: ["error"] })

# Warnings — document all, not blocking
list_console_messages({ types: ["warn"] })

# Info — skim for anomalies only
list_console_messages({ types: ["info", "log"] })

# Network — check for failed requests
list_network_requests({ resourceTypes: ["fetch", "xhr"] })
```

For detailed inspection of specific messages or requests:

```
get_console_message({ msgid: N })
get_network_request({ reqid: N })
```

### MCP Limitation: Service Worker Errors

**CRITICAL**: `list_console_messages` does NOT capture service worker errors. SW runs in a separate execution context. Always add this manual check step:

1. Ask user: "Do you see any errors in the browser console that I might be missing? (SW errors are invisible to MCP)"
2. Or use `evaluate_script` to probe SW health:

```
evaluate_script(() => navigator.serviceWorker.ready.then(r => ({ state: r.active?.state, scriptURL: r.active?.scriptURL })))
```

### Known Noise (ignore these)

<!-- FILL: Update this list as patterns emerge in your project -->
- Service Worker registration/update logs (info, expected)
- Analytics SDK debug/info logs (non-critical)
- Browser extension injected scripts (not our code)
- Favicon 404 (cosmetic, non-blocking)

---

## Pass Criteria

A flow **PASSES** when:

- Zero `console.error` messages (excluding known noise)
- Zero failed network requests (4xx/5xx on fetch/xhr)
- Page renders without blank screens or missing content (verified by snapshot)

A flow gets **WARNINGS** when:

- `console.warn` messages present but no errors
- Slow network requests (>2s) but successful

A flow **FAILS** when:

- Any `console.error` (not in known noise list)
- Any failed network request (4xx/5xx)
- Page fails to render (blank screen, error boundary)

---

## Principles

1. **Observe, don't fix** — This skill captures findings. Fixes happen in a separate `/plan` cycle.
2. **Evidence over assumptions** — Every finding includes the actual console message or network response.
3. **Demo tenant for mutations** — Never create/modify data on real tenants unless explicitly confirmed.
4. **Known noise evolves** — Add patterns to the noise list as we learn what's normal.
5. **Screenshots for failures** — If a flow fails, capture a screenshot for the findings doc.

---

## Skill Pipeline

```
/review-pr (merge) → /prod-audit → [if issues found] → /plan → implement → commit → push → PR → /review-pr
                          ↑
                     you are here
```

Also pairs with:

- `/scaling-check` — for capacity metrics (complementary to console health)
- `/db-audit` — for database-level health (complementary to frontend health)

---

## Summary + Next Step (CEO Footer)

After presenting the findings doc, close with a 3-line summary:

```
**Summary**: [1 sentence — production health status in plain language]
**Status**: All clean / X warnings / Y errors found
**Next step**: [specific action — e.g., "/plan to fix console errors" or "schedule next audit post-deploy"]
```
