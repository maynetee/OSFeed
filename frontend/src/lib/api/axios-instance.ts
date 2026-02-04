import axios, { type InternalAxiosRequestConfig } from 'axios'

import { useUserStore } from '@/stores/user-store'

const API_URL = import.meta.env.VITE_API_URL || ''

/**
 * Configured Axios instance for API requests.
 * Includes automatic cookie-based authentication, JSON headers, and
 * automatic token refresh on 401 errors via response interceptor.
 *
 * @example
 * ```ts
 * // Make authenticated API calls
 * const response = await api.get('/api/users')
 * await api.post('/api/messages', { text: 'Hello' })
 * ```
 */
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

/**
 * Process all queued requests after token refresh completes.
 * Resolves or rejects queued promises based on refresh success/failure.
 *
 * @param error - Error from token refresh (null if successful)
 */
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

/**
 * Build URLSearchParams from an object, handling arrays and null values.
 * Converts object parameters to URL query string format suitable for axios requests.
 * Automatically handles array values by repeating the key for each item.
 *
 * @param params - Object containing query parameters
 * @returns URLSearchParams instance ready for use in axios requests
 *
 * @example
 * ```ts
 * const params = buildParams({
 *   channel_ids: ['123', '456'],
 *   limit: 10,
 *   offset: 0
 * })
 * // Results in: channel_ids=123&channel_ids=456&limit=10&offset=0
 * ```
 */
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
