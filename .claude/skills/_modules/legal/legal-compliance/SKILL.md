---
name: legal-compliance
description: >-
  Legal compliance officer for your project. Three modes: Audit (monthly sweep),
  Gate (market readiness check), Counsel (ad-hoc legal Q&A).
  Covers data privacy, accessibility, cookies, food safety, marketing,
  consumer protection, PCI, and anti-spam across international jurisdictions.
  Triggers: /legal-compliance, "compliance check", "are we ready for [market]?",
  "can we legally [action]?"
allowed-tools: Read, Glob, Grep, WebSearch, WebFetch, AskUserQuestion, Task, mcp__database__execute_sql, mcp__database__list_tables
---

# Legal Compliance Skill

Your in-house compliance officer. Knows the regulations (reference files), understands your business (reads code, DB, marketing pages), and works in 3 modes.

**Disclaimer**: This skill assists with compliance workflows. It does not provide legal advice. All outputs should be reviewed by qualified legal counsel before being relied upon for binding decisions.

## When to Use

- `/legal-compliance` — monthly audit sweep
- `/legal-compliance gate <jurisdiction>` — "are we ready for the UK?"
- `/legal-compliance "question"` — "can we add SMS marketing?"
- After launching in a new market
- After adding features that collect new data types
- After updating marketing pages or competitor comparisons
- Periodically (monthly recommended, quarterly minimum)

## When NOT to Use

