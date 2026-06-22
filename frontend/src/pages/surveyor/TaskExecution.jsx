import { useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import { addSurveyMilestone, uploadSurveyReportPdf } from "../../api/survey";

const milestones = ["visit_scheduled", "arrived_on_site", "survey_started", "survey_completed"];

export default function TaskExecution({ applicationId = "", user }) {
  const [id, setId] = useState(applicationId);
  const [reportTitle, setReportTitle] = useState("Field survey report");
  const [findings, setFindings] = useState("");
  const [reportFile, setReportFile] = useState(null);
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

  async function uploadReport() {
    if (!reportFile) {
      setError("Choose a PDF survey report first.");
      return;
    }
    await run(
      () => uploadSurveyReportPdf(id, { reportTitle, findings, file: reportFile }),
      "Survey report PDF uploaded."
    );
    setReportFile(null);
  }

  return (
    <Panel title="Survey Task Execution">
      <div className="form-grid">
        <label>Application ID
          <input value={id} onChange={(event) => setId(event.target.value)} placeholder="LRMIS-2026-0002" />
        </label>
      </div>
      <Message error={error}>{message}</Message>
      <div className="form-grid">
        <label>Report title
          <input value={reportTitle} onChange={(event) => setReportTitle(event.target.value)} />
        </label>
        <label>Findings
          <textarea rows="3" value={findings} onChange={(event) => setFindings(event.target.value)} placeholder="Boundary findings, GPS notes, dispute observations" />
        </label>
        <label>Survey report PDF
          <input type="file" accept="application/pdf,.pdf" onChange={(event) => setReportFile(event.target.files?.[0] || null)} />
        </label>
      </div>
      <div className="panel-actions">
        {milestones.map((milestone) => (
          <button key={milestone} onClick={() => run(() => addSurveyMilestone(id, { milestone, by: user?.actor_id || "surveyor" }), `${milestone} saved.`)}>
            {milestone}
          </button>
        ))}
        <button className="primary" onClick={uploadReport}>Upload Report PDF</button>
      </div>
    </Panel>
  );
}

