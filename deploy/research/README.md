# Frozen Jev research run on GitHub

Status: encrypted public export and scheduled activation explicitly approved by the owner.
The active allocation uses `user_data/research/lesson-week-cloud-v2-approved/` on the original
operator computer. Earlier cancelled preparations are unfunded and must not be used.

This standalone controller runs one encrypted, frozen offline replay on a standard public
GitHub Linux runner. It does not install the legacy trading runtime, use a paid runner or
publish plaintext research data. It makes no market or model request in `verify` mode.

The experiment was fixed before its future data: October 17–23, 2026 entry opportunities,
October 24 protective exits, scheduled October 25 at 06:30 UTC. Its scientific source,
lesson and protocol hashes are unchanged. GitHub schedules can be delayed or dropped.

The original persistent USD 3 monthly ledger holds USD 0.504 for this job. Its execution
copy retains historical records and is capped at 168 lifetime reservations. A persistent
remote Git ref claims the study before any market/model call; a duplicate or uncertain
claim cannot authorize another paid draw. Lost or uncertain usage keeps the full original
hold. Successful authenticated collection reconciles the original allocation once.

Required environment secrets in `jev-lesson-week`, restricted to develop:

- `JEV_RESEARCH_ENVELOPE_KEY`: base64 AES-256-GCM key, retained in a private host file.
- `TYPESAFE_API_KEY`: existing provider token; never include either value in Git or logs.

Only allowlisted Python sources, original lesson/evidence/receipts, protocol and funded
execution ledger enter the encrypted input. Git stores only ciphertext and public identities.
Results, journals and execution accounting are encrypted and committed to the dedicated
`research/lesson-week-v2-cloud-claimed` branch. No Actions artifacts/cache/Packages are used.
The scheduled workflow disables itself after its terminal execution attempt.

On the original operator computer, download the encrypted `result.enc` from that branch into
the ignored `user_data/research/lesson-week-cloud-v2-approved/` directory. Then, from the original local
research checkout:

```bash
.venv/bin/python -m deploy.research.cloud collect --directory user_data/research/lesson-week-cloud-v2-approved
```

Collection verifies the encryption, allocation, terminal report and execution ledger. It
imports authenticated failure evidence even if provider usage remains uncertain; in that
case the full original hold stays pending. It never calls the provider or reruns the replay.
The public repository's legacy source is not the frozen research runtime: the controller
restores that exact runtime from the authenticated encrypted snapshot before importing it.
