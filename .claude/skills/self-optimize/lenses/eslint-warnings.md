# Lens: ESLint Warnings

## Objective

**Metric**: Total ESLint warning count across `src/`
**Direction**: Lower is better
**Current baseline**: 2 warnings (as of 2026-03-22)
**Target**: 0

Context: Was 149+ warnings historically. Down to 2 through manual cleanup.
The remaining 2 are `react-refresh/only-export-components` in a context provider file.
This lens is nearly solved — useful as a regression detector more than an optimizer.

## Evaluator

```bash
npx eslint src/ --max-warnings 999 2>&1 | tail -1
```

**How to extract the metric**: Last line reads something like:
`✖ 2 problems (0 errors, 2 warnings)`
Extract the warning count.

## Target Files

```
src/**/*.ts
src/**/*.tsx
```

## Scope Boundaries

NEVER touch:

- `eslint.config.js` (never disable or weaken rules to reduce warnings)
- `tsconfig.json`
- Test files (unless the warning is in a test file)
- Do NOT add `// eslint-disable` comments — fix the actual issue
- Do NOT change exports/imports in ways that break other consumers

## Safety Checks

```bash
npm run quality:check
```

## Hints

- The 2 remaining warnings are `react-refresh/only-export-components` in a context provider that co-exports a component
- Fix: move the React context to a separate file from the component, or re-export through a dedicated file
- After reaching 0: this lens becomes a regression detector — run periodically to catch new warnings

## Known Dead Ends

- (none yet)
