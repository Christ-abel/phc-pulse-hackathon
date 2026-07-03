# PHC Pulse — CHW Field App

Offline-first PWA for community health workers to record service visits in
the field and sync them to PHC Pulse when connectivity returns. Standalone
client of the `phc_pulse` REST webhook (built in Phase 3) — not an openIMIS
frontend module, doesn't go through `openimis.json`.

## How it works

- **Record a visit** (`RecordVisit.jsx`) writes straight to IndexedDB. No
  network call happens on submit — this is what makes it work with zero
  connectivity.
- **Sync** (`sync.js` + `SyncStatus.jsx`) is a separate step, triggered by:
  the browser's `online` event, a Background Sync message from `sw.js`
  (best-effort — not supported in all browsers, e.g. Safari), or the manual
  "Retry Sync Now" button. The manual button is what to click during the
  live demo, since it works regardless of Background Sync support.
- Each visit gets a client-generated UUID (`idempotencyKey`) before it's
  queued, matching the idempotency key the backend webhook checks — safe to
  retry a failed sync without creating duplicate records.

## Running it

```
npm install
npm run dev
```

Opens on `http://localhost:3001`. Set `VITE_PHC_PULSE_API_BASE` (defaults to
`http://localhost:8000`) if the backend isn't on the default port.

## Known gaps (not built yet)

- `facilityId`/`insureeId` are free-text numeric ID fields — a real
  CHW-friendly version needs a searchable facility/insuree picker instead of
  requiring the CHW to know raw database IDs. Not built since it needs a
  live backend to search against.
- No app icons in `manifest.webmanifest` yet — installability will work but
  browsers may warn about missing icons. Add real icons before the demo.
- Entirely unexecuted — built and reasoned about, but never run against a
  live `phc_pulse` webhook (Docker/backend blocked). Test the full offline
  → online → sync loop for real before Day 1, at least twice per the plan.
