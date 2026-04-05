# Lens: Bundle Size

## Objective

**Metric**: Gzipped size of the main critical-path chunk (e.g., `dist/assets/index-*.js`)
**Direction**: Lower is better
**Current baseline**: <!-- FILL: measure with your first build, e.g., 91.23 KB gzipped -->
**Target**: <!-- FILL: set based on your audience's network conditions, e.g., < 80 KB gzipped -->

<!-- FILL: Context about your users' network conditions -->
<!-- Example: Users are on 1-5 Mbps connections. Every KB matters. -->

## Evaluator

```bash
<!-- FILL: your build command that outputs chunk sizes -->
# Example for Vite:
npm run build 2>&1 | grep 'index-' | grep 'gzip:'
```

**How to extract the metric**: The output line looks like:
`dist/assets/index-XXXXX.js    329.40 kB | gzip:  91.23 kB`
Extract the gzip value (last number before "kB").

## Target Files

Files the agent is allowed to modify:

```
src/**/*.ts
src/**/*.tsx
<!-- FILL: your build config file, e.g., vite.config.ts (chunking strategy only — not plugins or aliases) -->
```

## Scope Boundaries

NEVER touch:

- `package.json` (no adding/removing dependencies without explicit approval)
- `tsconfig.json`
- Test setup files
- Linter/formatter configs
- Database/backend layer
- Static assets (`public/**`)
- Test files (`**/*.test.ts`, `**/*.test.tsx`)
- Do NOT remove features or break lazy loading
- Do NOT change the import alias configuration

## Safety Checks

```bash
<!-- FILL: your quality check command, e.g., npm run quality:check -->
```

This should run: format check + lint + type-check + unit tests. All must pass.

## Hints

- Check for imports that could be lazy-loaded (heavy components imported at top level)
- Look for barrel imports (`import { X } from '@/components'`) that defeat tree-shaking
- Check if any large library is imported in the critical path but only used in lazy routes
- Review build config for chunk splitting opportunities
- Look for duplicate code patterns that could be shared
- Check if date-fns, lodash, or icon imports are granular (not importing entire packages)

## Known Dead Ends

- (none yet — will be populated by the journal)
