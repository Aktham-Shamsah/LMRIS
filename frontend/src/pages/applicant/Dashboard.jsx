import { useEffect, useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import StatusPill from "../../components/StatusPill";
import { getApplicantApplications } from "../../api/applicants";

export default function ApplicantDashboard({ applicantId = "APP-400000000", onOpen }) {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getApplicantApplications(applicantId)
      .then((data) => setItems(data.items || []))
      .catch((err) => setError(err.message));
  }, [applicantId]);

  return (
    <Panel title="Applicant Dashboard">
      <Message error={error} />
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Application</th>
              <th>Type</th>
              <th>Status</th>
              <th>Parcel</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((app) => (
              <tr key={app.application_id}>
                <td>{app.application_id}</td>
                <td>{app.application_type}</td>
                <td><StatusPill status={app.status} /></td>
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

