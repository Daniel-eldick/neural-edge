# Intuitions

Compressed lessons in "When X, Do Y, Because Z" format. The System 1 cache — fast-path pattern matching from validated experience.

**Rules**: Human-curated only (CEO approves during `/coffee-break`). Target 15-30 entries. If > 50, prune aggressively. Remove when obsolete.

<!-- Entries are graduated from observations.md after validation.
     Each entry must have been confirmed across multiple interactions
     or explicitly approved by the user. -->

---

## Database & Backend

<!-- FILL: Add database-specific intuitions as you discover them -->
<!-- Example:
### RLS policy authoring
**When**: Writing or auditing RLS policies
**Do**: Always use `(SELECT auth.uid())` wrapper, never raw `auth.uid()` in WHERE clause
**Why**: Without wrapper, the database re-evaluates per row instead of once per query.
-->

## Performance

<!-- FILL: Add performance-specific intuitions -->
<!-- Example:
### New dependency evaluation
**When**: Considering adding a new npm package
**Do**: Check gzipped size first. Budget: critical path < 300KB total. Lazy-load if non-critical.
**Why**: Users on slow connections. Every KB matters.
-->

## UI / UX

<!-- FILL: Add UI/UX-specific intuitions -->
<!-- Example:
### Color tokens
**When**: Writing CSS/Tailwind in admin components
**Do**: Never use hardcoded colors. Always use design system tokens.
**Why**: Dark mode breaks with hardcoded colors.
-->

## Code Archaeology

<!-- FILL: Add "things that look wrong but aren't" intuitions -->
<!-- Example:
### Multiple variant files
**When**: Seeing multiple versions of a component and thinking "dead code"
**Do**: Check for feature flag routing before deleting
**Why**: Variants are often active via feature flags, not dead code.
-->

## Process

<!-- FILL: Add process-specific intuitions -->
<!-- Example:
### Documentation archive
**When**: Tempted to delete completed plan documents
**Do**: Move to docs/completed/, never delete
**Why**: Cheap to store, valuable audit trail. User explicitly values this.
-->