- Debugging code errors (use `/diagnose`)
- Database security audit (use `/db-audit` — complements, doesn't replace)
- Performance issues (use `/perf-audit`)
- Need current external research first (use `/research`, then come back)

---

## Knowledge Base

All legal knowledge lives in `.claude/references/legal/`. The skill reads these at runtime — update the references when laws change, no skill file edits needed.

```
.claude/references/legal/
├── INDEX.md               ← Jurisdiction → regulation mapping
├── GDPR.md                ← EU General Data Protection Regulation
├── CCPA.md                ← California Consumer Privacy Act + CPRA
├── UK-GDPR.md             ← UK GDPR + DUAA 2025 + PECR + Natasha's Law
├── WCAG.md                ← Accessibility (WCAG 2.2 AA + enforcement per jurisdiction)
├── PCI-DSS.md             ← Payment Card Industry Data Security Standard
├── FOOD-SAFETY.md         ← Allergen disclosure + food e-commerce regulations
├── MARKETING.md           ← Truth-in-advertising + anti-spam + competitor claims
└── CONSUMER-PROTECTION.md ← Consumer rights + returns + pricing transparency
```

<!-- FILL: Adjust the reference file list above to match your industry and jurisdictions -->
<!-- FOOD-SAFETY.md is for food service businesses. Replace with your industry's regulations. -->

**Staleness rule**: Each reference file has a `Last Verified` date. If > 6 months old, the skill flags it as YELLOW and suggests running `/research` to refresh that domain.

---

## Mode 1: Audit (Monthly Compliance Sweep)

**Trigger**: `/legal-compliance` or `/legal-compliance audit`

Like `/db-audit` for legal. Runs all automated checks, flags manual items, produces a CEO-brief report.

### Step 1: Read Knowledge Base

Read `.claude/references/legal/INDEX.md` to load the jurisdiction map. Read all reference files to understand current regulatory landscape.

### Step 2: Run Automated Checks

Run each check sequentially. Record GREEN / YELLOW / RED per check.

<!-- FILL: Customize these automated checks for your project's specific pages, components, and data flows -->

| #   | Check                          | Tool                                                                  | What it verifies                                   | GREEN                                           | YELLOW                             | RED                                |
| --- | ------------------------------ | --------------------------------------------------------------------- | -------------------------------------------------- | ----------------------------------------------- | ---------------------------------- | ---------------------------------- |
| A1  | Cookie consent — App           | Grep `src/` for CookieConsent usage                                   | Banner present on all public routes                | Present on all public pages                     | Present but missing on some routes | Missing entirely                   |
| A2  | Cookie consent — Marketing     | Grep marketing site for cookie consent                                | Banner on marketing pages                          | Present                                         | Partial                            | Missing                            |
| A3  | Privacy policy links           | Grep footer components                                                | Links present and pointing to valid pages          | Links in all footers                            | One footer missing link            | No privacy policy link             |
| A4  | Terms of service links         | Grep footer components                                                | Links present and valid                            | Both present                                    | One missing                        | No ToS link                        |
| A5  | Legal page content status      | Read legal pages, check for PLACEHOLDER markers                       | Are legal pages finalized?                         | No placeholder markers                          | Some sections marked draft         | Full PLACEHOLDER banner            |
| A6  | Marketing stats accuracy       | `mcp__database__execute_sql` vs hardcoded stats                       | Claims match reality (+/-20% tolerance)            | Within tolerance                                | 20-50% off                         | >50% off or fabricated             |
| A7  | Competitor claims currency     | Read competitor comparison pages                                      | Pricing/feature claims have dates or are current   | All claims < 6 months old                       | Some claims 6-12 months            | Claims > 12 months or unverifiable |
| A8  | Industry-specific data fields  | `mcp__database__list_tables` for required columns                     | Required data fields exist                         | Required columns present                        | Schema supports but no data        | No required fields                 |
| A9  | ARIA/accessibility basics      | Grep key components for `role=`, `aria-label`, `aria-describedby`     | Basic WCAG markers on interactive elements         | Present on all interactive elements             | Partial coverage                   | Missing on most                    |
| A10 | PCI scope verification         | Grep for payment integration pattern                                  | SAQ A (hosted payment), no direct card handling    | Hosted payment only, no card data touches code  | Hosted but some custom forms       | Direct card number handling        |
| A11 | Data retention policy          | Read data storage and cleanup code                                    | Retention policies active, no unbounded storage    | Cleanup active with defined retention           | Cleanup exists but not all stores  | No retention policy                |
| A12 | Analytics consent gating       | Read analytics integration code                                       | Analytics loads only after consent                 | Gated behind consent                            | Partially gated                    | Loads without consent              |

### Step 3: Flag Manual Checklist Items

Present items that need human/lawyer review. Tag each with jurisdiction and priority.

| #   | Check                          | Jurisdiction     | Priority | What to review                                                               |
| --- | ------------------------------ | ---------------- | -------- | ---------------------------------------------------------------------------- |
| M1  | Privacy policy completeness    | Global           | P0       | Covers all data types collected by your application                          |
| M2  | Terms of service completeness  | Global           | P0       | Liability, governing law, dispute resolution, SaaS terms                     |
| M3  | DPA template for tenants       | EU/UK            | P1       | GDPR Art. 28 Data Processing Agreement between platform and each tenant      |
| M4  | Cookie policy granularity      | EU/UK            | P1       | Per-category opt-in (not just all/nothing)? GDPR requires granular consent   |
| M5  | Right to deletion (DSAR)       | EU/US            | P1       | Process for users to request data deletion (GDPR Art. 17, CCPA)             |
| M6  | Marketing email compliance     | US/Canada        | P2       | CAN-SPAM unsubscribe, CASL express consent for non-transactional            |
| M7  | Competitor comparison accuracy | US/EU            | P1       | FTC Act S5, EU UCPD — claims substantiated and current?                      |
| M8  | Pricing transparency           | EU/US            | P2       | No hidden fees, clear totals, refund policy visible                          |
| M9  | Full WCAG audit                | EU/US/UK         | P1       | axe-core or Lighthouse accessibility on key pages                            |
| M10 | Tax disclosure                 | Per jurisdiction | P2       | VAT/sales tax handling and display                                           |

### Step 4: Check Reference Staleness

For each reference file, check the `Last Verified` date. Flag YELLOW if > 6 months old.

### Step 5: Generate Report

```markdown
## Legal Compliance Audit

**Date**: YYYY-MM-DD
**Platform**: <!-- FILL: your platform name and URLs -->

### Automated Checks

| #   | Check                | Status           | Finding  |
| --- | -------------------- | ---------------- | -------- |
| A1  | Cookie consent (app) | GREEN/YELLOW/RED | [detail] |
| ... | ...                  | ...              | ...      |

**Automated Score**: X/12 GREEN, Y/12 YELLOW, Z/12 RED

### Manual Review Items

| #   | Check          | Jurisdiction | Priority | Status            |
| --- | -------------- | ------------ | -------- | ----------------- |
| M1  | Privacy policy | Global       | P0       | Needs review / OK |
| ... | ...            | ...          | ...      | ...               |

### Reference Staleness

| File    | Last Verified | Status                                    |
| ------- | ------------- | ----------------------------------------- |
| GDPR.md | YYYY-MM-DD    | Current / Stale (re-research recommended) |
| ...     | ...           | ...                                       |

### Critical Findings

[Numbered list — items that need immediate attention]

### Summary

**Overall Status**: [Compliant / Gaps Found / Critical Gaps]
**Automated**: X/12 GREEN
**Manual items pending**: Y/10
**Stale references**: Z/8
**Next audit**: [date — 30 days recommended]
```

---

## Mode 2: Gate (Market Readiness)

**Trigger**: `/legal-compliance gate <jurisdiction>`

Accepted jurisdictions: `EU`, `US`, `UK`, `Canada`, `Australia`, `Lebanon`, `MENA`, `Global`

<!-- FILL: Adjust jurisdiction list to match your target markets -->

### Step 1: Load Jurisdiction Map

Read `.claude/references/legal/INDEX.md`. Identify which reference files apply to the requested jurisdiction.

### Step 2: Read Applicable References

Read only the reference files mapped to that jurisdiction. Extract the "Key Requirements" and platform-specific implications sections.

### Step 3: Run Jurisdiction-Filtered Checks

Run only the automated checks (A1-A12) that are relevant to this jurisdiction. Skip checks that don't apply.

<!-- FILL: Adjust this mapping to your jurisdictions and applicable checks -->

| Jurisdiction | Applicable Automated Checks             |
| ------------ | --------------------------------------- |
| EU           | A1, A2, A3, A4, A5, A6, A7, A8, A9, A12 |
| US           | A1, A3, A4, A5, A6, A7, A9, A10         |
| UK           | A1, A2, A3, A4, A5, A6, A7, A8, A9, A12 |
| Canada       | A1, A3, A4, A5, A6, A7, A9              |
| Australia    | A1, A3, A4, A5, A9                      |
| Global       | All (A1-A12)                            |

### Step 4: Generate Gate Report

```markdown
## Market Gate: [Jurisdiction]

**Date**: YYYY-MM-DD
**Question**: Is [Your Platform] ready for [jurisdiction]?

### Verdict: READY / NOT READY / PARTIALLY READY

### Requirements Checklist

| #   | Requirement   | Regulation | Status                  | Gap              |
| --- | ------------- | ---------- | ----------------------- | ---------------- |
| 1   | [requirement] | [ref]      | Met / Not Met / Partial | [what's missing] |
| ... | ...           | ...        | ...                     | ...              |

### Automated Check Results

| #                      | Check | Status | Finding |
| ---------------------- | ----- | ------ | ------- |
| [filtered checks only] |

### Blocking Gaps (must fix before entering this market)

1. [gap + specific regulation + penalty risk]

### Non-Blocking Gaps (should fix, not legally required)

1. [gap + recommendation]

### Next Step

[Specific action — e.g., "/plan to implement GDPR consent flow" or "consult local counsel for [specific question]"]
```

---

## Mode 3: Counsel (Legal Q&A)

**Trigger**: `/legal-compliance "question"` or natural language legal question

### Step 1: Parse the Question

Identify:

- What legal domains are relevant (privacy, marketing, accessibility, etc.)
- Which jurisdictions apply (or all if unspecified)
- Whether this is about an existing feature or a planned change

### Step 2: Read Applicable References

Read the relevant reference files from `.claude/references/legal/`.

### Step 3: Assess Whether Current Info Is Needed

If the question involves:

- A regulation that may have changed recently
- A specific enforcement action or ruling
- Technology-specific guidance (e.g., "does [service] comply with X?")

Ask the user: "This may benefit from a quick web check for current information. Run `/research` on this?" If yes, perform 1st-gear research (2-3 searches) inline.

### Step 4: Provide Reasoned Advice

```markdown
## Legal Counsel: [Question]

**Domains**: [Privacy, Marketing, etc.]
**Jurisdictions**: [EU, US, etc.]

### Short Answer

[1-3 sentences — the bottom line]

### Analysis

[Jurisdiction-by-jurisdiction breakdown if multiple apply]

| Jurisdiction | Rule                   | Implication for your platform   |
| ------------ | ---------------------- | ------------------------------- |
| EU           | [regulation + article] | [what you must/should/can do]   |
| US           | [regulation]           | [what you must/should/can do]   |

### Recommendation

[Specific action — what to do next]

### Caveats

- [Uncertainty or jurisdiction-specific nuance]
- This is not legal advice — consult qualified counsel for binding opinions

### Sources

[Reference files consulted + any web sources if research was run]
```

---

## Visibility Control — What the CEO Sees

**Show the CEO (interactive moments):**

- Mode selection confirmation (if ambiguous)
- Final report (Audit, Gate, or Counsel output)
- Blocking findings that need decisions

**Do silently (no play-by-play):**

- Reading reference files
- Running automated checks (A1-A12)
- Cross-referencing jurisdictions
- Internal staleness checks

**Why**: Same principle as `/research` — the CEO wants the signal, not the noise. Deliver the report, not the process.

---

## Principles

1. **International-first** — Build to GDPR standard everywhere. It automatically satisfies most other jurisdictions.
2. **Automated where possible, manual where necessary** — Code can check if a cookie banner exists. Only a lawyer can verify privacy policy content.
3. **Reference-driven, not hardcoded** — Laws change. Update `.claude/references/legal/*.md`, not the skill file.
4. **Always disclaim** — Every output includes "consult qualified counsel." This is a tool, not a lawyer.
5. **Flag, don't fix** — The skill identifies gaps. `/plan` creates the fix. Don't mix audit with implementation.
6. **Truth-in-advertising is compliance** — Marketing claims (stats, competitor comparisons, pricing) are legal obligations under FTC Act S5 and EU UCPD.
7. **Both surfaces** — Always audit BOTH your main app AND any marketing/landing sites. They're different codebases with different compliance needs.
8. **Staleness is a finding** — A 2-year-old reference file is a compliance risk. Flag it.

---

## Anti-Patterns

- Making compliance fixes during an audit (audit only — use `/plan` for fixes)
- Skipping the marketing site ("it's just landing pages" — landing pages have legal obligations too)
- Ignoring manual checklist items because automated checks passed
- Treating GREEN on automated checks as "fully compliant" (automated checks are necessary but not sufficient)
- Running Counsel mode for questions that need a real lawyer (contract disputes, litigation risk, regulatory filings)
- Assuming one jurisdiction's rules cover all markets
- Not including the disclaimer

---

## Skill Pipeline

```
/legal-compliance (periodic — monthly/quarterly)
/legal-compliance gate <market> → /plan (to fix gaps) → implement → /legal-compliance gate <market> (re-check)
/legal-compliance "question" → /research (if needed) → /plan (if action needed)
```

Also: `/research` (legal topics) → `/legal-compliance` (to check current state)
Complements: `/db-audit` (database security), `/perf-audit` (performance), `/prod-audit` (production health)

---

## Summary + Next Step (CEO Footer)

After presenting any report, close with:

```
**Summary**: [1 sentence — compliance status in plain language]
**Status**: Clean / X gaps found (Y critical)
**Next step**: [specific action — e.g., "/plan to implement cookie consent on landing site" or "schedule next audit in 30 days"]
```
