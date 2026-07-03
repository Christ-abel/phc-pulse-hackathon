import { getAllVisits, updateVisitStatus } from "./db";
import { syncVisit } from "./api";

// Each visit already carries a client-generated idempotencyKey (see
// RecordVisit.jsx), and the backend webhook (Phase 3) treats that key as
// its idempotency check -- so retrying a "failed" visit here, or double
// -triggering a sync from both the online-event listener and the
// Background Sync message, can never create a duplicate ServiceRecord.
export async function flushQueue(onProgress) {
  const visits = await getAllVisits();
  const pending = visits.filter((v) => v.syncStatus === "pending" || v.syncStatus === "failed");

  for (const visit of pending) {
    try {
      await syncVisit(visit);
      await updateVisitStatus(visit.idempotencyKey, "synced");
    } catch (err) {
      await updateVisitStatus(visit.idempotencyKey, "failed");
    }
    if (onProgress) onProgress();
  }
}
