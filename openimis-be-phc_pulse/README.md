# PHC Pulse

A capitation and output-based-aid (OBA) payment module for primary
healthcare facilities, built on openIMIS for Track 2 (Digital Solutions for
Primary Healthcare Financing) of the openIMIS Hackathon.

## The problem: the Cost of Silence

Primary healthcare facilities — rural dispensaries, health centres — are the
first point of contact for most patients, but they're also the lowest
level of the health financing system, and often the last to get paid.
Capitation and output-based-aid disbursements are calculated by hand,
reconciled from paper registers, and take months to reach a facility like
Kyangwithya Dispensary. In that gap: nurses wait for payments that may
never arrive, community health workers do unpaid, untracked work, and
scheme administrators have no real-time picture of what's owed to whom.
That delay and opacity is the Cost of Silence — and every month it persists
is a month a real facility runs short.

PHC Pulse is an intelligence layer on top of openIMIS, not a replacement
for it: it automates the capitation calculation, gives facility
administrators a plain-language dashboard of what they're owed and why,
gives scheme administrators a fast, audit-ready approval flow, and gives
community health workers an offline-first way to record field visits that
sync automatically once they're back in range.

## Architecture

```
openIMIS core (Django + React, existing)
 ├─ openimis-be-phc_pulse   Django app: capitation models, GraphQL API,
 │                          FHIR R4 PaymentNotice conversion, REST webhook
 │                          for CHW sync
 ├─ openimis-fe-phc_pulse   React module: Facility Dashboard, Scheme
 │                          Console, FHIR PaymentNotice viewer
 └─ chw-pwa                 Standalone offline-first PWA (IndexedDB +
                             service worker), syncs to the REST webhook —
                             not an openIMIS module, doesn't need Docker
```

Data flow: a `FacilityEnrolment` snapshot (enrolled population per
facility/product/period) plus a `CapitationRate` (per-head rate per
product/period) feed `run_capitation_cycle`, which produces a draft
`PaymentBatch` of `PaymentLine`s. A scheme administrator approves the batch
in the Scheme Console; each `PaymentLine` can be viewed as a FHIR R4
`PaymentNotice` resource. Separately, CHWs record visits offline in the PWA;
each visit is idempotency-keyed and POSTed to `/phc_pulse/webhook/chw-sync/`
once connectivity returns.

*(Turn this into an actual diagram image before the demo — the block/arrow
description above is meant to be redrawn, not pasted as-is.)*

## Repo layout

This is a multi-repo openIMIS module, following the platform's own
convention (core + independently pip/npm-installed modules), not a
monorepo:

- `openimis-be-phc_pulse/` — this repo, the Django backend module
- `openimis-fe-phc_pulse/` — the React frontend module (sibling directory)
- `chw-pwa/` — the standalone CHW PWA (sibling directory)
- `openimis-be_py/`, `openimis-fe_js/`, `openimis-dist_dkr/` — forked
  openIMIS core repos (siblings), with `openimis.json` in each pointing at
  our modules, and a `docker-compose.override.yml` in `openimis-dist_dkr/`
  wiring everything together

All five directories are expected to be siblings under one parent folder
(e.g. `openimis-hackathon/`).

## Installation

1. Fork `openimis-dist_dkr`, `openimis-be_py`, and `openimis-fe_js` from
   github.com/openimis into your own account.
2. Clone your forks as siblings, alongside this repo, `openimis-fe-phc_pulse/`,
   and `chw-pwa/`, all under one parent directory.
3. From `openimis-dist_dkr/`, run:
   ```
   docker compose up -d
   ```
   **Use `docker compose` (space) — the newer Compose v2 CLI bundled with
   Docker Desktop.** This project's `compose.yml` uses the `include:`
   directive, which the legacy standalone `docker-compose` (hyphenated)
   binary does not support.
4. Once the stack is up, load the seed data:
   ```
   docker compose exec backend python manage.py seed_demo_data
   ```
5. Open `http://localhost` for the openIMIS UI, log in with `admin`/`admin`,
   and navigate to the PHC Pulse menu entries (Facility Dashboard, Scheme
   Console).
6. For the CHW PWA (separate, standalone — doesn't need the Docker stack to
   load, but needs the backend running to actually sync):
   ```
   cd chw-pwa
   npm install
   npm run dev
   ```
   Opens on `http://localhost:3001`.

## Known limitations

Built and reasoned about carefully, but genuinely unexecuted against a real
Docker engine at the time of writing (blocked on a laptop BIOS/virtualization
issue during the build). Be honest about these if a judge asks:

- **No predictive layer.** The original pitch's chronic-illness risk
  flagging isn't built — cut deliberately to keep scope real. It's a
  roadmap item, not a hidden gap.
- **Single scheme/product only.** Multi-scheme support (comparing
  capitation across different benefit packages) isn't built.
- **FHIR `recipient` and `payee` both point at the same facility
  Organization.** In real FHIR semantics these are usually different
  parties (the org paid vs. the org being notified) — we haven't modelled
  a separate Payer/Scheme Organization yet.
- **The FHIR `payment` reference points at a `PaymentReconciliation`
  resource that doesn't actually exist** as a dereferenceable resource in
  this module — it's a syntactically valid but non-resolvable FHIR
  reference, a placeholder for a resource we didn't build.
- **The CHW sync webhook is unauthenticated** (`AllowAny`), with all synced
  records attributed to a shared system account. This is a real security
  gap, not a style choice — needs per-device/per-CHW auth before any real
  deployment.
- **No facility/insuree picker.** Both the CHW PWA and the facility
  dashboard's wiring assume you already know raw database IDs, not a
  searchable name/code lookup.
- **The Docker Compose override that wires this module into the stack is
  unverified.** It's grounded in reading the actual Dockerfiles/entrypoint
  scripts in `openimis-be_py`/`openimis-fe_js`, not in a working build —
  budget real debugging time for it, don't assume it works first try.
- **Django migrations for the four `phc_pulse` models don't exist yet** —
  they're generated, not hand-written; run
  `python manage.py makemigrations phc_pulse` once the stack is up.

## Roadmap (not built)

- Predictive chronic-illness risk flagging on top of claims history
- Multi-scheme / multi-product capitation comparison
- Real Payer/Scheme Organization modelling for correct FHIR `recipient`
- SMS/push notification to CHWs on payment (Africa's Talking or similar)
- Location-hierarchy filtering for payments/reports (ward/sub-county/county)
