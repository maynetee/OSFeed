import axios from 'axios'

import { useUserStore } from '@/stores/user-store'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth interceptor to include JWT token
api.interceptors.request.use((config) => {
  const tokens = useUserStore.getState().tokens
  if (tokens?.accessToken) {
    config.headers.Authorization = `Bearer ${tokens.accessToken}`
  }
  return config
})

// Add response interceptor to handle 401 errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Skip auth refresh for login/register endpoints
    const isAuthEndpoint = originalRequest?.url?.includes('/api/auth/login') ||
      originalRequest?.url?.includes('/api/auth/register')

    // If 401 and we haven't already tried to refresh
    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true

      const { tokens, setTokens, logout } = useUserStore.getState()

      if (tokens?.refreshToken) {
        try {
          const response = await axios.post(`${API_URL}/api/auth/refresh`, {
            refresh_token: tokens.refreshToken,
          })

          const newTokens = {
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token,
            refreshExpiresAt: response.data.refresh_expires_at,
          }

          setTokens(newTokens)
          originalRequest.headers.Authorization = `Bearer ${newTokens.accessToken}`
          return api(originalRequest)
        } catch {
          // Refresh failed, logout user - AuthGuard will redirect
          logout()
        }
      } else {
        // No refresh token, logout - AuthGuard will redirect
        logout()
      }
    }

    return Promise.reject(error)
  }
)

export const buildParams = (params: Record<string, unknown>) => {
  const searchParams = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null) return
    if (Array.isArray(value)) {
      value.forEach((item) => searchParams.append(key, String(item)))
      return
    }
    searchParams.append(key, String(value))
  })
  return searchParams
}
