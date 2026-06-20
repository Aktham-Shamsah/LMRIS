import { useState, useCallback } from 'react'
import Navbar from './components/Navbar'
import Toast from './components/Toast'
import ApplicationsPage from './pages/ApplicationsPage'
import ParcelsPage from './pages/ParcelsPage'
import UsersPage from './pages/UsersPage'
import AuditLogsPage from './pages/AuditLogsPage'

export default function App() {
  const [page, setPage] = useState('Applications')
  const [toast, setToast] = useState(null)

  const onToast = useCallback((message, type = 'success') => {
    setToast({ message, type })
  }, [])

  return (
    <div style={{ minHeight: '100vh', background: '#fafafa', fontFamily: 'system-ui, sans-serif' }}>
      <Navbar active={page} onNav={setPage} />
      <main style={{ maxWidth: 1100, margin: '0 auto' }}>
        {page === 'Applications' && <ApplicationsPage onToast={onToast} />}
        {page === 'Parcels' && <ParcelsPage onToast={onToast} />}
        {page === 'Users' && <UsersPage onToast={onToast} />}
        {page === 'Audit Logs' && <AuditLogsPage onToast={onToast} />}
      </main>
      {toast && (
        <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
      )}
    </div>
  )
}
