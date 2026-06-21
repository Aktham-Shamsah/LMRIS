export default function Message({ error, children }) {
  if (error) return <p className="message error">{error}</p>;
  if (children) return <p className="message">{children}</p>;
  return null;
}

