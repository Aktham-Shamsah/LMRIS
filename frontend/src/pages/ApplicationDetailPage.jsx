import { useState, useEffect, useCallback } from 'react'
import { applicationsApi } from '../api/applications'
import AttachmentsPanel from '../components/AttachmentsPanel'
import NotesPanel from '../components/NotesPanel'

const REASON_REQUIRED = new Set(['missing_documents', 'under_objection'])

export default function ApplicationDetailPage({ appId, onToast, onBack }) {
  const [details, setDetails] = useState(null)
  const [loading, setLoading] = useState(false)
  const [pendingAction, setPendingAction] = useState(null) // { kind: 'hold' | 'transition', target?, label }
  const [reason, setReason] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await applicationsApi.get(appId)
      setDetails(res.data)
    } catch (e) {
      onToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [appId, onToast])

  useEffect(() => { load() }, [load])

  function startTransition(target) {
    if (target === 'rejected') {
      setPendingAction({ kind: 'reject', label: 'Reject application' })
      setReason('')
    } else if (REASON_REQUIRED.has(target)) {
      setPendingAction({ kind: 'transition', target, label: `Transition to "${target}"` })
      setReason('')
    } else {
      runTransition(target, null)
    }
  }

  function startHold() {
    setPendingAction({ kind: 'hold', label: 'Place on hold' })
    setReason('')
  }

  async function runTransition(target, reasonText) {
    try {
      await applicationsApi.transition(appId, { new_status: target, reason: reasonText, performed_by: 'registrar' })
      onToast(`Status changed to "${target}".`)
      load()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  async function runHold(reasonText) {
    try {
      await applicationsApi.placeOnHold(appId, reasonText, 'registrar')
      onToast('Application placed on hold.')
      load()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  async function runReject(reasonText) {
    try {
      await applicationsApi.reject(appId, reasonText, 'registrar')
      onToast('Application rejected.')
      load()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  async function handleIssueCertificate() {
    try {
      await applicationsApi.issueCertificate(appId, 'registrar')
      onToast('Certificate generated.')
      load()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  async function confirmPendingAction() {
    if (!reason.trim()) {
      onToast('A reason is required.', 'error')
      return
    }
    if (pendingAction.kind === 'hold') {
      await runHold(reason.trim())
    } else if (pendingAction.kind === 'reject') {
      await runReject(reason.trim())
    } else {
      await runTransition(pendingAction.target, reason.trim())
    }
    setPendingAction(null)
    setReason('')
  }

  if (loading || !details) return <div style={styles.page}><p>Loading…</p></div>

  const { application: app, workflow, parcel, attachments, objections, certificate, internal_notes: internalNotes } = details
  const canHold = workflow.allowed_next_statuses.includes('on_hold')
  const canIssueCertificate = workflow.allowed_next_statuses.includes('certificate_issued')
  const otherTransitions = workflow.allowed_next_statuses.filter(s => s !== 'on_hold' && s !== 'certificate_issued')

  return (
    <div style={styles.page}>
      <button style={styles.btnGhost} onClick={onBack}>← Back to list</button>

      <div style={styles.header}>
        <div>
          <h2 style={styles.title}>{app.application_id}</h2>
          <p style={{ margin: 0, color: '#888' }}>{app.application_type}</p>
        </div>
        <span style={{ ...styles.badge, background: statusColor(app.status), fontSize: 14 }}>{app.status}</span>
      </div>

      <div style={styles.grid2}>
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Applicant</h3>
          <p><b>Name:</b> {app.applicant.name}</p>
          <p><b>Email:</b> {app.applicant.email}</p>
          <p><b>Phone:</b> {app.applicant.phone || '—'}</p>
          <p><b>National ID:</b> {app.applicant.national_id}</p>
        </div>
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Parcel</h3>
          <p><b>Parcel #:</b> {app.parcel_ref.parcel_number}</p>
          <p><b>Block #:</b> {app.parcel_ref.block_number}</p>
          <p><b>Basin #:</b> {app.parcel_ref.basin_number}</p>
          <p><b>Zone:</b> {app.parcel_ref.zone_id}</p>
          {parcel && <p><b>Parcel Code:</b> {parcel.parcel_code}</p>}
        </div>
      </div>

      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Workflow</h3>
        <p><b>Current status:</b> {workflow.current_status}</p>
        {workflow.previous_status && <p><b>Resumes to:</b> {workflow.previous_status}</p>}
        {workflow.hold_reason && <p><b>Hold reason:</b> {workflow.hold_reason}</p>}
        {workflow.rejection_reason && <p><b>Rejection reason:</b> {workflow.rejection_reason}</p>}
        {workflow.missing_documents_reason && <p><b>Missing documents reason:</b> {workflow.missing_documents_reason}</p>}
        {workflow.objection_reason && <p><b>Objection reason:</b> {workflow.objection_reason}</p>}

        <div style={styles.actions}>
          {canHold && (
            <button style={{ ...styles.btn, background: '#e67e22' }} onClick={startHold}>
              Place on hold
            </button>
          )}
          {canIssueCertificate && (
            <button style={{ ...styles.btn, background: '#27ae60' }} onClick={handleIssueCertificate}>
              Generate Certificate
            </button>
          )}
          {otherTransitions.map(target => (
            <button
              key={target}
              style={target === 'rejected' ? { ...styles.btn, background: '#c0392b' } : styles.btn}
              onClick={() => startTransition(target)}
            >
              {app.status === 'on_hold' && target === workflow.previous_status ? `Resume → ${target}` : target}
            </button>
          ))}
          {workflow.allowed_next_statuses.length === 0 && <p style={{ color: '#888' }}>No further transitions (terminal state).</p>}
        </div>
      </div>

      {workflow.hold_history.length > 0 && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Hold History</h3>
          <table style={styles.table}>
            <thead><tr>{['Reason', 'Held By', 'Held At'].map(h => <th key={h} style={styles.th}>{h}</th>)}</tr></thead>
            <tbody>
              {workflow.hold_history.map((h, i) => (
                <tr key={i}>
                  <td style={styles.td}>{h.reason}</td>
                  <td style={styles.td}>{h.held_by}</td>
                  <td style={styles.td}>{new Date(h.held_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {workflow.rejection_history.length > 0 && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Rejection History</h3>
          <table style={styles.table}>
            <thead><tr>{['Reason', 'Rejected By', 'Rejected At'].map(h => <th key={h} style={styles.th}>{h}</th>)}</tr></thead>
            <tbody>
              {workflow.rejection_history.map((r, i) => (
                <tr key={i}>
                  <td style={styles.td}>{r.reason}</td>
                  <td style={styles.td}>{r.rejected_by}</td>
                  <td style={styles.td}>{new Date(r.rejected_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {workflow.history.length > 0 && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Status History</h3>
          <table style={styles.table}>
            <thead><tr>{['From', 'To', 'By', 'When'].map(h => <th key={h} style={styles.th}>{h}</th>)}</tr></thead>
            <tbody>
              {workflow.history.map((h, i) => (
                <tr key={i}>
                  <td style={styles.td}>{h.from_status || '—'}</td>
                  <td style={styles.td}>{h.to_status}</td>
                  <td style={styles.td}>{h.performed_by}</td>
                  <td style={styles.td}>{new Date(h.timestamp).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AttachmentsPanel appId={appId} attachments={attachments} onToast={onToast} onChanged={load} />

      <NotesPanel appId={appId} notes={internalNotes} onToast={onToast} onChanged={load} />

      {objections.length > 0 && (
        <div style={styles.card}>
          <h3 style={styles.cardTitle}>Objections</h3>
          <table style={styles.table}>
            <thead><tr>{['Objector', 'Reason', 'Status', 'Filed'].map(h => <th key={h} style={styles.th}>{h}</th>)}</tr></thead>
            <tbody>
              {objections.map(o => (
                <tr key={o.objection_id}>
                  <td style={styles.td}>{o.objector_name}</td>
                  <td style={styles.td}>{o.reason}</td>
                  <td style={styles.td}>{o.status}</td>
                  <td style={styles.td}>{new Date(o.filed_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={styles.card}>
        <h3 style={styles.cardTitle}>Certificate</h3>
        <p><b>Status:</b> {certificate.status}</p>
        {certificate.certificate_id && <p><b>ID:</b> {certificate.certificate_id}</p>}
        {certificate.issued_at && <p><b>Issued:</b> {new Date(certificate.issued_at).toLocaleString()}</p>}
        {certificate.valid_until && <p><b>Valid until:</b> {new Date(certificate.valid_until).toLocaleString()}</p>}
      </div>

      {pendingAction && (
        <div style={styles.overlay}>
          <div style={styles.modal}>
            <h3 style={{ margin: 0 }}>{pendingAction.label}</h3>
            <label style={styles.label}>
              Reason (required)
              <textarea
                style={{ ...styles.input, height: 80 }}
                value={reason}
                onChange={e => setReason(e.target.value)}
                autoFocus
              />
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <button style={styles.btn} onClick={confirmPendingAction}>Confirm</button>
              <button style={styles.btnGhost} onClick={() => setPendingAction(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function statusColor(s) {
  const colors = {
    submitted: '#2980b9', pre_checked: '#2980b9', survey_required: '#16a085', surveyed: '#16a085',
    legal_review: '#8e44ad', approved: '#27ae60', certificate_issued: '#27ae60', closed: '#7f8c8d',
    rejected: '#c0392b', on_hold: '#e67e22', missing_documents: '#e67e22', under_objection: '#d35400',
  }
  return colors[s] || '#7f8c8d'
}

const styles = {
  page: { padding: 24, display: 'flex', flexDirection: 'column', gap: 16 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  title: { margin: 0, fontSize: 22 },
  grid2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 },
  card: { background: '#f9f9f9', border: '1px solid #eee', borderRadius: 8, padding: 16 },
  cardTitle: { margin: '0 0 10px', fontSize: 15 },
  actions: { display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 },
  label: { display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13, fontWeight: 500 },
  input: { padding: '8px 10px', border: '1px solid #ccc', borderRadius: 6, fontSize: 14 },
  btn: { padding: '8px 16px', background: '#4f8ef7', color: '#fff', border: 'none', borderRadius: 6,
    cursor: 'pointer', fontSize: 14, fontWeight: 600 },
  btnGhost: { padding: '8px 16px', background: 'none', border: '1px solid #ccc', borderRadius: 6,
    cursor: 'pointer', fontSize: 14 },
  btnSm: { padding: '4px 10px', background: '#4f8ef7', color: '#fff', border: 'none', borderRadius: 4,
    cursor: 'pointer', fontSize: 12 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: { textAlign: 'left', padding: '8px 10px', background: '#f0f0f0', borderBottom: '1px solid #ddd' },
  td: { padding: '8px 10px', borderBottom: '1px solid #eee', verticalAlign: 'middle' },
  badge: { padding: '4px 10px', borderRadius: 10, color: '#fff', fontWeight: 600 },
  overlay: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,.4)', display: 'flex',
    alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
  modal: { background: '#fff', borderRadius: 8, padding: 24, width: 400,
    display: 'flex', flexDirection: 'column', gap: 12 },
}
