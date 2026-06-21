import { useMemo, useState } from "react";
import { BarChart3, ClipboardList, FileCheck2, FilePlus2, Home, Map, Search, ShieldCheck, UserRound, UsersRound } from "lucide-react";
import NavButton from "./components/NavButton";
import LoginPage from "./pages/LoginPage";
import ApplicantDashboard from "./pages/applicant/Dashboard";
import SubmitApplication from "./pages/applicant/SubmitApplication";
import TrackApplication from "./pages/applicant/TrackApplication";
import StaffDashboard from "./pages/staff/Dashboard";
import ApplicationManagement from "./pages/staff/ApplicationManagement";
import ApplicationDetails from "./pages/staff/ApplicationDetails";
import TaskList from "./pages/surveyor/TaskList";
import TaskExecution from "./pages/surveyor/TaskExecution";
import RegistrarReview from "./pages/registrar/RegistrarReview";
import CertificateView from "./pages/registrar/CertificateView";
import AnalyticsDashboard from "./pages/analytics/Dashboard";
import LiveMap from "./pages/map/LiveMap";

const navItems = [
  { id: "login", label: "User Selection", icon: UserRound },
  { id: "applicant-dashboard", label: "Applicant Dashboard", icon: Home },
  { id: "submit", label: "Submit Application", icon: FilePlus2 },
  { id: "track", label: "Track Application", icon: Search },
  { id: "staff-dashboard", label: "Staff Dashboard", icon: ShieldCheck },
  { id: "manage", label: "Application Management", icon: ClipboardList },
  { id: "details", label: "Application Details", icon: FileCheck2 },
  { id: "tasks", label: "Surveyor Tasks", icon: UsersRound },
  { id: "execute", label: "Task Execution", icon: ClipboardList },
  { id: "registrar-review", label: "Registrar Review", icon: ShieldCheck },
  { id: "map", label: "Live Map", icon: Map },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "certificate", label: "Certificate View", icon: FileCheck2 }
];

export default function App() {
  const [view, setView] = useState("login");
  const [role, setRole] = useState(localStorage.getItem("lrmisUiRole") || "staff");
  const [selectedApplication, setSelectedApplication] = useState("LRMIS-2026-0001");

  const title = useMemo(() => navItems.find((item) => item.id === view)?.label || "LRMIS", [view]);

  function chooseRole(next) {
    setRole(next.id);
    localStorage.setItem("lrmisUiRole", next.id);
    localStorage.setItem("lrmisRole", next.apiRole);
    const landing = {
      applicant: "applicant-dashboard",
      staff: "staff-dashboard",
      surveyor: "tasks",
      registrar: "registrar-review",
      manager: "analytics"
    }[next.id];
    setView(landing || "staff-dashboard");
  }

  function openApplication(id) {
    setSelectedApplication(id);
    setView("details");
  }

  function openTask(id) {
    setSelectedApplication(id);
    setView("execute");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <strong>LRMIS</strong>
          <span>COMP4382 Land Registration</span>
        </div>
        <div className="role-switcher">
          <label>Current role
            <select value={role} onChange={(event) => chooseRole({ id: event.target.value, apiRole: event.target.value === "registrar" ? "registrar" : event.target.value === "surveyor" ? "surveyor" : "staff" })}>
              <option value="applicant">Applicant</option>
              <option value="staff">Staff</option>
              <option value="surveyor">Surveyor</option>
              <option value="registrar">Registrar</option>
              <option value="manager">Manager</option>
            </select>
          </label>
        </div>
        <nav className="nav">
          {navItems.map((item) => (
            <NavButton key={item.id} active={view === item.id} icon={item.icon} label={item.label} onClick={() => setView(item.id)} />
          ))}
        </nav>
      </aside>
      <main className="content">
        <div className="topline">
          <h1>{title}</h1>
          <span>{selectedApplication}</span>
        </div>
        {view === "login" && <LoginPage onSelect={chooseRole} />}
        {view === "applicant-dashboard" && <ApplicantDashboard onOpen={openApplication} />}
        {view === "submit" && <SubmitApplication onCreated={(id) => { setSelectedApplication(id); setView("track"); }} />}
        {view === "track" && <TrackApplication initialId={selectedApplication} />}
        {view === "staff-dashboard" && <StaffDashboard />}
        {view === "manage" && <ApplicationManagement onOpen={openApplication} />}
        {view === "details" && <ApplicationDetails applicationId={selectedApplication} />}
        {view === "tasks" && <TaskList onOpen={openTask} />}
        {view === "execute" && <TaskExecution applicationId={selectedApplication} />}
        {view === "registrar-review" && <RegistrarReview />}
        {view === "map" && <LiveMap />}
        {view === "analytics" && <AnalyticsDashboard />}
        {view === "certificate" && <CertificateView />}
      </main>
    </div>
  );
}

