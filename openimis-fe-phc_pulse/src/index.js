import reducer from "./reducer";
import FacilityDashboard from "./pages/FacilityDashboard";
import SchemeConsole from "./pages/SchemeConsole";

const ROUTE_FACILITY_DASHBOARD = "phc_pulse/facility_dashboard";
const ROUTE_SCHEME_CONSOLE = "phc_pulse/scheme_console";

export const PhcPulseModule = (cfg = {}) => ({
  "core.Router": [
    { path: ROUTE_FACILITY_DASHBOARD, component: FacilityDashboard },
    { path: ROUTE_SCHEME_CONSOLE, component: SchemeConsole },
  ],
  "core.MainMenu": [
    {
      id: "phc_pulse",
      text: "phcPulse.mainMenu",
      icon: "assessment",
      entries: [
        { text: "phcPulse.mainMenu.facilityDashboard", path: `/${ROUTE_FACILITY_DASHBOARD}` },
        { text: "phcPulse.mainMenu.schemeConsole", path: `/${ROUTE_SCHEME_CONSOLE}` },
      ],
    },
  ],
  "core.Reducers": [{ phcPulse: reducer }],
});
