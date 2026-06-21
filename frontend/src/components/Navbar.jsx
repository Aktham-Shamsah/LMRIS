export default function Navbar({ active, onNav }) {
  const links = ['Applications', 'Parcels', 'Users', 'Audit Logs']

  return (
    <nav style={styles.nav}>
      <span style={styles.brand}>WebService</span>
      <div style={styles.links}>
        {links.map((l) => (
          <button
            key={l}
            style={{ ...styles.link, ...(active === l ? styles.active : {}) }}
            onClick={() => onNav(l)}
          >
            {l}
          </button>
        ))}
      </div>
    </nav>
  )
}

const styles = {
  nav: {
    display: 'flex',
    alignItems: 'center',
    gap: 24,
    padding: '12px 24px',
    background: '#1a1a2e',
    color: '#fff',
  },
  brand: { fontWeight: 700, fontSize: 18, letterSpacing: 1 },
  links: { display: 'flex', gap: 8 },
  link: {
    background: 'none',
    border: '1px solid transparent',
    color: '#ccc',
    cursor: 'pointer',
    padding: '6px 14px',
    borderRadius: 6,
    fontSize: 14,
  },
  active: { borderColor: '#4f8ef7', color: '#fff' },
}
