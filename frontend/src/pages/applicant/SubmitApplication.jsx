import { useState } from "react";
import Panel from "../../components/Panel";
import Message from "../../components/Message";
import { createApplicant } from "../../api/applicants";
import { createApplication } from "../../api/applications";

const defaultGeometry = {
  type: "Polygon",
  coordinates: [[[35.2001, 31.9021], [35.2015, 31.9021], [35.2015, 31.903], [35.2001, 31.903], [35.2001, 31.9021]]]
};

export default function SubmitApplication({ user, onCreated }) {
  const [form, setForm] = useState({
    full_name: "Nour Ahmad",
    national_id: "400000000",
    email: "nour@example.com",
    phone: "+970599000000",
    applicant_type: "citizen",
    application_type: "ownership_transfer",
    parcel_number: "145",
    block_number: "12",
    basin_number: "3",
    zone_id: "ZONE-RM-01",
    description: "Ownership transfer application"
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value });

  async function submit(event) {
    event.preventDefault();
    setError("");
    setMessage("");
    try {
      const applicant = await createApplicant({
        full_name: form.full_name,
        applicant_type: form.applicant_type,
        identity: { national_id: form.national_id, verified: true },
        contacts: { email: form.email, phone: form.phone },
        address: { city: "Ramallah", zone_id: form.zone_id },
        verification_state: "verified"
      });
      const payload = {
        application_type: form.application_type,
        applicant_ref: {
          applicant_id: user?.actor_id || applicant.applicant_id,
          applicant_type: form.applicant_type,
          submitted_by_representative: false
        },
        parcel_ref: {
          parcel_number: form.parcel_number,
          block_number: form.block_number,
          basin_number: form.basin_number,
          zone_id: form.zone_id,
          geometry: defaultGeometry
        },
        description: form.description,
        idempotency_key: `${form.national_id}-${form.parcel_number}-${form.application_type}`
      };
      const app = await createApplication(payload, payload.idempotency_key);
      setMessage(`Created ${app.application_id}`);
      onCreated?.(app.application_id);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <Panel title="Submit Application">
      <Message error={error}>{message}</Message>
      <form className="form-grid" onSubmit={submit}>
        {["full_name", "national_id", "email", "phone", "parcel_number", "block_number", "basin_number", "zone_id"].map((field) => (
          <label key={field}>{field.replaceAll("_", " ")}
            <input name={field} value={form[field]} onChange={update} />
          </label>
        ))}
        <label>Applicant type
          <select name="applicant_type" value={form.applicant_type} onChange={update}>
            <option value="citizen">citizen</option>
            <option value="lawyer">lawyer</option>
            <option value="company">company</option>
            <option value="surveyor">surveyor</option>
            <option value="authorized_representative">authorized_representative</option>
          </select>
        </label>
        <label>Application type
          <select name="application_type" value={form.application_type} onChange={update}>
            <option value="first_registration">first_registration</option>
            <option value="ownership_transfer">ownership_transfer</option>
            <option value="parcel_subdivision">parcel_subdivision</option>
            <option value="parcel_merge">parcel_merge</option>
            <option value="boundary_correction">boundary_correction</option>
            <option value="certificate_request">certificate_request</option>
          </select>
        </label>
        <label className="wide">Description
          <textarea name="description" value={form.description} onChange={update} rows="3" />
        </label>
        <button className="primary" type="submit">Submit</button>
      </form>
    </Panel>
  );
}

