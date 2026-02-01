import axios, { type InternalAxiosRequestConfig } from 'axios'

import { useUserStore } from '@/stores/user-store'

const API_URL = import.meta.env.VITE_API_URL || ''

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Check if a JWT access token is expired (or near-expired).
 * Decodes the base64 payload to read the `exp` claim.
 * Returns true if the token is expired, will expire within the buffer, or is malformed.
 */
export function isTokenExpired(token: string, bufferSeconds = 60): boolean {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return true
    const payload = JSON.parse(atob(parts[1]))
    const exp = payload.exp
    if (typeof exp !== 'number') return true
    return Date.now() >= exp * 1000 - bufferSeconds * 1000
  } catch {
    return true // Treat decode failures as expired
  }
}

// Refresh token queue - prevents concurrent refresh attempts
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (error: unknown) => void
}> = []

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error)
    } else {
      promise.resolve(token!)
    }
  })
  failedQueue = []
}

// Add auth interceptor to include JWT token
api.interceptors.request.use((config) => {
  const tokens = useUserStore.getState().tokens
  if (tokens?.accessToken) {
    config.headers.Authorization = `Bearer ${tokens.accessToken}`
  }
  return config
})

// Add response interceptor to handle 401 errors with refresh token queue
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
      return new Promise<string>((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then((newToken) => {
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      })
    }

    isRefreshing = true

    const { tokens, setTokens, logout } = useUserStore.getState()

    if (!tokens?.refreshToken) {
      isRefreshing = false
      processQueue(error)
      logout()
      return Promise.reject(error)
    }

    try {
      // Use plain axios (not api instance) to avoid interceptor recursion
      const response = await axios.post(`${API_URL}/api/auth/refresh`, {
        refresh_token: tokens.refreshToken,
      })

      const newTokens = {
        accessToken: response.data.access_token as string,
        refreshToken: response.data.refresh_token as string,
        refreshExpiresAt: response.data.refresh_expires_at as string,
      }

      setTokens(newTokens)

      // Resolve all queued requests with the new token
      processQueue(null, newTokens.accessToken)

      // Retry the original request with the new token
      originalRequest.headers.Authorization = `Bearer ${newTokens.accessToken}`
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
