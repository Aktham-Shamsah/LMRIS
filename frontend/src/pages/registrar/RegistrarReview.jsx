import { useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import { registrarReview } from "../../api/registrar";

export default function RegistrarReview() {
  const [applicationId, setApplicationId] = useState("LRMIS-2026-0003");
  const [decision, setDecision] = useState("accept");
  const [notes, setNotes] = useState("Registrar review completed.");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function submit() {
    try {
      setError("");
      const result = await registrarReview(applicationId, {
        decision,
        registrar_id: "REG-RM-01",
        notes,
        reason: notes
      });
      setMessage(`Application is now ${result.status}`);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Panel title="Registrar Review">
      <div className="form-grid">
        <label>Application ID
          <input value={applicationId} onChange={(event) => setApplicationId(event.target.value)} />
        </label>
        <label>Decision
          <select value={decision} onChange={(event) => setDecision(event.target.value)}>
            <option value="accept">accept survey report</option>
            <option value="approve">approve legal review</option>
            <option value="continue_after_objection">continue after objection</option>
            <option value="request_documents">request documents</option>
            <option value="hold">hold</option>
            <option value="reject">reject</option>
          </select>
        </label>
        <label>Notes or reason
          <textarea rows="3" value={notes} onChange={(event) => setNotes(event.target.value)} />
        </label>
        <button className="primary" onClick={submit}>Submit Review</button>
      </div>
      <Message error={error}>{message}</Message>
    </Panel>
  );
}

