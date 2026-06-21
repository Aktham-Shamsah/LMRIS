import { useState } from 'react'
import { applicationsApi } from '../api/applications'

export default function NotesPanel({ appId, notes, onToast, onChanged }) {
  const [text, setText] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleAdd() {
    const trimmed = text.trim()
    if (!trimmed) {
      onToast('Note text is required.', 'error')
      return
    }
    setSaving(true)
    try {
      await applicationsApi.addNote(appId, trimmed, 'registrar')
      onToast('Note added.')
      setText('')
      onChanged()
    } catch (e) {
      onToast(e.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const sorted = [...notes].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))

  return (
    <div style={styles.card}>
      <div style={styles.headerRow}>
        <h3 style={styles.cardTitle}>Internal Notes & Remarks</h3>
        <span style={styles.count}>{notes.length} note{notes.length !== 1 ? 's' : ''}</span>
      </div>
      <p style={styles.hint}>Visible to registrars only. Entries are permanent and form an audit trail — they cannot be edited or deleted.</p>

      <div style={styles.composer}>
        <textarea
          style={styles.textarea}
          placeholder="Add an internal note or remark…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={2000}
        />
        <button style={styles.btn} onClick={handleAdd} disabled={saving || !text.trim()}>
          {saving ? 'Adding…' : 'Add Note'}
        </button>
      </div>

      {sorted.length === 0 ? (
        <p style={{ color: '#888', marginTop: 12 }}>No internal notes yet.</p>
      ) : (
        <ul style={styles.list}>
          {sorted.map((n) => (
            <li key={n.note_id} style={styles.item}>
              <p style={styles.itemText}>{n.text}</p>
              <p style={styles.itemMeta}>
                <b>{n.created_by}</b> · {new Date(n.created_at).toLocaleString()}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

const styles = {
  card: { background: '#f9f9f9', border: '1px solid #eee', borderRadius: 8, padding: 16 },
  headerRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { margin: 0, fontSize: 15 },
  count: { color: '#888', fontSize: 13 },
  hint: { margin: '4px 0 0', color: '#888', fontSize: 12 },
  composer: { display: 'flex', gap: 8, marginTop: 12, alignItems: 'flex-start' },
  textarea: {
    flex: 1, minHeight: 60, padding: '8px 10px', border: '1px solid #ccc', borderRadius: 6,
    fontSize: 14, resize: 'vertical', fontFamily: 'inherit',
  },
  btn: { padding: '8px 16px', background: '#4f8ef7', color: '#fff', border: 'none', borderRadius: 6,
    cursor: 'pointer', fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap' },
  list: { listStyle: 'none', margin: '12px 0 0', padding: 0, display: 'flex', flexDirection: 'column', gap: 8 },
  item: { background: '#fff', border: '1px solid #eee', borderRadius: 6, padding: '10px 12px' },
  itemText: { margin: 0, fontSize: 14, whiteSpace: 'pre-wrap' },
  itemMeta: { margin: '6px 0 0', fontSize: 12, color: '#888' },
}
