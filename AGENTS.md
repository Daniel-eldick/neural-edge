# Agent handoff

Read [the single reference plan](docs/active/APPRENTICE_TRADER_PLAN.md) first.
Current authorization: documentation and organization only. Do not build, deploy, start workers, spend API credits or enable live trading without the next explicit request.

The reference plan supersedes the April five-layer architecture and its task queue. User-approved limits are recorded there; proposed defaults are labeled separately.
Existing runtime code does not yet enforce the new limits.

Branch from develop; PRs target develop. Do not merge or push to main as part of this handoff.
Preserve existing source and tests. Never treat archived completion percentages as current readiness.

This is Python, not a Node/Vercel project. For code changes the existing quality commands are:
`ruff check . && mypy . && pytest -x --timeout=30`
For documentation-only changes validate links and diff scope; do not install trading dependencies or launch trading merely to validate prose.
Report expected-failure tests separately from passing implemented behavior.

Inherited framework guides contain stale commands and architectural claims. This root guidance and the active plan govern the current project; preserve safety constraints. Do not edit framework skills during project setup.
