import { useEffect, useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import StatusPill from "../../components/StatusPill";
import { listApplications } from "../../api/applications";

export default function ApplicationManagement({ onOpen }) {
  const [filters, setFilters] = useState({ status: "", application_type: "", zone_id: "" });
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      const result = await listApplications(filters);
      setItems(result.items || []);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const change = (event) => setFilters({ ...filters, [event.target.name]: event.target.value });

  return (
    <Panel title="Application Management" actions={<button onClick={load}>Refresh</button>}>
      <div className="form-grid">
        <label>Status
          <select name="status" value={filters.status} onChange={change}>
            <option value="">All</option>
            {["submitted", "pre_checked", "survey_required", "surveyed", "legal_review", "approved", "certificate_issued", "closed", "rejected", "on_hold", "missing_documents", "under_objection"].map((status) => <option key={status} value={status}>{status}</option>)}
          </select>
        </label>
        <label>Type
          <input name="application_type" value={filters.application_type} onChange={change} placeholder="ownership_transfer" />
        </label>
        <label>Zone
          <input name="zone_id" value={filters.zone_id} onChange={change} placeholder="ZONE-RM-01" />
        </label>
      </div>
      <Message error={error} />
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Status</th>
              <th>Type</th>
              <th>Zone</th>
              <th>Parcel</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((app) => (
              <tr key={app.application_id}>
                <td>{app.application_id}</td>
                <td><StatusPill status={app.status} /></td>
                <td>{app.application_type}</td>
                <td>{app.parcel_ref?.zone_id}</td>
                <td>{app.parcel_ref?.parcel_code}</td>
                <td><button onClick={() => onOpen(app.application_id)}>Open</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

