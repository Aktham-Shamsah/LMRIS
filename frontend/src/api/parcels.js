import { api } from './client'

export const parcelsApi = {
  list: (page = 1, limit = 20, status) => {
    const params = new URLSearchParams({ page, limit })
    if (status) params.set('status', status)
    return api.get(`/parcels?${params}`)
  },
  get: (id) => api.get(`/parcels/${id}`),
  create: (data) => api.post('/parcels', data),
  update: (id, data) => api.patch(`/parcels/${id}`, data),
  delete: (id) => api.delete(`/parcels/${id}`),
  nearby: (lng, lat, maxDist = 5000, limit = 20) =>
    api.get(`/parcels/nearby?longitude=${lng}&latitude=${lat}&max_distance_meters=${maxDist}&limit=${limit}`),
}
