import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.clearAuth()
      router.push({ name: 'Login' })
    }
    return Promise.reject(error)
  }
)

export default api

// 段位管理 API
export const rankApi = {
  list: () => api.get('/ranks'),
  get: (id: number) => api.get(`/ranks/${id}`),
  create: (data: { name: string; min_score: number; max_score: number | null; image_url: string; display_order: number }) =>
    api.post('/ranks', data),
  update: (id: number, data: Partial<{ name: string; min_score: number; max_score: number | null; image_url: string; display_order: number }>) =>
    api.put(`/ranks/${id}`, data),
  delete: (id: number) => api.delete(`/ranks/${id}`),
}
