# PHC Pulse — 8-Minute Demo Script

Three short scenes, one recurring character per scene, built around the
actual pages/components in this repo. Rehearse this at least twice on the
real presentation laptop before Day 1 — timings below are targets, not
guarantees, and the airplane-mode moment in particular needs a dry run.

**Before you start:** seed data loaded (`manage.py seed_demo_data`), a draft
`PaymentBatch` already generated (`manage.py run_capitation_cycle <start>
<end>`) so Scene 2 has something to approve, and the CHW PWA
(`chw-pwa`, `npm run dev`) open in a second browser tab/window.

---

## 0:00–0:30 — The Hook

> "Healthcare in Kenya is fragmented. When a patient moves between
> facilities, their history disappears — doctors treat blind, tests get
> repeated, money gets wasted. That's the Cost of Silence. PHC Pulse is an
> intelligence layer on top of openIMIS that fixes the money side of that
> problem first: getting capitation payments to rural facilities in
> seconds, not months."

Cut straight to Scene 1 — no slides, go to the browser.

## 0:30–3:00 — Scene 1: Agnes, the Facility Nurse

**Page:** Facility Dashboard (`openimis-fe-phc_pulse/src/pages/FacilityDashboard.js`)

- "This is Agnes. She runs Kyangwithya Dispensary. Before PHC Pulse, she
  waited months for capitation payments with no idea why the amount was
  what it was."
- Open the Facility Dashboard for Kyangwithya. Point at the amount owed and
  the plain-language explanation line ("calculated as your enrolled
  population multiplied by the per-head rate...").
- "No jargon, no GraphQL, no spreadsheet. Agnes sees exactly what she's
  owed and why, today."
- Scroll to payment history — show a prior period already paid, to signal
  this isn't a one-off demo record.

**Timing check:** if running long, cut the payment-history scroll — the
amount + explanation is the point of this scene, not the table.

## 3:00–5:30 — Scene 2: Margaret, the Scheme Administrator

**Pages:** Scheme Console + FHIR PaymentNotice Viewer

- "This is Margaret. She approves capitation payments for the whole
  scheme. Before PHC Pulse: spreadsheets, manual reconciliation, days of
  delay per batch."
- Open Scheme Console. Show the draft batch with its facility count and
  total.
- Click **Approve Batch** → confirmation dialog appears → click **Yes,
  Approve**. *(Two clicks. Say it out loud: "Two clicks.")*
- Batch drops off the draft list, or — if narrating live — refresh to show
  status now `approved`.
- **The FHIR moment.** Go back to a facility's payment line, click **View
  FHIR PaymentNotice**. Let the JSON sit on screen for a beat.
  > "This is the language of modern healthcare interoperability — HL7 FHIR
  > R4. We generate this automatically, replacing what used to be weeks of
  > spreadsheets with seconds of precision. Every field here — status,
  > amount, payment reference, recipient — is a real openIMIS Organization
  > and Product, not mocked data."
  - *(Be ready for a question here: recipient and payee currently both
    point at the same facility Organization — say so plainly if asked,
    don't dodge it.)*

## 5:30–8:00 — Scene 3: Joseph, the Community Health Worker

**App:** `chw-pwa` (standalone, separate tab)

- "This is Joseph. He does vital fieldwork in villages with no signal —
  and until now, that work was invisible. Unrecorded, unpaid."
- Open the CHW PWA. **Physically turn off wifi/data on the laptop now** —
  this is the most impressive technical beat, don't skip it or fake it.
- Fill in a visit (facility, insuree, service type) and click **Save
  Visit**. Point at the green "Saved locally" banner and the Sync Status
  panel showing `OFFLINE` / `1 visit(s) queued locally`.
  > "That record just wrote to IndexedDB, entirely on-device. Zero
  > network. This is what Joseph's actual work day looks like."
- **Turn wifi back on.** Watch the status flip to `ONLINE` and the record
  sync automatically (or click **Retry Sync Now** if it doesn't fire
  immediately — say "and if it doesn't auto-fire, one tap" and click it).
- Status flips to `synced`.
  > "Joseph's work is now tracked, timestamped, and — once payment logic
  > extends to CHW performance pay — payable. No paper, no lost reports."

## 8:00 — Close

> "Agnes gets paid on time. Margaret approves in two clicks with an
> audit-ready FHIR trail. Joseph's fieldwork finally counts. Multiply that
> across the roughly 2 billion Kenyan shillings that move through this
> system every month — we're not just coding a module. We're fixing the
> plumbing of Kenya's health economy."

---

## If something breaks live

- **Dashboard shows no payment for the period:** re-run `manage.py
  run_capitation_cycle <period_start> <period_end>` before going on stage,
  and confirm the period matches what the frontend queries for.
- **Approve button does nothing / no confirmation dialog:** check the
  browser console for a GraphQL error first — most likely cause is the
  `approvePaymentBatch` mutation hitting a stale `batchId`.
- **FHIR viewer shows "No FHIR PaymentNotice available":** the
  `fhirPaymentNotice` GraphQL field failed to resolve — check the backend
  logs for a FHIR validation error before assuming it's a frontend bug.
- **PWA sync doesn't fire on reconnect:** click **Retry Sync Now**
  manually — this is expected to sometimes be necessary (see the
  Background-Sync-is-best-effort note in `chw-pwa/README.md`), and is why
  the manual button exists. Don't panic on stage, just click it.
