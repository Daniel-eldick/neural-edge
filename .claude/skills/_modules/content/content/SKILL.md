# Content Skill

Generate on-brand content for any channel using your project's canonical brand identity.

## When to Use

- `/content`, "write a post", "draft content for", "create copy for"
- Any content creation task: social posts, landing page copy, email outreach, product UI copy, community posts

## When NOT to Use

- Brand strategy decisions (use `/brainstorm`)
- Content performance optimization (use `/self-optimize` with `social-content` lens)
- Product UI implementation (use `/plan`)

---

## Step 1: Load Brand Context

Read these files before writing anything:

<!-- FILL: Update these paths to match your project's brand/marketing file structure -->
1. `marketing/brand/voice.md` — personality, tone, We Are/Are Not, copy rules
2. `marketing/brand/strategy.md` — positioning, differentiators, partnership model
3. `marketing/brand/audience.md` — who we're writing for, their fears, trust signals
4. `marketing/content/guidelines.md` — format rules per platform

---

## Step 2: Clarify the Brief

Use `AskUserQuestion` if any of these are unclear:

| Question        | Why it matters                                         |
| --------------- | ------------------------------------------------------ |
| **Channel**     | Determines tone register (see Voice Chart in voice.md) |
| **Goal**        | Awareness, engagement, conversion, community?          |
| **Audience**    | Which persona segment? (use audience.md)               |
| **Topic**       | What specific subject or feature?                      |
| **Constraints** | Character limit, platform rules, existing campaign?    |

---

## Step 3: Draft Content

### Pre-Flight Checklist (before writing)

<!-- FILL: Customize these checks to match your brand voice and positioning -->
- [ ] Am I using the right terminology for the target audience?
- [ ] Is the product invisible and the user's craft/goal the hero?
- [ ] Am I being warm and direct (not corporate, not startup-bro)?
- [ ] Does this match the channel's tone register?
- [ ] Am I showing, not telling?

### Write the Draft

Generate 2-3 variations when possible. Present them with brief rationale for each approach.

### Post-Draft Review

Run every draft through these gates:

| Gate                | Check                                                      |
| ------------------- | ---------------------------------------------------------- |
| **Voice alignment** | Does it sound like us? Check against We Are/Are Not        |
| **Copy rules**      | All rules in voice.md followed?                            |
| **Audience fit**    | Would our persona (audience.md) understand and trust this? |
| **No violations**   | No urgency tactics, no superlatives, no competitor attacks |
| **Platform fit**    | Meets format rules in guidelines.md?                       |

---

## Step 4: Present and Log

Present the draft(s) to the user. After approval:

<!-- FILL: Update the log path to match your project's content tracking file -->
- Remind user to log the published content in `marketing/content/log.md`

---

## Content Type Templates

### Social Post

```
[Hook — 1 line that stops the scroll]

[Value — 1-2 lines that deliver insight or relatability]

[CTA — 1 line, soft ask]

[Hashtags — 3-5 max, topic-specific]
```

### Comparison Page Section

```
1. Acknowledge competitor — what they do well (1-2 sentences)
2. Show difference — factual, no spin
3. Who each is best for — honest, including when competitor wins
4. Present your product — values-first, not feature-dump
5. CTA — "Try the demo. See the difference for yourself."
```

### Outbound Email

```
Subject: [Under 50 chars, personal, no urgency]

[1 line — connect to their world]
[1-2 lines — value proposition]
[1 line — clear CTA]

[Signature]
```

---

## Principles

1. **Brand voice is non-negotiable** — every word must align with voice.md
2. **Audience-first** — write for the person in audience.md, not for us
3. **Show variations** — let the CEO choose the angle
4. **Log everything** — published content goes in the content log
5. **Craft over features** — lead with their passion, not our capabilities

---

## Skill Pipeline

```
/brainstorm (if strategy unclear) → /content → publish → log → /self-optimize social-content (measure)
```
