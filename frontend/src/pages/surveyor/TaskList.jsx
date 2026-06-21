import { useEffect, useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import { listSurveyTasks } from "../../api/survey";

export default function TaskList({ onOpen }) {
  const [surveyorId, setSurveyorId] = useState("SURV-RM-04");
  const [tasks, setTasks] = useState([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      const result = await listSurveyTasks(surveyorId);
      setTasks(result.items || []);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <Panel title="Surveyor Task List" actions={<button onClick={load}>Refresh</button>}>
      <div className="form-grid">
        <label>Surveyor ID
          <input value={surveyorId} onChange={(event) => setSurveyorId(event.target.value)} />
        </label>
      </div>
      <Message error={error} />
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Task</th>
              <th>Application</th>
              <th>Parcel</th>
              <th>Milestone</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.task_id}>
                <td>{task.task_id}</td>
                <td>{task.application_id}</td>
                <td>{task.parcel_id}</td>
                <td>{task.status}</td>
                <td><button onClick={() => onOpen(task.application_id)}>Execute</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

