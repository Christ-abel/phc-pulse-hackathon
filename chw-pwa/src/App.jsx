import React, { useState } from "react";
import RecordVisit from "./components/RecordVisit";
import SyncStatus from "./components/SyncStatus";

function App() {
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="app">
      <h1>PHC Pulse — CHW Field App</h1>
      <RecordVisit onRecorded={() => setRefreshKey((k) => k + 1)} />
      <SyncStatus key={refreshKey} />
    </div>
  );
}

export default App;
