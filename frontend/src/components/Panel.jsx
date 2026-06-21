export default function Panel({ title, actions, children }) {
  return (
    <section className="panel">
      <header className="panel-header">
        <h2>{title}</h2>
        <div className="panel-actions">{actions}</div>
      </header>
      {children}
    </section>
  );
}

