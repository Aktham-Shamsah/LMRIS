import { useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import { addSurveyMilestone, uploadSurveyReport } from "../../api/survey";

const milestones = ["visit_scheduled", "arrived_on_site", "survey_started", "survey_completed"];

export default function TaskExecution({ applicationId = "" }) {
  const [id, setId] = useState(applicationId);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function run(action, success) {
    try {
      setError("");
      await action();
      setMessage(success);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Panel title="Survey Task Execution">
      <div className="form-grid">
        <label>Application ID
          <input value={id} onChange={(event) => setId(event.target.value)} placeholder="LRMIS-2026-0002" />
        </label>
      </div>
      <Message error={error}>{message}</Message>
      <div className="panel-actions">
        {milestones.map((milestone) => (
          <button key={milestone} onClick={() => run(() => addSurveyMilestone(id, { milestone, by: "SURV-RM-04" }), `${milestone} saved.`)}>
            {milestone}
          </button>
        ))}
        <button className="primary" onClick={() => run(() => uploadSurveyReport(id, { report_title: "Field survey report", surveyor_id: "SURV-RM-04", findings: "Boundary verified.", field_notes: ["GPS points captured"] }), "Report uploaded.")}>
          report_uploaded
        </button>
      </div>
    </Panel>
  );
}

