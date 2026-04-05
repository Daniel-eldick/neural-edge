---
description: Testing guidelines and commands
globs:
  # FILL: Add glob patterns for your test files
  - 'e2e/**'
  - '**/*.test.*'
  - '**/*.spec.*'
---

# Testing Guide

## Test Commands

<!-- FILL: Replace with your project's test commands -->
```bash
# Unit Tests
npm test                  # Watch mode
npm run test:run          # Single run
npm run test:coverage     # With coverage

# E2E Tests
npm run test:e2e          # Headless
npm run test:e2e:ui       # UI mode
npm run test:e2e:headed   # In browser

# Full Suite (REQUIRED before commits)
npm run test:all          # Lint + Unit + E2E
```

## Running Single Tests

<!-- FILL: Replace with your project's single test commands -->
```bash
# Unit test
npm test -- path/to/test.test.ts
npm test -- -t "should handle edge case"

# E2E test
npm run test:e2e -- path/to/test.spec.ts
npm run test:e2e -- --grep "specific test name"
```

## Test ID Convention

Use `data-testid` attributes for E2E selectors:

- Format: `{component}-{element}-{modifier}`
- Example: `user-submit-button`, `search-input-field`

## Test Types

<!-- FILL: Update locations to match your project structure -->
| Type   | Location          | Purpose                           |
| ------ | ----------------- | --------------------------------- |
| Unit   | `src/__tests__/`  | Component logic, hooks, utilities |
| E2E    | `e2e/`            | User flows, integration           |
| Manual | `docs/testbooks/` | QA verification                   |

## Coverage Tax

When you touch a source file with < 60% coverage AND the change is logic (not CSS/copy/config), add at least one test for the code you touched. Coverage grows organically — like cleaning your station as you cook.

**Exempt from coverage tax**:

- CSS/styling-only changes
- Copy/text changes
- Config, docs, skill files
- Files already at >= 60% coverage

**Check coverage**: `npm run test:coverage`

## Zero Tolerance Policy

- All tests must pass before commit
- No skipped tests without documented reason
- No console warnings in test output
