import { useRef, useState } from 'react'
import { applicationsApi } from '../api/applications'

const ICONS = { pdf: '📄', jpg: '🖼️', jpeg: '🖼️', png: '🖼️', doc: '📝', docx: '📝' }
const ACCEPT = '.pdf,.jpg,.jpeg,.png,.doc,.docx'

function iconFor(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  return ICONS[ext] || '📎'
}

function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function AttachmentsPanel({ appId, attachments, onToast, onChanged }) {
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(null)
  const fileInputRef = useRef(null)

  async function handleFiles(files) {
    if (!files || !files.length) return
    setUploading(true)
    try {
      for (const file of files) {
        await applicationsApi.uploadAttachment(appId, file, 'registrar')
      }
      onToast(files.length > 1 ? 'Files uploaded.' : 'File uploaded.')
      onChanged()
    } catch (e) {
      onToast(e.message, 'error')
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragOver(false)
    handleFiles(Array.from(e.dataTransfer.files))
  }

  async function handleVerify(attachmentId) {
    try {
      await applicationsApi.verifyAttachment(appId, attachmentId, 'registrar')
      onToast('Attachment verified.')
      onChanged()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  async function handleDelete(attachmentId) {
    try {
      await applicationsApi.deleteAttachment(appId, attachmentId, 'registrar')
      onToast('Attachment deleted.')
      setConfirmDelete(null)
      onChanged()
    } catch (e) {
      onToast(e.message, 'error')
    }
  }

  return (
    <div style={styles.card}>
      <div style={styles.headerRow}>
        <h3 style={styles.cardTitle}>Attachments</h3>
        <span style={styles.count}>{attachments.length} file{attachments.length !== 1 ? 's' : ''}</span>
      </div>

      <div
        style={{ ...styles.dropzone, ...(dragOver ? styles.dropzoneActive : {}) }}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPT}
          style={{ display: 'none' }}
          onChange={(e) => handleFiles(Array.from(e.target.files))}
        />
        {uploading ? (
          <p style={{ margin: 0 }}>Uploading…</p>
        ) : (
          <p style={{ margin: 0, color: '#888' }}>
            <b style={{ color: '#4f8ef7' }}>Click to upload</b> or drag and drop — PDF, JPG, PNG, DOC (max 10MB)
          </p>
        )}
      </div>

      {attachments.length === 0 ? (
        <p style={{ color: '#888', marginTop: 12 }}>No attachments uploaded.</p>
      ) : (
        <table style={{ ...styles.table, marginTop: 12 }}>
          <thead>
            <tr>{['', 'Filename', 'Size', 'Uploaded', 'Status', ''].map((h) => <th key={h} style={styles.th}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {attachments.map((d) => (
              <tr key={d.doc_id}>
                <td style={styles.td}>{iconFor(d.filename)}</td>
                <td style={styles.td}>
                  <a
                    href={applicationsApi.attachmentDownloadUrl(appId, d.doc_id)}
                    target="_blank"
                    rel="noreferrer"
                    style={styles.link}
                  >
                    {d.filename}
                  </a>
                </td>
                <td style={styles.td}>{formatSize(d.size_bytes)}</td>
                <td style={styles.td}>{new Date(d.uploaded_at).toLocaleString()}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.badge, background: d.verified ? '#27ae60' : '#e67e22' }}>
                    {d.verified ? 'Verified' : 'Pending'}
                  </span>
                </td>
                <td style={{ ...styles.td, whiteSpace: 'nowrap' }}>
                  {!d.verified && (
                    <button style={styles.btnSm} onClick={() => handleVerify(d.doc_id)}>Verify</button>
                  )}
                  <button style={{ ...styles.btnSm, background: '#c0392b' }} onClick={() => setConfirmDelete(d)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {confirmDelete && (
        <div style={styles.overlay}>
          <div style={styles.modal}>
            <h3 style={{ margin: 0 }}>Delete attachment?</h3>
            <p style={{ margin: 0, color: '#666' }}>
              This will permanently delete <b>{confirmDelete.filename}</b>. This cannot be undone.
            </p>
            <div style={{ display: 'flex', gap: 8 }}>
              <button style={{ ...styles.btn, background: '#c0392b' }} onClick={() => handleDelete(confirmDelete.doc_id)}>
                Delete
              </button>
              <button style={styles.btnGhost} onClick={() => setConfirmDelete(null)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const styles = {
  card: { background: '#f9f9f9', border: '1px solid #eee', borderRadius: 8, padding: 16 },
  headerRow: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  cardTitle: { margin: 0, fontSize: 15 },
  count: { color: '#888', fontSize: 13 },
  dropzone: {
    marginTop: 10, border: '2px dashed #ccc', borderRadius: 8, padding: '20px 16px',
    textAlign: 'center', cursor: 'pointer', background: '#fff', transition: 'border-color .15s, background .15s',
  },
  dropzoneActive: { borderColor: '#4f8ef7', background: '#eef4ff' },
  link: { color: '#4f8ef7', textDecoration: 'none' },
  btn: { padding: '8px 16px', background: '#4f8ef7', color: '#fff', border: 'none', borderRadius: 6,
    cursor: 'pointer', fontSize: 14, fontWeight: 600 },
  btnGhost: { padding: '8px 16px', background: 'none', border: '1px solid #ccc', borderRadius: 6,
    cursor: 'pointer', fontSize: 14 },
  btnSm: { padding: '4px 10px', background: '#4f8ef7', color: '#fff', border: 'none', borderRadius: 4,
    cursor: 'pointer', fontSize: 12, marginRight: 6 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: { textAlign: 'left', padding: '8px 10px', background: '#f0f0f0', borderBottom: '1px solid #ddd' },
  td: { padding: '8px 10px', borderBottom: '1px solid #eee', verticalAlign: 'middle' },
  badge: { padding: '2px 8px', borderRadius: 10, color: '#fff', fontSize: 11, fontWeight: 600 },
  overlay: { position: 'fixed', inset: 0, background: 'rgba(0,0,0,.4)', display: 'flex',
    alignItems: 'center', justifyContent: 'center', zIndex: 1000 },
  modal: { background: '#fff', borderRadius: 8, padding: 24, width: 400,
    display: 'flex', flexDirection: 'column', gap: 12 },
}
