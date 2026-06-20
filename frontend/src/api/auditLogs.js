import { api } from './client'

export const auditLogsApi = {
  list: (page = 1, limit = 20, action, entityId) => {
    const params = new URLSearchParams({ page, limit })
    if (action) params.set('action', action)
    if (entityId) params.set('entity_id', entityId)
    return api.get(`/audit-logs?${params}`)
  },
}
