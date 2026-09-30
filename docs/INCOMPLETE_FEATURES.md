# INCOMPLETE FEATURES

Current status (2026-09-30): offline replay/risk foundation, restart recovery, daily reporting and visual comparison cockpit implemented and browser-verified on desktop, tablet and phone. Jev filters candidates with durable responses and a USD 3/month cap. The first real historical pilot completed, but its 100-attempt cap left 11 candidates unevaluated; it establishes no edge. An opt-in deterministic evidence teacher and causal same-run memory are implemented and tested. The [first three-window memory screen](research/MEMORY_SCREEN_V1.md) completed with full coverage and zero policy errors; the tiny sample does not establish a learning advantage. Broader trader decisions, a generative teacher, robust learning evaluation, automatic online updates and operating controls remain unfinished. A private static Vercel preview is now deployed; see [hosting/access](guides/COCKPIT_HOSTING.md). See the reference plan and linked pilot report for evidence.

Use [the single reference plan](active/APPRENTICE_TRADER_PLAN.md) for findings, blockers, milestones, acceptance tests and deferred scope. This page is retained as a compatibility entry point, not a second task list.

Initial [foundation curriculum](curriculum/FOUNDATIONS.md) assembled: five verified primary
sources and six lesson/exercise cards. Six separate runtime cards are now available to the
opt-in memory policy only from 2026-09-30 UTC. Historical pilot runs remain memory-free.
Measured learning and competency evaluation remain unfinished.

Recurring market-pattern recognition is now an explicit requirement. Frozen Jev input is
21 base-interval bars; memory mode adds bounded trade memory. Opt-in `jev-context` now adds
causal daily/weekly OHLCV history, with explicit unknown states and tested recovery. The first
[context screen](research/CONTEXT_SCREEN_V1.md) is complete with verified daily data: it
avoided memory-only losses by always waiting, matching cash across three falling periods.
Broader market coverage, missed-opportunity evaluation, chart-pattern retrieval and
multi-cycle evaluation remain unfinished. See the single plan's section 7.
Formal [teacher/memory QA](reviews/2026-09-30_TEACHER_MEMORY_QA.md) passed with warnings.

The [comparison screen review and Full QA](reviews/2026-09-30_MEMORY_SCREEN_QA.md) passed with warnings: 190 tests passed, 17 existing expected failures.

[Daily/weekly context QA](reviews/2026-09-30_MARKET_CONTEXT_QA.md): 215 passed, 17 existing expected failures; no new paid inference or real context study.

[Context-study review and Full QA](reviews/2026-09-30_CONTEXT_SCREEN_QA.md): 228 passed, 17 existing expected failures. No learned-edge or operating-readiness claim.
