---
name: ux-design
description: UX conception for user-facing features. 6 phases, 8 principles, wireframes, journey maps. Use before /plan for any feature with a UI component.
allowed-tools: Read, Glob, Grep, Bash, AskUserQuestion, WebSearch, WebFetch, mcp__shadcn__search_items_in_registries, mcp__shadcn__view_items_in_registries, mcp__chrome-devtools__take_snapshot, mcp__chrome-devtools__navigate_page, mcp__chrome-devtools__emulate, mcp__claude_ai_Figma__get_design_context, mcp__claude_ai_Figma__get_screenshot
---

# UX Design Skill

User experience conception for features with a user-facing component. Produces a UX Brief that feeds into `/plan` as Section 2 (Solution Design).

_"If a busy user can't figure it out during a lunch rush, it's a bug — not a training issue."_

## When to Use

- Before `/plan` for any feature with a UI component
- `/ux-design`, "design the UX", "how should this look/work for the user"
- After `/brainstorm` converges on BUILD for a UI feature

## When NOT to Use

- Backend-only changes (no UI) → go straight to `/plan`
- Bug fix with no UX impact → `/diagnose` or `/plan`
- Styling/theming only (no interaction change) → just do it

---

## The 8 Principles

Every user-facing feature is evaluated against these. Tailored to the project context — consider your users' devices, environment, connectivity, and usage patterns.

| #   | Principle             | Question                                                              |
| --- | --------------------- | --------------------------------------------------------------------- |
| 1   | **Visibility**        | Does the user always know what's happening? (loading, success, error) |
| 2   | **Forgiveness**       | Can they undo mistakes? (undo > "are you sure?")                      |
| 3   | **Minimalism**        | Does every element earn its screen space?                             |
| 4   | **Consistency**       | Same action, same place, same look across the app?                    |
| 5   | **Context-awareness** | Works on greasy tablet, loud kitchen, 1-5 Mbps, one-handed?           |
| 6   | **Error recovery**    | Error says WHAT happened + WHAT to do about it?                       |
| 7   | **Speed of use**      | Minimum taps/clicks for the primary action?                           |
| 8   | **Learnability**      | Productive in <5 min, zero training required?                         |

---

## The 6 Phases

### Phase 1: User Context — Who, Where, When

Define the user and their environment before designing anything.

| Question                      | Answer                                                     |
| ----------------------------- | ---------------------------------------------------------- |
| **Who** uses this?            | [persona]                                                  |
| **Where**?                    | [device, environment — tablet in kitchen? phone on couch?] |
| **When**?                     | [during rush? end of day? first setup?]                    |
| **What else** are they doing? | [multitasking? focused?]                                   |
| **Skill level**?              | [tech-savvy owner? first-time customer?]                   |

**Output**: 2-3 sentence user context statement.

### Phase 2: Benchmark (Optional) — Research & Compare

**Skip unless**: the feature has clear industry comparisons worth studying, or the user requests it.

