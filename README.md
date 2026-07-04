# PHC Pulse

**openIMIS Hackathon — Track 2: Digital Solutions for Primary Healthcare Financing**

## Problem Statement

Primary healthcare facilities (rural dispensaries, community clinics) are the first point of
contact for most patients across Kenya and similar LMIC settings, yet they are chronically
underfunded — not always for lack of money, but for lack of systems to move funds accurately
and on time. Facility administrators often wait months for payments that depend on manual
reconciliation between enrolment records, paper claim forms, and spreadsheets. Community health
workers (CHWs) complete real field visits that are never recorded, and therefore never
compensated, when connectivity isn't available at the point of care.

openIMIS already connects beneficiaries, providers, and payers, but does not yet model
primary-healthcare-specific financing mechanisms (e.g. capitation) or automate the path from an
enrolled population to an approved, standards-compliant payment.

**PHC Pulse turns enrolment data into an accurate, auditable, interoperable payment, and ensures
field work is captured even when connectivity is not guaranteed.**

## Architecture Overview

PHC Pulse follows openIMIS's modular architecture: new functionality is added as independent
Django and React packages that register with the core platform at startup. No core openIMIS
code is modified.

| Repository | Role |
|---|---|
| `openimis-be-phc_pulse/` | Django backend module — capitation data models, calculation service, GraphQL schema, FHIR R4 `PaymentNotice` builder |
| `openimis-fe-phc_pulse/` | React frontend module — registers into the existing openIMIS navigation menu; facility dashboard, scheme console, FHIR viewer |
| `chw-pwa/` | Standalone offline-first PWA for community health workers; syncs to the backend via a REST webhook once connectivity returns |
| `openimis-be_py/`, `openimis-fe_js/`, `openimis-dist_dkr/` | Forks of the official openIMIS repos, with PHC Pulse registered as a module (see `docker-compose.override.yml` in `openimis-dist_dkr/`) |

**Core data model**: `CapitationRate` → `FacilityEnrolment` → `PaymentBatch` → `PaymentLine`,
drawing enrolment/coverage data from existing openIMIS insuree records.

**Online + offline integration**: the CHW PWA and the openIMIS admin console are intentionally
separate applications that meet at the shared Django backend. A CHW records a visit offline
(saved to local device storage); once the device reconnects, the PWA syncs the record to the
backend via webhook; the same data is then visible to the Scheme/Facility Administrator in the
openIMIS-integrated frontend.

**Stack**: Python/Django/PostgreSQL backend, GraphQL (Graphene-Django) + REST sync endpoint,
HL7 FHIR R4 `PaymentNotice`, React frontend reusing openIMIS's component library, Docker Compose
for orchestration.

## Installation Steps

1. Fork/clone `openimis-dist_dkr`, `openimis-be_py`, and `openimis-fe_js` (already done in this
   repo's sibling folders), alongside this repo's `openimis-be-phc_pulse` and
   `openimis-fe-phc_pulse` modules.
2. In `openimis-dist_dkr/`, copy `.env.example` to `.env` (and `.env.openSearch.example` to
   `.env.openSearch`) if not already present.
3. `docker compose up -d --build db redis migrations backend frontend` from `openimis-dist_dkr/`
   brings up the database, cache, backend (with the PHC Pulse module bind-mounted and installed),
   and a custom-built frontend image with the PHC Pulse React module baked in.
   (OpenSearch, RabbitMQ, and the Celery worker are optional and not required for PHC Pulse's
   core features.)
4. Visit the frontend at the port configured by `HTTP_PORT` in `.env` (default `80`).
5. For the CHW offline app: `cd chw-pwa && npm install && npm start` (or the project's
   documented dev command).

## Known Limitations

- **Development environment network sensitivity**: building the custom frontend image involves
  a large `npm install`; on constrained or unstable connections this can be slow. The
  `Dockerfile.phc_pulse` in `openimis-fe_js/` includes retry and npm-cache-integrity handling to
  make this more resilient.
- **OneDrive-synced working directories** (or other cloud-sync folders) can intermittently lock
  files during `npm install`/Docker builds on Windows; building from a local, non-synced path is
  recommended.
- **OpenSearch, RabbitMQ, and the Celery worker are not wired into the demo stack** — they are
  optional dependencies for observability/async tasks unrelated to PHC Pulse's core capitation,
  FHIR, and CHW-sync features, and were intentionally left out of the minimal local stack.
- **Stretch/Reach tier components** (Output Based Aid Tracker, Facility Performance Scorecard,
  Equipment and Supplies Linkage) are prioritized after the three core components (capitation
  engine, FHIR `PaymentNotice`, offline CHW sync) and may be partial or absent depending on time
  available during the event.

## License

Licensed under the GNU Affero General Public License v3.0 — see [LICENSE](LICENSE).
