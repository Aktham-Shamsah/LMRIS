import { useEffect, useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import StatusPill from "../../components/StatusPill";
import { getApplication, holdApplication, issueCertificate, rejectApplication, transitionApplication, uploadDocumentPdf } from "../../api/applications";
import { autoAssignSurveyor } from "../../api/survey";
import { registrarReview } from "../../api/registrar";

const registrarRoles = ["registrar", "supervisor", "admin"];

export default function ApplicationDetails({ applicationId, user }) {
  const [application, setApplication] = useState(null);
  const [target, setTarget] = useState("pre_checked");
  const [reason, setReason] = useState("");
  const [documentType, setDocumentType] = useState("ownership_deed");
  const [documentFile, setDocumentFile] = useState(null);
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

  async function uploadOwnershipDocument() {
    if (!documentFile) {
      setError("Choose a PDF document first.");
      return;
    }
    await run(
      () => uploadDocumentPdf(application.application_id, {
        file: documentFile,
        documentType,
        isOwnershipDoc: ["ownership_deed", "sale_contract", "title_deed"].includes(documentType)
      }),
      "PDF document uploaded."
    );
    setDocumentFile(null);
  }

  useEffect(() => {
    load();
  }, [applicationId]);

  useEffect(() => {
    const next = application?.allowed_next?.[0];
    if (next && !application.allowed_next.includes(target)) {
      setTarget(next);
    }
  }, [application, target]);

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
          {registrarRoles.includes(user?.role) ? (
            <div className="form-grid">
              <label>Target status
                <select value={target} onChange={(event) => setTarget(event.target.value)}>
                  {(application.allowed_next || []).map((status) => <option key={status} value={status}>{status}</option>)}
                </select>
              </label>
              <label>Reason
                <input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Required for hold/reject/missing/objection" />
              </label>
              <label>Document type
                <select value={documentType} onChange={(event) => setDocumentType(event.target.value)}>
                  <option value="ownership_deed">ownership_deed</option>
                  <option value="sale_contract">sale_contract</option>
                  <option value="title_deed">title_deed</option>
                  <option value="supporting_evidence">supporting_evidence</option>
                </select>
              </label>
              <label>PDF document
                <input type="file" accept="application/pdf,.pdf" onChange={(event) => setDocumentFile(event.target.files?.[0] || null)} />
              </label>
              <button disabled={!application.allowed_next?.length} onClick={() => run(() => transitionApplication(application.application_id, { target_status: target, reason, performed_by: user?.actor_id || "staff-ui" }), "Status updated.")}>Transition</button>
              <button onClick={uploadOwnershipDocument}>Upload PDF Document</button>
              {application.status === "survey_required" && <button onClick={() => run(() => autoAssignSurveyor(application.application_id), "Surveyor assigned.")}>Auto Assign</button>}
              {application.status === "surveyed" && <button onClick={() => run(() => registrarReview(application.application_id, { decision: "accept", registrar_id: user?.actor_id || "registrar", notes: "Survey report accepted." }), "Moved to legal review.")}>Accept Survey</button>}
              {application.status === "legal_review" && <button onClick={() => run(() => registrarReview(application.application_id, { decision: "approve", registrar_id: user?.actor_id || "registrar", notes: "Legal review approved." }), "Approved.")}>Approve</button>}
              {application.status === "approved" && <button onClick={() => run(() => issueCertificate(application.application_id), "Certificate issued.")}>Issue Certificate</button>}
              <button onClick={() => run(() => holdApplication(application.application_id, { reason: reason || "Administrative hold", performed_by: user?.actor_id || "staff-ui" }), "Placed on hold.")}>Hold</button>
              <button className="danger" onClick={() => run(() => rejectApplication(application.application_id, { reason: reason || "Rejected by registrar", performed_by: user?.actor_id || "staff-ui" }), "Rejected.")}>Reject</button>
            </div>
          ) : null}
        </div>
      ) : null}
    </Panel>
  );
}

