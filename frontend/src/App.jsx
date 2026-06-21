import { useMemo, useState } from "react";
import { BarChart3, ClipboardList, FileCheck2, FilePlus2, Home, LogOut, Map, Search, Settings, ShieldCheck, UsersRound } from "lucide-react";
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
import AdminPanel from "./pages/admin/AdminPanel";

const navItems = [
  { id: "applicant-dashboard", label: "Applicant Dashboard", icon: Home, roles: ["applicant"] },
  { id: "submit", label: "Submit Application", icon: FilePlus2, roles: ["applicant"] },
  { id: "track", label: "Track Application", icon: Search, roles: ["applicant"] },
  { id: "staff-dashboard", label: "Staff Dashboard", icon: ShieldCheck, roles: ["supervisor", "admin"] },
  { id: "manage", label: "Application Management", icon: ClipboardList, roles: ["registrar", "supervisor", "admin"] },
  { id: "details", label: "Application Details", icon: FileCheck2, roles: ["registrar", "supervisor", "admin"] },
  { id: "tasks", label: "Surveyor Tasks", icon: UsersRound, roles: ["surveyor", "supervisor", "admin"] },
  { id: "execute", label: "Task Execution", icon: ClipboardList, roles: ["surveyor", "supervisor", "admin"] },
  { id: "registrar-review", label: "Registrar Review", icon: ShieldCheck, roles: ["registrar", "supervisor", "admin"] },
  { id: "map", label: "Live Map", icon: Map, roles: ["supervisor", "admin"] },
  { id: "analytics", label: "Analytics", icon: BarChart3, roles: ["supervisor", "admin"] },
  { id: "certificate", label: "Certificate View", icon: FileCheck2, roles: ["applicant", "registrar", "supervisor", "admin"] },
  { id: "admin", label: "Admin Panel", icon: Settings, roles: ["supervisor", "admin"] }
];

export default function App() {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("lrmisUser");
    return raw ? JSON.parse(raw) : null;
  });
  const [view, setView] = useState(() => landingFor(JSON.parse(localStorage.getItem("lrmisUser") || "null")));
  const [selectedApplication, setSelectedApplication] = useState("LRMIS-2026-0001");

  const visibleNav = useMemo(() => navItems.filter((item) => user && item.roles.includes(user.role)), [user]);
  const title = useMemo(() => navItems.find((item) => item.id === view)?.label || "LRMIS", [view]);

  function handleLogin(nextUser) {
    setUser(nextUser);
    setView(landingFor(nextUser));
  }

  function logout() {
    localStorage.removeItem("lrmisToken");
    localStorage.removeItem("lrmisUser");
    setUser(null);
    setView("login");
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
        {user ? (
          <div className="user-card">
            <strong>{user.full_name}</strong>
            <span>{user.role} - {user.actor_id}</span>
            <button onClick={logout}><LogOut size={16} /> Logout</button>
          </div>
        ) : null}
        <nav className="nav">
          {visibleNav.map((item) => (
            <NavButton key={item.id} active={view === item.id} icon={item.icon} label={item.label} onClick={() => setView(item.id)} />
          ))}
        </nav>
      </aside>
      <main className="content">
        <div className="topline">
          <h1>{title}</h1>
          <span>{user ? selectedApplication : "Please log in"}</span>
        </div>
        {!user && <LoginPage onLogin={handleLogin} />}
        {user && view === "applicant-dashboard" && <ApplicantDashboard applicantId={user.actor_id} onOpen={openApplication} />}
        {user && view === "submit" && <SubmitApplication user={user} onCreated={(id) => { setSelectedApplication(id); setView("track"); }} />}
        {user && view === "track" && <TrackApplication initialId={selectedApplication} user={user} />}
        {view === "staff-dashboard" && <StaffDashboard />}
        {view === "manage" && <ApplicationManagement onOpen={openApplication} />}
        {user && view === "details" && <ApplicationDetails applicationId={selectedApplication} user={user} />}
        {user && view === "tasks" && <TaskList user={user} onOpen={openTask} />}
        {user && view === "execute" && <TaskExecution applicationId={selectedApplication} user={user} />}
        {user && view === "registrar-review" && <RegistrarReview user={user} />}
        {view === "map" && <LiveMap />}
        {view === "analytics" && <AnalyticsDashboard />}
        {view === "certificate" && <CertificateView />}
        {view === "admin" && <AdminPanel />}
      </main>
    </div>
  );
}

function landingFor(user) {
  if (!user) return "login";
  return {
    applicant: "applicant-dashboard",
    surveyor: "tasks",
    registrar: "registrar-review",
    supervisor: "analytics",
    admin: "admin"
  }[user.role] || "login";
}

