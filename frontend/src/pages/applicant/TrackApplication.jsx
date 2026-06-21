import { useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import StatusPill from "../../components/StatusPill";
import { addComment, addDocument, addObjection, getApplication, getTimeline } from "../../api/applications";

export default function TrackApplication({ initialId = "" }) {
  const [applicationId, setApplicationId] = useState(initialId);
  const [application, setApplication] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function load(id = applicationId) {
    setError("");
    try {
      const [app, events] = await Promise.all([getApplication(id), getTimeline(id)]);
      setApplication(app);
      setTimeline(events.items || []);
    } catch (err) {
      setError(err.message);
    }
  }

  async function addMetadata() {
    try {
      await addDocument(application.application_id, {
        document_type: "ownership_deed",
        filename: "ownership-deed.pdf",
        status: "uploaded",
        is_ownership_doc: true
      });
      setMessage("Document metadata added.");
      load(application.application_id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function comment() {
    try {
      await addComment(application.application_id, { text: "Applicant response submitted.", author_id: application.applicant_ref.applicant_id });
      setMessage("Comment added.");
      load(application.application_id);
    } catch (err) {
      setError(err.message);
    }
  }

  async function object() {
    try {
      await addObjection(application.application_id, { reason: "Applicant reports a boundary dispute.", submitted_by: application.applicant_ref.applicant_id });
      setMessage("Objection submitted.");
      load(application.application_id);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Panel title="Track Application">
      <div className="form-grid">
        <label>Application ID
          <input value={applicationId} onChange={(event) => setApplicationId(event.target.value)} placeholder="LRMIS-2026-0001" />
        </label>
        <button className="primary" onClick={() => load()}>Search</button>
      </div>
      <Message error={error}>{message}</Message>
      {application ? (
        <div className="detail-grid">
          <div>
            <h3>{application.application_id}</h3>
            <p><StatusPill status={application.status} /></p>
            <p>{application.description}</p>
            <p>{application.parcel_ref?.parcel_code}</p>
            <div className="panel-actions">
              <button onClick={addMetadata}>Add Document</button>
              <button onClick={comment}>Comment</button>
              <button onClick={object}>Submit Objection</button>
            </div>
          </div>
          <ul className="timeline">
            {timeline.map((event, index) => (
              <li key={`${event.type}-${index}`}>
                <strong>{event.type}</strong>
                <div>{event.at}</div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Panel>
  );
}

