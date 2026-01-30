import { api } from './axios-instance'

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/api/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  register: (email: string, password: string) =>
    api.post('/api/auth/register', { email, password }),
  verifyEmail: (token: string) =>
    api.post('/api/auth/verify', { token }),
  requestVerification: (email: string) =>
    api.post('/api/auth/request-verify-token', { email }),
  forgotPassword: (email: string) =>
    api.post('/api/auth/forgot-password', { email }),
  resetPassword: (token: string, password: string) =>
    api.post('/api/auth/reset-password', { token, password }),
  me: () => api.get('/api/auth/me'),
  logout: () => api.post('/api/auth/logout'),
}
