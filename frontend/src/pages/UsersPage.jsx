import { useState, useEffect, useCallback } from 'react'
import { usersApi } from '../api/users'

const EMPTY_FORM = { name: '', email: '', phone: '', role: 'user' }

export default function UsersPage({ onToast }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [editId, setEditId] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const limit = 10

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await usersApi.list(page, limit)
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
    try {
      if (editId) {
        await usersApi.update(editId, { name: form.name, phone: form.phone, role: form.role })
        onToast('User updated.')
      } else {
        await usersApi.create(form)
        onToast('User created.')
      }
      setShowForm(false); setEditId(null); setForm(EMPTY_FORM); load()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  async function handleDelete(id) {
    if (!confirm('Delete this user?')) return
    try {
      await usersApi.delete(id)
      onToast('User deleted.')
      load()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  function openEdit(item) {
    setForm({ name: item.name, email: item.email, phone: item.phone, role: item.role })
    setEditId(item.id); setShowForm(true)
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h2 style={styles.title}>Users</h2>
        <button style={styles.btn} onClick={() => { setForm(EMPTY_FORM); setEditId(null); setShowForm(true) }}>
          + New User
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} style={styles.form}>
          <h3 style={{ margin:0 }}>{editId ? 'Edit User' : 'New User'}</h3>
          <div style={styles.grid2}>
            {[['name','Name'],['email','Email'],['phone','Phone']].map(([k, label]) => (
              <label key={k} style={styles.label}>
                {label}
                <input style={styles.input} value={form[k]} type={k==='email'?'email':'text'}
                  disabled={editId && k === 'email'}
                  onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
                  required={k !== 'phone'} />
              </label>
            ))}
            <label style={styles.label}>
              Role
              <select style={styles.input} value={form.role}
                onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
                <option value="user">user</option>
                <option value="admin">admin</option>
              </select>
            </label>
          </div>
          <div style={{ display:'flex', gap:8 }}>
            <button type="submit" style={styles.btn}>{editId ? 'Update' : 'Create'}</button>
            <button type="button" style={styles.btnGhost}
              onClick={() => { setShowForm(false); setEditId(null) }}>Cancel</button>
          </div>
        </form>
      )}

      {loading ? <p>Loading…</p> : (
        <table style={styles.table}>
          <thead><tr>
            {['Name','Email','Phone','Role','Actions'].map(h => <th key={h} style={styles.th}>{h}</th>)}
          </tr></thead>
          <tbody>
            {items.map(u => (
              <tr key={u.id}>
                <td style={styles.td}>{u.name}</td>
                <td style={styles.td}>{u.email}</td>
                <td style={styles.td}>{u.phone || '—'}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, background: u.role==='admin'?'#8e44ad':'#2980b9' }}>{u.role}</span>
                </td>
                <td style={styles.td}>
                  <button style={styles.btnSm} onClick={() => openEdit(u)}>Edit</button>
                  <button style={{ ...styles.btnSm, background:'#c0392b' }} onClick={() => handleDelete(u.id)}>Del</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div style={styles.pagination}>
        <button style={styles.btnGhost} disabled={page===1} onClick={() => setPage(p=>p-1)}>← Prev</button>
        <span style={{ color:'#888' }}>Page {page} · {total} total</span>
        <button style={styles.btnGhost} disabled={page*limit>=total} onClick={() => setPage(p=>p+1)}>Next →</button>
      </div>
    </div>
  )
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
}
