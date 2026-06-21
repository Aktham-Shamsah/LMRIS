import { useEffect, useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import StatusPill from "../../components/StatusPill";
import { addDocument, getApplication, holdApplication, issueCertificate, rejectApplication, transitionApplication } from "../../api/applications";
import { autoAssignSurveyor } from "../../api/survey";
import { registrarReview } from "../../api/registrar";

const statuses = ["pre_checked", "survey_required", "surveyed", "legal_review", "approved", "certificate_issued", "closed", "missing_documents", "under_objection"];

export default function ApplicationDetails({ applicationId }) {
  const [application, setApplication] = useState(null);
  const [target, setTarget] = useState("pre_checked");
  const [reason, setReason] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function load() {
    if (!applicationId) return;
    try {
      setApplication(await getApplication(applicationId));
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, [applicationId]);

  async function run(action, success) {
    setError("");
    setMessage("");
    try {
      await action();
      setMessage(success);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  if (!applicationId) {
    return <Panel title="Application Details"><p>Select an application from the management table.</p></Panel>;
  }

  return (
    <Panel title="Application Details" actions={<button onClick={load}>Refresh</button>}>
      <Message error={error}>{message}</Message>
      {application ? (
        <div className="detail-grid">
          <div>
            <h3>{application.application_id}</h3>
            <p><StatusPill status={application.status} /></p>
            <p>{application.description}</p>
            <p>{application.application_type}</p>
            <p>{application.parcel_ref?.parcel_code} / {application.parcel_ref?.zone_id}</p>
            <p>Allowed next: {(application.allowed_next || []).join(", ") || "none"}</p>
          </div>
          <div className="form-grid">
            <label>Target status
              <select value={target} onChange={(event) => setTarget(event.target.value)}>
                {statuses.map((status) => <option key={status} value={status}>{status}</option>)}
              </select>
            </label>
            <label>Reason
              <input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Required for hold/reject/missing/objection" />
            </label>
            <button onClick={() => run(() => transitionApplication(application.application_id, { target_status: target, reason, performed_by: "staff-ui" }), "Status updated.")}>Transition</button>
            <button onClick={() => run(() => addDocument(application.application_id, { document_type: "ownership_deed", filename: "ownership-deed.pdf", is_ownership_doc: true }), "Ownership document registered.")}>Add Ownership Doc</button>
            <button onClick={() => run(() => autoAssignSurveyor(application.application_id), "Surveyor assigned.")}>Auto Assign</button>
            <button onClick={() => run(() => registrarReview(application.application_id, { decision: "accept", registrar_id: "REG-RM-01", notes: "Survey report accepted." }), "Moved to legal review.")}>Accept Survey</button>
            <button onClick={() => run(() => registrarReview(application.application_id, { decision: "approve", registrar_id: "REG-RM-01", notes: "Legal review approved." }), "Approved.")}>Approve</button>
            <button onClick={() => run(() => issueCertificate(application.application_id), "Certificate issued.")}>Issue Certificate</button>
            <button onClick={() => run(() => holdApplication(application.application_id, { reason: reason || "Administrative hold", performed_by: "staff-ui" }), "Placed on hold.")}>Hold</button>
            <button className="danger" onClick={() => run(() => rejectApplication(application.application_id, { reason: reason || "Rejected by registrar", performed_by: "staff-ui" }), "Rejected.")}>Reject</button>
          </div>
        </div>
      ) : null}
    </Panel>
  );
}

