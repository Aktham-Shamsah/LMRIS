import Panel from "../components/Panel";

const roles = [
  { id: "applicant", label: "Applicant", apiRole: "staff" },
  { id: "staff", label: "Staff", apiRole: "staff" },
  { id: "surveyor", label: "Surveyor", apiRole: "surveyor" },
  { id: "registrar", label: "Registrar", apiRole: "registrar" },
  { id: "manager", label: "Manager", apiRole: "manager" }
];

export default function LoginPage({ onSelect }) {
  return (
    <Panel title="User Selection">
      <div className="grid">
        {roles.map((role) => (
          <button key={role.id} className="primary" onClick={() => onSelect(role)}>
            {role.label}
          </button>
        ))}
      </div>
    </Panel>
  );
}

