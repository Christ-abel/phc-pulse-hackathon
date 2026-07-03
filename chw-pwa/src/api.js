// Backend base URL is configurable since this PWA runs standalone, separate
// from the openIMIS frontend shell's dev proxy. Points at the phc_pulse
// webhook built in Phase 3 -- note the URL uses "phc_pulse" (underscore),
// the module's real registered name, not "phc-pulse" as earlier drafts of
// the plan assumed.
const API_BASE = import.meta.env.VITE_PHC_PULSE_API_BASE || "http://localhost:8000";
const SYNC_ENDPOINT = `${API_BASE}/phc_pulse/webhook/chw-sync/`;

export async function syncVisit(visit) {
  const response = await fetch(SYNC_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      facility_id: visit.facilityId,
      insuree_id: visit.insureeId,
      service_type: visit.serviceType,
      timestamp: visit.timestamp,
      idempotency_key: visit.idempotencyKey,
    }),
  });
  if (!response.ok) {
    throw new Error(`Sync failed with status ${response.status}`);
  }
  return response.json();
}
