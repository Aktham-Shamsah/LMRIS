import { useEffect, useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import { applicationsByZone, getKpis, processingTime, registrarAnalytics, surveyorAnalytics } from "../../api/analytics";

export default function AnalyticsDashboard() {
  const [data, setData] = useState({});
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getKpis(), applicationsByZone(), processingTime(), surveyorAnalytics(), registrarAnalytics()])
      .then(([kpis, zones, processing, surveyors, registrars]) => setData({ kpis, zones, processing, surveyors, registrars }))
      .catch((err) => setError(err.message));
  }, []);

  const maxZone = Math.max(...(data.zones || []).map((zone) => zone.count), 1);

  return (
    <Panel title="Analytics Dashboard">
      <Message error={error} />
      {data.kpis ? (
        <div className="grid">
          <div className="metric"><span>Total applications</span><strong>{data.kpis.total_applications}</strong></div>
          <div className="metric"><span>Pending</span><strong>{data.kpis.pending_applications}</strong></div>
          <div className="metric"><span>Rejected</span><strong>{data.kpis.rejected_applications}</strong></div>
          <div className="metric"><span>Objections</span><strong>{data.kpis.applications_under_objection}</strong></div>
        </div>
      ) : null}
      <div>
        <h3>Applications by zone</h3>
        {(data.zones || []).map((zone) => (
          <div className="bar" key={zone._id}>
            <span>{zone._id}</span>
            <div className="bar-track"><div className="bar-fill" style={{ width: `${(zone.count / maxZone) * 100}%` }} /></div>
            <strong>{zone.count}</strong>
          </div>
        ))}
      </div>
      <div className="grid">
        <div>
          <h3>Surveyors</h3>
          {(data.surveyors || []).map((item) => <p key={item.staff_code}>{item.name}: {item.task_count} tasks</p>)}
        </div>
        <div>
          <h3>Registrars</h3>
          {(data.registrars || []).map((item) => <p key={item._id}>{item.name}: {item.review_count} reviews</p>)}
        </div>
      </div>
    </Panel>
  );
}