- Research competitor UX for the same flow (WebSearch/WebFetch)
- Extract patterns (what works) and anti-patterns (what doesn't)
- Note industry standards (e.g., "all major POS systems show order total in top-right")

| Competitor / Standard | Pattern Found | Applicable?  |
| --------------------- | ------------- | ------------ |
| [name]                | [pattern]     | Yes/No/Adapt |

**Output**: 2-3 actionable insights that inform the design.

### Phase 3: Journey Map — The User's Path

Map the full user journey, not just the happy path.

```
30s BEFORE          → PRIMARY ACTION        → HAPPY PATH           → DONE
[what triggers it]  → [the core interaction] → [success feedback]   → [what's next]
```

**Edge cases to map** (pick relevant ones):

| State      | What the user sees   | What they can do       |
| ---------- | -------------------- | ---------------------- |
| Empty      | [no data yet]        | [clear CTA]            |
| Error      | [what went wrong]    | [recovery action]      |
| Slow (>2s) | [loading feedback]   | [can they cancel?]     |
| Offline    | [degraded state]     | [what still works?]    |
| First-time | [onboarding needed?] | [guided or intuitive?] |

**Output**: Journey map with edge cases relevant to this feature.

### Phase 4: Wireframe — Make It Visual

**Default: ASCII wireframe.** Supports other formats on request.

```
┌─────────────────────────────────┐
│  [Header / Navigation]          │
├─────────────────────────────────┤
│                                 │
│  [Primary content area]         │
│                                 │
│  [Primary action — prominent]   │
│                                 │
├─────────────────────────────────┤
│  [Secondary actions]            │
└─────────────────────────────────┘
```

**Rules**:

- Primary action visible without scrolling
- Touch targets ≥ 44px (Apple HIG / WCAG 2.1 AAA)
- Critical info in top 60% of viewport (thumb zone on mobile)
- No more than 3 actions visible at once (cognitive load)

**Alternative formats** (when requested):

- **Figma pull**: Use `mcp__claude_ai_Figma__get_design_context` if designs exist
- **Structured text flow**: Step-by-step interaction description
- **React prototype**: Quick functional prototype (for complex interactions)

**Output**: Visual representation of the key screens/states.

### Phase 5: Heuristic Sweep — Score Against 8 Principles

Evaluate the design against each principle. Be honest — CONCERN and FAIL are useful findings.

| #   | Principle         | Score             | Finding                |
| --- | ----------------- | ----------------- | ---------------------- |
| 1   | Visibility        | PASS/CONCERN/FAIL | [specific observation] |
| 2   | Forgiveness       | PASS/CONCERN/FAIL | [specific observation] |
| 3   | Minimalism        | PASS/CONCERN/FAIL | [specific observation] |
| 4   | Consistency       | PASS/CONCERN/FAIL | [specific observation] |
| 5   | Context-awareness | PASS/CONCERN/FAIL | [specific observation] |
| 6   | Error recovery    | PASS/CONCERN/FAIL | [specific observation] |
| 7   | Speed of use      | PASS/CONCERN/FAIL | [specific observation] |
| 8   | Learnability      | PASS/CONCERN/FAIL | [specific observation] |

**FAIL** = must fix before implementation. **CONCERN** = document as UX debt if not addressed.

**Output**: Heuristic scorecard with specific findings per principle.

### Phase 6: Pattern Check — Reuse Before Reinventing

Before finalizing, check what already exists:

1. **Existing app flows**: Grep for similar patterns in `src/components/` — reuse interaction patterns for consistency
2. **shadcn registry**: `mcp__shadcn__search_items_in_registries` for relevant components
3. **Figma designs**: Check if designs exist via Figma MCP (if configured)
4. **Admin color system**: If admin UI, reference `docs/guides/ADMIN_COLOR_SYSTEM.md` tokens

**Output**: List of reusable components/patterns + any new components needed.

---

## UX Brief Output

The final output is a **UX Brief** — a structured summary that feeds into `/plan` as Section 2 (Solution Design).

```markdown
## UX Brief: [Feature Name]

### User Context

[From Phase 1 — who, where, when, skill level]

### Key Insights

[From Phase 2 — benchmarks, if run. Otherwise skip.]

### Journey Map

[From Phase 3 — primary flow + key edge cases]

### Wireframe

[From Phase 4 — ASCII or reference to other format]

### Heuristic Compliance

[From Phase 5 — scorecard summary. Any FAIL items = must-fix in plan.]

### Reusable Patterns

[From Phase 6 — existing components to use, new ones needed]

### UX Debt (if any)

[CONCERN items from Phase 5 that won't be addressed in this feature — log in TECHNICAL_DEBT.md UX Debt section]
```

---

## Principles

1. **User first, system second** — Design for the person, then figure out the architecture.
2. **Context is everything** — A button that works great on desktop may be unusable on a greasy tablet in a loud kitchen.
3. **Phases are flexible** — Skip Benchmark for simple features. Spend more time on Journey Map for complex flows. Use judgment.
4. **Reuse over reinvent** — Check existing patterns before designing new ones. Consistency > novelty.
5. **FAIL is a gift** — Finding a UX problem before implementation saves 10x the effort of fixing it after.
6. **ASCII is the default** — Low-fidelity wireframes force focus on interaction design, not visual polish.
7. **Zero training** — If it needs a tutorial, it needs a redesign.

---

## Anti-Patterns

- Skipping straight to wireframes without understanding the user context
- Designing for desktop when the primary device is a tablet
- Ignoring edge cases (empty, error, slow, offline, first-time)
- Over-designing with too many options/actions per screen
- Treating UX as visual design only (it's interaction design + information architecture)
- Not checking existing app patterns (leads to inconsistency)

---

## Skill Pipeline

```
/research → /brainstorm → /ux-design → /plan → /sign-off → /worktree create → implement → /code-review → /qa → commit → push → PR → /review-pr (in develop)
                               ↑
                          you are here (for UI features — skip for backend-only work)
```
