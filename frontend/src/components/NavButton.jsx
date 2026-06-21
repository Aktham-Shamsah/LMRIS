export default function NavButton({ active, icon: Icon, label, onClick }) {
  return (
    <button className={active ? "nav-button active" : "nav-button"} onClick={onClick} title={label}>
      {Icon ? <Icon size={18} /> : null}
      <span>{label}</span>
    </button>
  );
}

