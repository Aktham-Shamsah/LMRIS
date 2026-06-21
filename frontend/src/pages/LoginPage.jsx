import { useState } from "react";
import Panel from "../components/Panel";
import Message from "../components/Message";
import { login } from "../api/auth";

const demoAccounts = [
  ["applicant@lrmis-demo.ps", "applicant123", "Applicant"],
  ["surveyor@lrmis-demo.ps", "surveyor123", "Surveyor"],
  ["registrar@lrmis-demo.ps", "registrar123", "Registrar"],
  ["supervisor@lrmis-demo.ps", "supervisor123", "Supervisor"],
  ["admin@lrmis-demo.ps", "admin123", "Admin"]
];

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState("applicant@lrmis-demo.ps");
  const [password, setPassword] = useState("applicant123");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const result = await login(email, password);
      localStorage.setItem("lrmisToken", result.access_token);
      localStorage.setItem("lrmisUser", JSON.stringify(result.user));
      onLogin(result.user);
    } catch (err) {
      setError(err.message);
    }
  }

  function fill(account) {
    setEmail(account[0]);
    setPassword(account[1]);
  }

  return (
    <Panel title="Login">
      <Message error={error} />
      <form className="form-grid" onSubmit={submit}>
        <label>Email
          <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
        </label>
        <label>Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        <button className="primary" type="submit">Login</button>
      </form>
      <h3>Demo accounts</h3>
      <div className="grid">
        {demoAccounts.map((account) => (
          <button key={account[0]} onClick={() => fill(account)}>
            {account[2]}
          </button>
        ))}
      </div>
    </Panel>
  );
}

