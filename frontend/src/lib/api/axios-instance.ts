import axios, { type InternalAxiosRequestConfig } from 'axios'

import { useUserStore } from '@/stores/user-store'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// Refresh token queue - prevents concurrent refresh attempts
let isRefreshing = false
let failedQueue: Array<{
  resolve: () => void
  reject: (error: unknown) => void
}> = []

const processQueue = (error: unknown) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error)
    } else {
      promise.resolve()
    }
  })
  failedQueue = []
}

// Add response interceptor to handle 401 errors with automatic cookie-based refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Skip auth refresh for login/register/refresh endpoints
    const isAuthEndpoint = originalRequest?.url?.includes('/api/auth/login') ||
      originalRequest?.url?.includes('/api/auth/register') ||
      originalRequest?.url?.includes('/api/auth/refresh')

    // If not a 401, or already retried, or is an auth endpoint, reject immediately
    if (error.response?.status !== 401 || originalRequest._retry || isAuthEndpoint) {
      return Promise.reject(error)
    }

    // Mark this request so we don't retry it again
    originalRequest._retry = true

    // If a refresh is already in progress, queue this request to wait for the result
    if (isRefreshing) {
      return new Promise<void>((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then(() => {
        return api(originalRequest)
      })
    }

    isRefreshing = true

    const { logout } = useUserStore.getState()

    try {
      // Call refresh endpoint - cookies are sent automatically with withCredentials: true
      // The backend will read refresh_token from cookies and set new cookies in response
      await api.post(`${API_URL}/api/auth/refresh`)

      // Resolve all queued requests
      processQueue(null)

      // Retry the original request - new cookies will be sent automatically
      return api(originalRequest)
    } catch (refreshError) {
      // Refresh failed - reject all queued requests and logout once
      processQueue(refreshError)
      logout()
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
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
