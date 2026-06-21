import { useState, useEffect, useCallback } from 'react'
import { applicationsApi } from '../api/applications'
import ApplicationDetailPage from './ApplicationDetailPage'

const EMPTY_FORM = {
  application_type: 'first_registration',
  applicant_name: '', applicant_email: '', applicant_phone: '', applicant_national_id: '',
  parcel_number: '', block_number: '', basin_number: '', zone_id: '', parcel_code: '',
  notes: '',
}

const APPLICATION_TYPES = [
  'first_registration', 'ownership_transfer', 'parcel_subdivision',
  'parcel_merge', 'boundary_correction', 'certificate_request',
]

export default function ApplicationsPage({ onToast }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [statusFilter, setStatusFilter] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [showForm, setShowForm] = useState(false)
  const [selectedId, setSelectedId] = useState(null)
  const limit = 10

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await applicationsApi.list(page, limit, statusFilter || undefined, search || undefined)
      setItems(res.data.items)
      setTotal(res.data.total)
    } catch (e) {
      onToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [page, statusFilter, search, onToast])

  useEffect(() => { load() }, [load])

  async function handleSubmit(e) {
    e.preventDefault()
    try {
      await applicationsApi.create({
        application_type: form.application_type,
        applicant: {
          name: form.applicant_name, email: form.applicant_email,
          phone: form.applicant_phone, national_id: form.applicant_national_id,
        },
        parcel_ref: {
          parcel_number: form.parcel_number, block_number: form.block_number,
          basin_number: form.basin_number, zone_id: form.zone_id, parcel_code: form.parcel_code,
        },
        notes: form.notes,
      })
      onToast('Application created.')
      setShowForm(false)
      setForm(EMPTY_FORM)
      load()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  if (selectedId) {
    return (
      <ApplicationDetailPage
        appId={selectedId}
        onToast={onToast}
        onBack={() => { setSelectedId(null); load() }}
      />
    )
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h2 style={styles.title}>Applications</h2>
        <button style={styles.btn} onClick={() => { setForm(EMPTY_FORM); setShowForm(true) }}>
          + New Application
        </button>
      </div>

      <div style={styles.filters}>
        <input style={{ ...styles.input, width: 260 }} placeholder="Search by ID, applicant, parcel…"
          value={search} onChange={e => { setPage(1); setSearch(e.target.value) }} />
        <select style={styles.input} value={statusFilter} onChange={e => { setPage(1); setStatusFilter(e.target.value) }}>
          <option value="">All statuses</option>
          {['submitted','pre_checked','survey_required','surveyed','legal_review','approved',
            'certificate_issued','closed','rejected','on_hold','missing_documents','under_objection'].map(s =>
            <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} style={styles.form}>
          <h3 style={{ margin: 0 }}>New Application</h3>
          <label style={styles.label}>
            Application Type
            <select style={styles.input} value={form.application_type}
              onChange={e => setForm(f => ({ ...f, application_type: e.target.value }))}>
              {APPLICATION_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </label>
          <div style={styles.grid2}>
            {[['applicant_name','Applicant Name'],['applicant_email','Applicant Email'],
              ['applicant_phone','Applicant Phone'],['applicant_national_id','National ID']].map(([k, label]) => (
              <label key={k} style={styles.label}>
                {label}
                <input style={styles.input} type={k === 'applicant_email' ? 'email' : 'text'} value={form[k]}
                  onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
                  required={k !== 'applicant_phone'} />
              </label>
            ))}
            {[['parcel_number','Parcel Number'],['block_number','Block Number'],
              ['basin_number','Basin Number'],['zone_id','Zone ID'],['parcel_code','Parcel Code']].map(([k, label]) => (
              <label key={k} style={styles.label}>
                {label}
                <input style={styles.input} value={form[k]}
                  onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
                  required={k !== 'parcel_code'} />
              </label>
            ))}
          </div>
          <label style={styles.label}>
            Notes
            <textarea style={{ ...styles.input, height: 60 }} value={form.notes}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
          </label>
          <div style={{ display: 'flex', gap: 8 }}>
            <button type="submit" style={styles.btn}>Create</button>
            <button type="button" style={styles.btnGhost} onClick={() => setShowForm(false)}>Cancel</button>
          </div>
        </form>
      )}

      {loading ? <p>Loading…</p> : (
        <table style={styles.table}>
          <thead><tr>
            {['Application ID','Type','Applicant','Status','Updated','Actions'].map(h =>
              <th key={h} style={styles.th}>{h}</th>)}
          </tr></thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id}>
                <td style={styles.td}>{item.application_id}</td>
                <td style={styles.td}>{item.application_type}</td>
                <td style={styles.td}>{item.applicant.name}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, background: statusColor(item.status) }}>{item.status}</span>
                </td>
                <td style={styles.td}>{new Date(item.timestamps.updated_at).toLocaleString()}</td>
                <td style={styles.td}>
                  <button style={styles.btnSm} onClick={() => setSelectedId(item.id)}>Review</button>
                </td>
              </tr>
            ))}
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

function statusColor(s) {
  const colors = {
    submitted: '#2980b9', pre_checked: '#2980b9', survey_required: '#16a085', surveyed: '#16a085',
    legal_review: '#8e44ad', approved: '#27ae60', certificate_issued: '#27ae60', closed: '#7f8c8d',
    rejected: '#c0392b', on_hold: '#e67e22', missing_documents: '#e67e22', under_objection: '#d35400',
  }
  return colors[s] || '#7f8c8d'
}

const styles = {
  page: { padding: 24 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  title: { margin: 0, fontSize: 22 },
  filters: { display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' },
  form: { background: '#f9f9f9', border: '1px solid #ddd', borderRadius: 8, padding: 20, marginBottom: 20,
    display: 'flex', flexDirection: 'column', gap: 12 },
  grid2: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 },
  label: { display: 'flex', flexDirection: 'column', gap: 4, fontSize: 13, fontWeight: 500 },
  input: { padding: '8px 10px', border: '1px solid #ccc', borderRadius: 6, fontSize: 14 },
  btn: { padding: '8px 16px', background: '#4f8ef7', color: '#fff', border: 'none', borderRadius: 6,
    cursor: 'pointer', fontSize: 14, fontWeight: 600 },
  btnGhost: { padding: '8px 16px', background: 'none', border: '1px solid #ccc', borderRadius: 6,
    cursor: 'pointer', fontSize: 14 },
  btnSm: { padding: '4px 10px', background: '#4f8ef7', color: '#fff', border: 'none', borderRadius: 4,
    cursor: 'pointer', fontSize: 12, marginRight: 4 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: { textAlign: 'left', padding: '10px 12px', background: '#f0f0f0', borderBottom: '1px solid #ddd' },
  td: { padding: '10px 12px', borderBottom: '1px solid #eee', verticalAlign: 'middle' },
  badge: { padding: '2px 8px', borderRadius: 10, color: '#fff', fontSize: 11, fontWeight: 600 },
  pagination: { display: 'flex', gap: 12, alignItems: 'center', marginTop: 16 },
}
