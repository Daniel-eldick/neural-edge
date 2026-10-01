# Agent handoff

Read [the single reference plan](docs/active/APPRENTICE_TRADER_PLAN.md) first.
2026-09-23: Daniel explicitly authorized implementation. Build and verify offline replay and paper-only foundations. Deployment, unattended workers, paid API calls and real trading still require separate authorization.
2026-09-30: Daniel supplied a TypeSafe token and authorized a total AI budget of USD 3/month.
Paid Jev calls are permitted only through the persistent budget guard. This does not authorize
unattended operation or real trading. Never print credentials or put them in Git.

2026-09-30: Daniel authorized a private static cockpit preview on his existing Vercel account.
No account upgrade, background worker, production/main promotion or real trading is authorized.

The reference plan supersedes the April five-layer architecture and its task queue. User-approved limits are recorded there; proposed defaults are labeled separately.
The offline replay enforces admission limits; the legacy Freqtrade runtime does not. Read the plan's implementation limitations before extending either.

Branch from develop; PRs target develop. Do not merge or push to main as part of this handoff.
Preserve existing source and tests. Never treat archived completion percentages as current readiness.

The runtime is Python; Vercel hosts only an isolated generated HTML report. Never deploy the repository root. For code changes the existing quality commands are:
`ruff check . && mypy . && pytest -x --timeout=30`
For documentation-only changes validate links and diff scope; do not install trading dependencies or launch trading merely to validate prose.
Report expected-failure tests separately from passing implemented behavior.

Inherited framework guides contain stale commands and architectural claims. This root guidance and the active plan govern the current project; preserve safety constraints. Do not edit framework skills during project setup.
