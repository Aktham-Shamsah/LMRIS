import { useEffect, useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import { applicationsByStatus, getKpis } from "../../api/analytics";

export default function StaffDashboard() {
  const [kpis, setKpis] = useState(null);
  const [statuses, setStatuses] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getKpis(), applicationsByStatus()])
      .then(([kpiData, statusData]) => {
        setKpis(kpiData);
        setStatuses(statusData);
      })
      .catch((err) => setError(err.message));
  }, []);

  const max = Math.max(...statuses.map((item) => item.count), 1);

  return (
    <Panel title="Staff Dashboard">
      <Message error={error} />
      {kpis ? (
        <div className="grid">
          <div className="metric"><span>Total</span><strong>{kpis.total_applications}</strong></div>
          <div className="metric"><span>Pending</span><strong>{kpis.pending_applications}</strong></div>
          <div className="metric"><span>Approved</span><strong>{kpis.approved_applications}</strong></div>
          <div className="metric"><span>Under objection</span><strong>{kpis.applications_under_objection}</strong></div>
        </div>
      ) : null}
      <div>
        {statuses.map((item) => (
          <div className="bar" key={item._id}>
            <span>{item._id}</span>
            <div className="bar-track"><div className="bar-fill" style={{ width: `${(item.count / max) * 100}%` }} /></div>
            <strong>{item.count}</strong>
          </div>
        ))}
      </div>
    </Panel>
  );
}

