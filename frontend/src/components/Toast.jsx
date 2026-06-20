import { useEffect } from 'react'

export default function Toast({ message, type = 'info', onClose }) {
  useEffect(() => {
    const t = setTimeout(onClose, 3500)
    return () => clearTimeout(t)
  }, [onClose])

  const bg = type === 'error' ? '#c0392b' : '#27ae60'

  return (
    <div style={{ ...styles.box, background: bg }}>
      {message}
      <button style={styles.close} onClick={onClose}>×</button>
    </div>
  )
}

const styles = {
  box: {
    position: 'fixed',
    bottom: 24,
    right: 24,
    padding: '12px 20px',
    borderRadius: 8,
    color: '#fff',
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    zIndex: 9999,
    boxShadow: '0 4px 12px rgba(0,0,0,.3)',
  },
  close: {
    background: 'none',
    border: 'none',
    color: '#fff',
    fontSize: 18,
    cursor: 'pointer',
    lineHeight: 1,
  },
}
