import { api } from './client'

export const usersApi = {
  list: (page = 1, limit = 20) => api.get(`/users?page=${page}&limit=${limit}`),
  get: (id) => api.get(`/users/${id}`),
  create: (data) => api.post('/users', data),
  update: (id, data) => api.patch(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
}
