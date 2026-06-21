import { useState, useEffect, useCallback } from 'react'
import { auditLogsApi } from '../api/auditLogs'

const ACTIONS = [
  'application_created', 'status_changed', 'hold_placed', 'rejection_issued',
  'missing_documents_flagged', 'objection_raised', 'certificate_generated',
  'attachment_uploaded', 'attachment_verified', 'attachment_deleted', 'note_added',
]

function actionLabel(action) {
  return action.replace(/_/g, ' ')
}

function actionColor(action) {
  const colors = {
    application_created: '#2980b9',
    status_changed: '#8e44ad',
    hold_placed: '#e67e22',
    rejection_issued: '#c0392b',
    missing_documents_flagged: '#e67e22',
    objection_raised: '#d35400',
    certificate_generated: '#27ae60',
    attachment_uploaded: '#2980b9',
    attachment_verified: '#27ae60',
    attachment_deleted: '#c0392b',
    note_added: '#16a085',
  }
  return colors[action] || '#7f8c8d'
}

function formatDetails(details) {
  if (!details || Object.keys(details).length === 0) return '—'
  return Object.entries(details).map(([k, v]) => `${k}: ${v}`).join(' · ')
}

export default function AuditLogsPage({ onToast }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [actionFilter, setActionFilter] = useState('')
  const [entityId, setEntityId] = useState('')
  const [loading, setLoading] = useState(false)
  const limit = 20

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await auditLogsApi.list(page, limit, actionFilter || undefined, entityId || undefined)
      setItems(res.data.items)
      setTotal(res.data.total)
    } catch (e) {
      onToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [page, actionFilter, entityId, onToast])

  useEffect(() => { load() }, [load])

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h2 style={styles.title}>Audit Logs</h2>
        <button style={styles.btnGhost} onClick={load}>↻ Refresh</button>
      </div>
      <p style={{ marginTop: -8, color: '#888' }}>
        Read-only record of critical system actions, written to <code>performance_logs</code> for auditing.
      </p>

      <div style={styles.filters}>
        <input
          style={{ ...styles.input, width: 260 }}
          placeholder="Filter by entity ID (e.g. APP-2026…)"
          value={entityId}
          onChange={e => { setPage(1); setEntityId(e.target.value) }}
        />
        <select
          style={styles.input}
          value={actionFilter}
          onChange={e => { setPage(1); setActionFilter(e.target.value) }}
        >
          <option value="">All actions</option>
          {ACTIONS.map(a => <option key={a} value={a}>{actionLabel(a)}</option>)}
        </select>
      </div>

      {loading ? <p>Loading…</p> : (
        <table style={styles.table}>
          <thead><tr>
            {['Timestamp', 'Action', 'Entity Type', 'Entity ID', 'Performed By', 'Details'].map(h =>
              <th key={h} style={styles.th}>{h}</th>)}
          </tr></thead>
          <tbody>
            {items.map(log => (
              <tr key={log.id}>
                <td style={{ ...styles.td, whiteSpace: 'nowrap' }}>{new Date(log.timestamp).toLocaleString()}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, background: actionColor(log.action) }}>{actionLabel(log.action)}</span>
                </td>
                <td style={styles.td}>{log.entity_type}</td>
                <td style={styles.td}>{log.entity_id}</td>
                <td style={styles.td}>{log.performed_by}</td>
                <td style={styles.td}>{formatDetails(log.details)}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td style={styles.td} colSpan={6}>No log entries match the current filters.</td></tr>
            )}
          </tbody>
        </table>
      )}

      <div style={styles.pagination}>
        <button style={styles.btnGhost} disabled={page === 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
        <span style={{ color: '#888' }}>Page {page} · {total} total</span>
        <button style={styles.btnGhost} disabled={page * limit >= total} onClick={() => setPage(p => p + 1)}>Next →</button>
      </div>
    </div>
  )
}

const styles = {
  page: { padding: 24 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  title: { margin: 0, fontSize: 22 },
  filters: { display: 'flex', gap: 8, marginTop: 16, marginBottom: 16, flexWrap: 'wrap' },
  input: { padding: '8px 10px', border: '1px solid #ccc', borderRadius: 6, fontSize: 14 },
  btnGhost: { padding: '8px 16px', background: 'none', border: '1px solid #ccc', borderRadius: 6,
    cursor: 'pointer', fontSize: 14 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: { textAlign: 'left', padding: '10px 12px', background: '#f0f0f0', borderBottom: '1px solid #ddd' },
  td: { padding: '10px 12px', borderBottom: '1px solid #eee', verticalAlign: 'middle' },
  badge: { padding: '2px 8px', borderRadius: 10, color: '#fff', fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap' },
  pagination: { display: 'flex', gap: 12, alignItems: 'center', marginTop: 16 },
}
