# Private cockpit hosting

Verified 2026-09-30. This hosts a dated results snapshot only. Trading, teacher/memory,
background execution, controls and automatic publishing are not hosted here.

- [Open cockpit](https://neural-edge-cockpit-fnrbbq9de-daniel-eldicks-projects.vercel.app) — sign in with the Vercel account that owns the project.
- [Manage project](https://vercel.com/daniel-eldicks-projects/neural-edge-cockpit)
- Scope: `daniel-eldicks-projects`; project: `prj_sphrTaxgCiGWvkTZhtzQ8GtUCcj2`.
- Preview: `dpl_9eNE8J213h15injrq4WVm2Dxv3xu`; READY, preview target, no aliases.
- Authentication: standard Vercel protection, `prod_deployment_urls_and_all_previews`.
- Uses the existing Pro account, with no plan upgrade, add-on, functions or database.
  Static hosting consumes the account's normal usage allowance; this is not a separate
  promise of a zero invoice. No new AI inference occurred during deployment.

## Refresh procedure

1. Generate the report locally with the README cockpit command, selecting completed journals
   and archives. Inspect its dates, results and any degraded-coverage warning.
2. Stage only `index.html` and the configuration below in an isolated directory outside the
   repository, such as `/private/tmp/neural-edge-cockpit-preview`. Never deploy the repo root.
3. Link this existing project with `vercel link --yes --project neural-edge-cockpit --scope
   daniel-eldicks-projects` from that directory. Link may download `.env.local`; remove that
   generated file from the staging directory, not the real project's credential file.
4. Use a staging `.vercelignore` containing `*`, `!index.html`, `!vercel.json` on separate
   lines. Verify `.vercel/project.json` matches the project and scope above. Check project
   protection still equals `prod_deployment_urls_and_all_previews` before uploading.
5. Run `vercel deploy --target preview --yes --scope daniel-eldicks-projects`.
   Verify the returned deployment is READY, is not production, and has no public aliases.
   CLI 59.3.0 unexpectedly promoted the first upload despite `--target preview`; that
   deployment and alias were removed. Do not trust CLI intent without checking the result. `--skip-domain` is rejected for
   previews by CLI 59.3.0; it cannot be used as a preview safeguard. For any new project,
   validate deployment behavior with an empty non-sensitive page before uploading results.
6. Anonymous access must redirect to Vercel login and contain no report data. From the linked
   directory, use `vercel curl / --deployment <preview-url> --scope daniel-eldicks-projects
   -- --silent -H x-vercel-skip-toolbar:1 --output /private/tmp/cockpit-verified.html` and
   compare its bytes with the staged report. `vercel curl` manages its authorized protection
   token; never print, commit or put that token in a share link. Keep protection enabled.
7. Update the cockpit links in README and this guide to the verified preview URL. Inspect
   desktop/mobile layout after browser login. Browser refresh alone does not regenerate data.

Current access and visual checks passed at 1440×1050 desktop, 820×1180 tablet and 390×844 phone.
The snapshot retains 38 replay/reference records: the degraded February 2024 opportunity
window, three fully covered context-screen windows, three earlier memory-screen windows and
the original pilot/archive. Its overview shows February 2024 context mode by fixed input order
with an Incomplete test warning; May/August/November opportunity windows were never run;
dated evidence groups expose all periods. The hosted HTML matches the local snapshot byte for byte.
Authenticated browser automation reused the existing Vercel project automation credential in
memory, restricted its request header to this deployment origin, and blocked other origins.
No credential was printed, saved in screenshots or placed in a shared URL. Normal browser
access still requires the owner to sign in. Chart radio controls (click and keyboard),
expanded evidence, no horizontal overflow and no browser errors were verified. Vercel injects
its toolbar by default, which our CSP blocks. The documented test header suppresses toolbar
injection for byte comparison without weakening authentication or CSP.

## Static configuration

Save as `vercel.json` in the isolated staging directory:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": null,
  "buildCommand": "",
  "installCommand": "",
  "outputDirectory": ".",
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "private, no-store"
        },
        {
          "key": "X-Robots-Tag",
          "value": "noindex, nofollow, noarchive"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "Referrer-Policy",
          "value": "no-referrer"
        },
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'none'; style-src 'unsafe-inline'; img-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
        }
      ]
    }
  ]
}
```

The report's source snapshot and runtime journals remain ignored local artifacts. No Git
integration or automatic deployment is configured. To roll back hosting, remove this preview
from the Vercel project; retain all local journals and the AI budget ledger.

References: [Vercel Authentication](https://vercel.com/docs/deployment-protection/methods-to-protect-deployments/vercel-authentication),
[toolbar suppression for tests](https://vercel.com/docs/vercel-toolbar/managing-toolbar#disable-toolbar-for-automation).

## Live updates: local implementation, online connection pending

2026-10-01: `web/cockpit/` implements the replacement shell and private read endpoint.
It has not replaced the static preview linked above. The local source currently holds 38
actual replay/reference records; completed results retain their historical dates and warnings.
The page polls metadata every 30 seconds while visible. A local observer publishes source
status every 60 seconds and refreshes results only when completed evidence changes. It is
read-only: it cannot start a replay, change a strategy, call Jev or place an order.

A successful HTTP response never makes old source data fresh. After 180 seconds without a
source heartbeat, the page says “Publisher offline or delayed” and reports unknown agent
status. Network/authentication failures retain the last loaded charts. A source verification
failure is explicit and retains the last good report. Chart choice and open evidence survive
result updates. “Updates connected” means the dashboard source is reachable, not that trading
or learning is taking place. Publication timestamps include the viewer's timezone; market
periods remain historical UTC.

### Local operation

Use Python from the project environment and Node 22 or newer. No new npm dependencies.
Create an ignored `user_data/cockpit/live-sources.json` with explicit local inputs, for example:

```json
{
  "roots": ["user_data/research"],
  "archives": ["user_data/backtest_results/backtest-result-2026-04-06_04-41-23.zip"],
  "references": []
}
```

The already configured local file also includes seven reference groups; do not replace it with
this minimal example or silently remove those comparisons. Each reference entry specifies
`baseline`, `candles`, and replay `settings`; data hash and settings must match the recorded
baseline. Use a separate output directory when intentionally changing source configuration.

```bash
.venv/bin/python -m src.cockpit.live --config user_data/cockpit/live-sources.json --output user_data/cockpit/live --watch
```

In a separate terminal, for local viewing only:

```bash
node web/cockpit/local.mjs user_data/cockpit/live
```

Open `http://127.0.0.1:8765`. The test server binds only to loopback and serves an explicit
asset allowlist. It is not a public hosting or authentication service. The current processes
are terminal-session processes on Daniel's Mac, not login services; no autostart or 24/7 host
has been installed. Sleep, shutdown or closing the process stops source updates.

