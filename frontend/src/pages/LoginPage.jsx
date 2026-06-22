import { useState } from "react";
import Panel from "../components/Panel";
import Message from "../components/Message";
import { login, resendOtp, signup, verifyEmail } from "../api/auth";

const demoAccounts = [
  ["applicant@lrmis-demo.ps", "applicant123", "Applicant"],
  ["surveyor@lrmis-demo.ps", "surveyor123", "Surveyor"],
  ["registrar@lrmis-demo.ps", "registrar123", "Registrar"],
  ["supervisor@lrmis-demo.ps", "supervisor123", "Supervisor"],
  ["admin@lrmis-demo.ps", "admin123", "Admin"]
];

export default function LoginPage({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("applicant@lrmis-demo.ps");
  const [password, setPassword] = useState("applicant123");
  const [signupForm, setSignupForm] = useState({
    full_name: "",
    email: "",
    password: "",
    national_id: "",
    phone: "",
    applicant_type: "citizen",
    city: "Ramallah",
    neighborhood: "",
    zone_id: "ZONE-RM-01",
    preferred_language: "ar"
  });
  const [otpCode, setOtpCode] = useState("");
  const [pendingEmail, setPendingEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const result = await login(email, password);
      localStorage.setItem("lrmisToken", result.access_token);
      localStorage.setItem("lrmisUser", JSON.stringify(result.user));
      onLogin(result.user);
    } catch (err) {
      setError(err.message);
    }
  }

  async function submitSignup(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const result = await signup(signupForm);
      setPendingEmail(result.user?.email || signupForm.email);
      setMode("verify");
      setMessage(`Verification code sent to ${result.user?.email || signupForm.email}.`);
    } catch (err) {
      setError(err.message);
    }
  }

  async function submitOtp(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const result = await verifyEmail(pendingEmail || signupForm.email, otpCode);
      localStorage.setItem("lrmisToken", result.access_token);
      localStorage.setItem("lrmisUser", JSON.stringify(result.user));
      onLogin(result.user);
    } catch (err) {
      setError(err.message);
    }
  }

  async function sendAgain() {
    setError("");
    setMessage("");
    try {
      await resendOtp(pendingEmail || signupForm.email);
      setMessage("Verification code resent.");
    } catch (err) {
      setError(err.message);
    }
  }

  function fill(account) {
    setEmail(account[0]);
    setPassword(account[1]);
    setMode("login");
  }

  return (
    <Panel title={mode === "signup" ? "Create Account" : mode === "verify" ? "Verify Email" : "Login"}>
      <Message error={error}>{message}</Message>
      <div className="panel-actions">
        <button className={mode === "login" ? "primary" : ""} onClick={() => setMode("login")}>Login</button>
        <button className={mode === "signup" ? "primary" : ""} onClick={() => setMode("signup")}>Sign up</button>
      </div>
      {mode === "login" ? (
        <form className="form-grid" onSubmit={submit}>
          <label>Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label>Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          <button className="primary" type="submit">Login</button>
        </form>
      ) : null}
      {mode === "signup" ? (
        <form className="form-grid" onSubmit={submitSignup}>
          <label>Full name
            <input value={signupForm.full_name} onChange={(event) => setSignupForm({ ...signupForm, full_name: event.target.value })} required />
          </label>
          <label>Email
            <input type="email" value={signupForm.email} onChange={(event) => setSignupForm({ ...signupForm, email: event.target.value })} required />
          </label>
          <label>Password
            <input type="password" minLength="8" value={signupForm.password} onChange={(event) => setSignupForm({ ...signupForm, password: event.target.value })} required />
          </label>
          <label>National ID
            <input value={signupForm.national_id} onChange={(event) => setSignupForm({ ...signupForm, national_id: event.target.value })} required />
          </label>
          <label>Phone
            <input value={signupForm.phone} onChange={(event) => setSignupForm({ ...signupForm, phone: event.target.value })} />
          </label>
          <label>Applicant type
            <select value={signupForm.applicant_type} onChange={(event) => setSignupForm({ ...signupForm, applicant_type: event.target.value })}>
              <option value="citizen">citizen</option>
              <option value="lawyer">lawyer</option>
              <option value="company">company</option>
              <option value="surveyor">surveyor</option>
              <option value="authorized_representative">authorized_representative</option>
            </select>
          </label>
          <label>City
            <input value={signupForm.city} onChange={(event) => setSignupForm({ ...signupForm, city: event.target.value })} />
          </label>
          <label>Zone
            <select value={signupForm.zone_id} onChange={(event) => setSignupForm({ ...signupForm, zone_id: event.target.value })}>
              <option value="ZONE-RM-01">ZONE-RM-01</option>
              <option value="ZONE-RM-02">ZONE-RM-02</option>
              <option value="ZONE-RM-03">ZONE-RM-03</option>
            </select>
          </label>
          <button className="primary" type="submit">Sign up and send OTP</button>
        </form>
      ) : null}
      {mode === "verify" ? (
        <form className="form-grid" onSubmit={submitOtp}>
          <label>Email
            <input type="email" value={pendingEmail || signupForm.email} onChange={(event) => setPendingEmail(event.target.value)} />
          </label>
          <label>OTP code
            <input value={otpCode} onChange={(event) => setOtpCode(event.target.value)} inputMode="numeric" />
          </label>
          <button className="primary" type="submit">Verify and login</button>
          <button type="button" onClick={sendAgain}>Resend OTP</button>
        </form>
      ) : null}
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

