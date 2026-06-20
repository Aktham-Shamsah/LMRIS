import { api, API_BASE } from './client'

export const applicationsApi = {
  list: (page = 1, limit = 20, status, search) => {
    const params = new URLSearchParams({ page, limit })
    if (status) params.set('status', status)
    if (search) params.set('search', search)
    return api.get(`/applications?${params}`)
  },
  get: (id) => api.get(`/applications/${id}`),
  create: (data) => api.post('/applications', data),
  transition: (id, data) => api.patch(`/applications/${id}/transition`, data),
  placeOnHold: (id, reason, performedBy) =>
    api.post(`/applications/${id}/hold`, { reason, performed_by: performedBy || 'registrar' }),
  reject: (id, reason, performedBy) =>
    api.post(`/applications/${id}/reject`, { reason, performed_by: performedBy || 'registrar' }),
  issueCertificate: (id, performedBy) =>
    api.post(`/applications/${id}/certificate`, { performed_by: performedBy || 'registrar' }),
  listAttachments: (id) => api.get(`/applications/${id}/attachments`),
  listNotes: (id) => api.get(`/applications/${id}/notes`),
  addNote: (id, text, performedBy) =>
    api.post(`/applications/${id}/notes`, { text, performed_by: performedBy || 'registrar' }),
  uploadAttachment: (id, file, performedBy) =>
    api.upload(`/applications/${id}/attachments`, file, { performed_by: performedBy || 'registrar' }),
  verifyAttachment: (id, attachmentId, performedBy) =>
    api.post(`/applications/${id}/attachments/${attachmentId}/verify`, { performed_by: performedBy || 'registrar' }),
  deleteAttachment: (id, attachmentId, performedBy) =>
    api.delete(`/applications/${id}/attachments/${attachmentId}?performed_by=${encodeURIComponent(performedBy || 'registrar')}`),
  attachmentDownloadUrl: (id, attachmentId) => `${API_BASE}/applications/${id}/attachments/${attachmentId}/download`,
}
