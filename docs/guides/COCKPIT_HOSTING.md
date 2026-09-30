# Private cockpit hosting

Verified 2026-09-30. This hosts a dated results snapshot only. Trading, teacher/memory,
background execution, controls and automatic publishing are not hosted here.

- [Open cockpit](https://neural-edge-cockpit-6wkzon4c2-daniel-eldicks-projects.vercel.app) — sign in with the Vercel account that owns the project.
- [Manage project](https://vercel.com/daniel-eldicks-projects/neural-edge-cockpit)
- Scope: `daniel-eldicks-projects`; project: `prj_sphrTaxgCiGWvkTZhtzQ8GtUCcj2`.
- Preview: `dpl_2ynMHRtaXrKzjS7tdG9M1mAwk3Nn`; READY, preview target, no aliases.
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

Current access and visual checks passed at 1440px desktop, 820px tablet and 390px phone widths.
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
