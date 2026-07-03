import React, { useState } from "react";
import { addVisit } from "../db";

// Writes to IndexedDB immediately on submit -- this must work with zero
// network connectivity, per the "airplane mode" demo moment. No fetch call
// happens here at all; syncing is a completely separate step (see
// SyncStatus.jsx / sync.js), triggered by connectivity or a manual retry.
//
// TODO(follow-up): facilityId/insureeId are free-text numeric IDs for now.
// A real CHW-friendly version needs a searchable facility/insuree picker
// (matching openIMIS's core PublishedComponent picker pattern) instead of
// requiring the CHW to know raw database IDs -- not built here since it
// needs a live backend to search against.
const RecordVisit = ({ onRecorded }) => {
  const [facilityId, setFacilityId] = useState("");
  const [insureeId, setInsureeId] = useState("");
  const [serviceType, setServiceType] = useState("");
  const [notes, setNotes] = useState("");
  const [savedMessage, setSavedMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const visit = {
      idempotencyKey: crypto.randomUUID(),
      facilityId,
      insureeId,
      serviceType,
      notes,
      timestamp: new Date().toISOString(),
      syncStatus: "pending",
    };
    await addVisit(visit);
    setSavedMessage(`Saved locally at ${new Date().toLocaleTimeString()} — will sync when online.`);
    setFacilityId("");
    setInsureeId("");
    setServiceType("");
    setNotes("");

    // Best-effort Background Sync registration -- not relied on for the
    // demo (see public/sw.js), but wired up in case the browser supports it.
    if ("serviceWorker" in navigator && "SyncManager" in window) {
      try {
        const registration = await navigator.serviceWorker.ready;
        await registration.sync.register("chw-sync");
      } catch (err) {
        // Background Sync unsupported/unavailable -- fine, the online-event
        // listener and manual Retry Sync button in SyncStatus.jsx cover it.
      }
    }

    if (onRecorded) onRecorded();
  };

  return (
    <form onSubmit={handleSubmit} className="record-visit-form">
      <h2>Record Service Visit</h2>
      <label>
        Facility ID
        <input value={facilityId} onChange={(e) => setFacilityId(e.target.value)} required />
      </label>
      <label>
        Insuree ID
        <input value={insureeId} onChange={(e) => setInsureeId(e.target.value)} required />
      </label>
      <label>
        Service Type
        <input value={serviceType} onChange={(e) => setServiceType(e.target.value)} required />
      </label>
      <label>
        Notes (optional)
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} />
      </label>
      <button type="submit">Save Visit</button>
      {savedMessage && <p className="saved-banner">✓ {savedMessage}</p>}
    </form>
  );
};

export default RecordVisit;
