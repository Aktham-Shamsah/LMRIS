import { useState, useEffect, useCallback } from 'react'
import { parcelsApi } from '../api/parcels'

const EMPTY_FORM = {
  parcel_code: '', parcel_number: '', zone_id: '',
  owner_name: '', owner_national_id: '', owner_email: '', owner_phone: '',
  area: '', longitude: '', latitude: '',
  land_use: '', status: 'active', description: '',
}

export default function ParcelsPage({ onToast }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [editId, setEditId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [nearbyForm, setNearbyForm] = useState({ lng: '', lat: '', dist: 5000 })
  const [nearbyResults, setNearbyResults] = useState(null)
  const limit = 10

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await parcelsApi.list(page, limit)
      setItems(res.data.items)
      setTotal(res.data.total)
    } catch (e) {
      onToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [page, onToast])

  useEffect(() => { load() }, [load])

  async function handleSubmit(e) {
    e.preventDefault()
    const updatable = {
      owner: {
        name: form.owner_name,
        national_id: form.owner_national_id,
        email: form.owner_email,
        phone: form.owner_phone,
      },
      area: parseFloat(form.area),
      geometry: {
        type: 'Point',
        coordinates: [parseFloat(form.longitude), parseFloat(form.latitude)],
      },
      land_use: form.land_use,
      description: form.description,
      status: form.status,
    }
    try {
      if (editId) {
        await parcelsApi.update(editId, updatable)
        onToast('Parcel updated.')
      } else {
        await parcelsApi.create({
          ...updatable,
          parcel_code: form.parcel_code,
          parcel_number: form.parcel_number,
          zone_id: form.zone_id,
        })
        onToast('Parcel created.')
      }
      setShowForm(false)
      setEditId(null)
      setForm(EMPTY_FORM)
      load()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  async function handleDelete(id) {
    if (!confirm('Delete this parcel?')) return
    try {
      await parcelsApi.delete(id)
      onToast('Parcel deleted.')
      load()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  function openEdit(item) {
    setForm({
      parcel_code: item.parcel_code,
      parcel_number: item.parcel_number,
      zone_id: item.zone_id,
      owner_name: item.owner.name,
      owner_national_id: item.owner.national_id,
      owner_email: item.owner.email,
      owner_phone: item.owner.phone,
      area: String(item.area),
      longitude: String(item.geometry.coordinates[0]),
      latitude: String(item.geometry.coordinates[1]),
      land_use: item.land_use,
      status: item.status,
      description: item.description,
    })
    setEditId(item.id)
    setShowForm(true)
  }

  async function handleNearby(e) {
    e.preventDefault()
    try {
      const res = await parcelsApi.nearby(
        parseFloat(nearbyForm.lng),
        parseFloat(nearbyForm.lat),
        parseFloat(nearbyForm.dist),
      )
      setNearbyResults(res.data)
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h2 style={styles.title}>Parcels</h2>
        <button style={styles.btn} onClick={() => { setForm(EMPTY_FORM); setEditId(null); setShowForm(true) }}>
          + New Parcel
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} style={styles.form}>
          <h3 style={{ margin: 0 }}>{editId ? 'Edit Parcel' : 'New Parcel'}</h3>
          <div style={styles.grid2}>
            {[['parcel_code','Parcel Code'],['parcel_number','Parcel Number'],['zone_id','Zone ID']].map(([k, label]) => (
              <label key={k} style={styles.label}>
                {label}
                <input style={styles.input} value={form[k]} disabled={!!editId}
                  onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))} required />
              </label>
            ))}
            {[['owner_name','Owner Name'],['owner_national_id','Owner National ID'],
              ['owner_email','Owner Email'],['owner_phone','Owner Phone']].map(([k, label]) => (
              <label key={k} style={styles.label}>
                {label}
                <input style={styles.input} type={k === 'owner_email' ? 'email' : 'text'} value={form[k]}
                  onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
                  required={k !== 'owner_phone'} />
              </label>
            ))}
            {[['area','Area (m²)'],['longitude','Longitude'],['latitude','Latitude'],['land_use','Land Use']].map(([k, label]) => (
              <label key={k} style={styles.label}>
                {label}
                <input style={styles.input} value={form[k]}
                  onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))} required={k !== 'land_use'} />
              </label>
            ))}
            <label style={styles.label}>
              Status
              <select style={styles.input} value={form.status}
                onChange={e => setForm(f => ({ ...f, status: e.target.value }))}>
                {['active','inactive','under_transfer','subdivided'].map(s => <option key={s}>{s}</option>)}
              </select>
            </label>
          </div>
          <label style={styles.label}>
            Description
            <textarea style={{ ...styles.input, height: 60 }} value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          </label>
          <div style={{ display:'flex', gap:8 }}>
            <button type="submit" style={styles.btn}>{editId ? 'Update' : 'Create'}</button>
            <button type="button" style={styles.btnGhost}
              onClick={() => { setShowForm(false); setEditId(null) }}>Cancel</button>
          </div>
        </form>
      )}

      <div style={styles.section}>
        <h3 style={styles.sectionTitle}>Find Nearby (2dsphere)</h3>
        <form onSubmit={handleNearby} style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
          <input style={{ ...styles.input, width:120 }} placeholder="Longitude"
            value={nearbyForm.lng} onChange={e => setNearbyForm(f=>({...f,lng:e.target.value}))} required />
          <input style={{ ...styles.input, width:120 }} placeholder="Latitude"
            value={nearbyForm.lat} onChange={e => setNearbyForm(f=>({...f,lat:e.target.value}))} required />
          <input style={{ ...styles.input, width:120 }} placeholder="Max dist (m)"
            value={nearbyForm.dist} onChange={e => setNearbyForm(f=>({...f,dist:e.target.value}))} />
          <button style={styles.btn} type="submit">Search</button>
          {nearbyResults !== null && (
            <button style={styles.btnGhost} type="button" onClick={() => setNearbyResults(null)}>Clear</button>
          )}
        </form>
        {nearbyResults !== null && (
          <p style={{ marginTop:8, color:'#888' }}>Found {nearbyResults.length} parcel(s) nearby.</p>
        )}
      </div>

      {loading ? <p>Loading…</p> : (
        <table style={styles.table}>
          <thead><tr>
            {['Number','Owner','Area (m²)','Status','Coordinates','Actions'].map(h =>
              <th key={h} style={styles.th}>{h}</th>)}
          </tr></thead>
          <tbody>
            {(nearbyResults ?? items).map(item => (
              <tr key={item.id}>
                <td style={styles.td}>{item.parcel_number}</td>
                <td style={styles.td}>{item.owner.name}</td>
                <td style={styles.td}>{item.area}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, background: statusColor(item.status) }}>{item.status}</span>
                </td>
                <td style={styles.td}>
                  {item.geometry.coordinates[1].toFixed(4)}, {item.geometry.coordinates[0].toFixed(4)}
                </td>
                <td style={styles.td}>
                  <button style={styles.btnSm} onClick={() => openEdit(item)}>Edit</button>
                  <button style={{ ...styles.btnSm, background:'#c0392b' }} onClick={() => handleDelete(item.id)}>Del</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={styles.pagination}>
        <button style={styles.btnGhost} disabled={page === 1} onClick={() => setPage(p => p-1)}>← Prev</button>
        <span style={{ color:'#888' }}>Page {page} · {total} total</span>
        <button style={styles.btnGhost} disabled={page * limit >= total} onClick={() => setPage(p => p+1)}>Next →</button>
      </div>
    </div>
  )
}

function statusColor(s) {
  if (s === 'active') return '#27ae60'
  if (s === 'inactive') return '#7f8c8d'
  if (s === 'under_transfer') return '#f39c12'
  return '#8e44ad'
}

const styles = {
  page: { padding: 24 },
  header: { display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 },
  title: { margin:0, fontSize:22 },
  form: { background:'#f9f9f9', border:'1px solid #ddd', borderRadius:8, padding:20, marginBottom:20,
    display:'flex', flexDirection:'column', gap:12 },
  grid2: { display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 },
  label: { display:'flex', flexDirection:'column', gap:4, fontSize:13, fontWeight:500 },
  input: { padding:'8px 10px', border:'1px solid #ccc', borderRadius:6, fontSize:14 },
  btn: { padding:'8px 16px', background:'#4f8ef7', color:'#fff', border:'none', borderRadius:6,
    cursor:'pointer', fontSize:14, fontWeight:600 },
  btnGhost: { padding:'8px 16px', background:'none', border:'1px solid #ccc', borderRadius:6,
    cursor:'pointer', fontSize:14 },
  btnSm: { padding:'4px 10px', background:'#4f8ef7', color:'#fff', border:'none', borderRadius:4,
    cursor:'pointer', fontSize:12, marginRight:4 },
  table: { width:'100%', borderCollapse:'collapse', fontSize:13 },
  th: { textAlign:'left', padding:'10px 12px', background:'#f0f0f0', borderBottom:'1px solid #ddd' },
  td: { padding:'10px 12px', borderBottom:'1px solid #eee', verticalAlign:'middle' },
  badge: { padding:'2px 8px', borderRadius:10, color:'#fff', fontSize:11, fontWeight:600 },
  pagination: { display:'flex', gap:12, alignItems:'center', marginTop:16 },
  section: { marginBottom:20, padding:16, background:'#f9f9f9', borderRadius:8, border:'1px solid #eee' },
  sectionTitle: { margin:'0 0 10px', fontSize:15 },
}
