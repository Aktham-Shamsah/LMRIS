import { useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import { downloadCertificatePdf, getApplicationCertificate, getCertificate } from "../../api/certificates";

export default function CertificateView() {
  const [mode, setMode] = useState("certificate");
  const [id, setId] = useState("CERT-2026-0001");
  const [certificate, setCertificate] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    try {
      setError("");
      setCertificate(mode === "certificate" ? await getCertificate(id) : await getApplicationCertificate(id));
    } catch (err) {
      setError(err.message);
    }
  }

  async function openPdf() {
    try {
      setError("");
      await downloadCertificatePdf(certificate.certificate_id);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Panel title="Certificate View">
      <div className="form-grid">
        <label>Lookup mode
          <select value={mode} onChange={(event) => setMode(event.target.value)}>
            <option value="certificate">certificate_id</option>
            <option value="application">application_id</option>
          </select>
        </label>
        <label>ID
          <input value={id} onChange={(event) => setId(event.target.value)} />
        </label>
        <button className="primary" onClick={load}>Load</button>
      </div>
      <Message error={error} />
      {certificate ? (
        <>
          <div className="panel-actions">
            {certificate.pdf && <button className="primary" onClick={openPdf}>Open Certificate PDF</button>}
          </div>
          <div className="grid">
            <div className="metric"><span>Certificate</span><strong>{certificate.certificate_id}</strong></div>
            <div className="metric"><span>Status</span><strong>{certificate.status}</strong></div>
            <div className="metric"><span>Application</span><strong>{certificate.application_id}</strong></div>
            <div className="metric"><span>Issued</span><strong>{certificate.issued_at || "pending"}</strong></div>
            <div className="metric"><span>Owner</span><strong>{certificate.issued_to?.full_name || certificate.issued_to?.applicant_id}</strong></div>
            <div className="metric"><span>Parcel</span><strong>{certificate.certificate_details?.parcel_code || certificate.parcel_ref?.parcel_code}</strong></div>
          </div>
        </>
      ) : null}
    </Panel>
  );
}