The observer holds an OS advisory lock and refuses duplicate observers for the same output.
Stopping with Ctrl+C or SIGTERM releases that lock; an existing lock file is not a stale lock.
It persists a private source inventory and hash-verified report metadata for restart recovery.
Corrupt generated state or a changed source configuration fails explicitly; source journal
corruption is instead displayed as unavailable while retaining verified earlier results.
Original journals and the inference budget ledger remain authoritative and untouched.

### Pending online activation

Requested storage: dedicated **Upstash Redis free** plan, preview environment only,
`autoUpgrade=false`, `prodPack=false`, `eviction=false`, region `iad1`. The native Vercel
integration command returned `integration_terms_acceptance_required`; no resource was created.
The owner must accept the [Vercel Upstash terms](https://vercel.com/daniel-eldicks-projects/~/integrations/accept-terms/upstash?source=cli)
and then tell the assistant to continue. Do not bypass this with temporary/unclaimed storage
or silently accept legal terms. Do not upgrade the plan.

After acceptance, the assistant still must:

1. Provision and verify the dedicated free resource/disabled upgrades, connected only to this
   project's preview environment. Preserve all existing account/project integrations.
2. Securely configure `KV_REST_API_URL`, `KV_REST_API_TOKEN` for the local publisher and
   `KV_REST_API_READ_ONLY_TOKEN` for the server reader. Keep local publisher credentials in
   a separately ignored file with mode 0600, never chat, tracked source, command-line arguments
   or the browser. Do not overwrite the existing Jev environment file. No browser storage SDK.
3. Add `--publish` to the Python observer command in an environment containing those storage
   credentials. `publish.mjs` is an internal one-shot helper; Python owns the lock, retries and
   process lifetime. Upload failures retry at 60/120/240/300-second intervals and do not advance
   the confirmed revision or cloud timestamp. Unchanged reports are not uploaded repeatedly.
4. Stage only deploy-allowed files from `web/cockpit/` in an isolated directory. The allowlist
   excludes the publisher, test server, tests, local inputs, journals and credential files.
   Keep project protection enabled, deploy a preview, check actual target and empty aliases.
5. Verify both HTML and API reject anonymous access. Authenticate and verify a real source
   heartbeat advances without redeployment; stop source → stale → resume → connected. Confirm
   all 38 result/reference records and incomplete-study warning remain present. Recheck layouts.
6. Record the verified deployment and update the online links. Until then, use the existing
   static preview or the local live demo; do not claim online live updates are running.

The API exposes only fixed sanitized status/report keys and GET requests. The cloud stores
only sanitized report HTML and status; a changed report and its metadata publish atomically.
The reader requires the read-only token. Browser code receives neither storage credentials
nor raw prompts, databases or budget internals. Strict CSP, no-store/noindex and a script-free
sandboxed report frame remain in place. Two separate output directories would not share a
lock: one configured publisher is supported per private store.

Free Redis currently includes 500,000 commands/month and 256 MB. One continuously visible
tab plus a 60-second publisher is approximately 132,000 status commands per 31-day month,
plus changed-report reads/writes; more tabs add usage. The selected free plan must not auto-upgrade.
Vercel serverless/transfer usage still consumes the existing Pro allowance, so this is not a
promise of a zero account invoice. No inference spend or paid-plan change was made here.
See [Upstash pricing](https://upstash.com/pricing/redis),
[REST API](https://upstash.com/docs/redis/features/restapi), and
[the Vercel integration](https://vercel.com/marketplace/upstash).

Rollback: stop the observer's publication and return to the existing protected static preview.
Never remove local research evidence or reset pending AI charges as part of dashboard rollback.
