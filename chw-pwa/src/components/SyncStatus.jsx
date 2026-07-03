import React, { useCallback, useEffect, useState } from "react";
import { getAllVisits } from "../db";
import { flushQueue } from "../sync";

// Visually obvious for the demo: queued count, per-record status, a big
// "Retry Sync" button. Auto-retries on the browser's `online` event and on
// a Background Sync postMessage from sw.js -- but the manual button is what
// the presenter actually clicks live, since it works in every browser
// regardless of Background Sync support.
const SyncStatus = () => {
  const [visits, setVisits] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  const refresh = useCallback(async () => {
    const all = await getAllVisits();
    setVisits(all.sort((a, b) => (a.timestamp < b.timestamp ? 1 : -1)));
  }, []);

  const runSync = useCallback(async () => {
    setSyncing(true);
    await flushQueue(refresh);
    await refresh();
    setSyncing(false);
  }, [refresh]);

  useEffect(() => {
    refresh();

    const handleOnline = () => {
      setIsOnline(true);
      runSync();
    };
    const handleOffline = () => setIsOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    const handleSwMessage = (event) => {
      if (event.data?.type === "TRIGGER_SYNC") runSync();
    };
    navigator.serviceWorker?.addEventListener("message", handleSwMessage);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
      navigator.serviceWorker?.removeEventListener("message", handleSwMessage);
    };
  }, [refresh, runSync]);

  const pendingCount = visits.filter((v) => v.syncStatus !== "synced").length;

  return (
    <div className="sync-status">
      <h2>
        Sync Status: <span className={isOnline ? "online" : "offline"}>{isOnline ? "ONLINE" : "OFFLINE"}</span>
      </h2>
      <p>
        <strong>{pendingCount}</strong> visit(s) queued locally, not yet synced.
      </p>
      <button onClick={runSync} disabled={syncing || !isOnline}>
        {syncing ? "Syncing..." : "Retry Sync Now"}
      </button>

      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Facility</th>
            <th>Insuree</th>
            <th>Service</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {visits.map((v) => (
            <tr key={v.idempotencyKey}>
              <td>{new Date(v.timestamp).toLocaleString()}</td>
              <td>{v.facilityId}</td>
              <td>{v.insureeId}</td>
              <td>{v.serviceType}</td>
              <td className={`status-${v.syncStatus}`}>{v.syncStatus}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default SyncStatus;
