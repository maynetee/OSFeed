import { api } from './axios-instance'

export const authApi = {
  /**
   * Authenticate a user with email and password credentials.
   * Returns an access token upon successful authentication.
   *
   * @param email - User's email address
   * @param password - User's password
   * @returns Promise resolving to authentication response with access token
   */
  login: (email: string, password: string) =>
    api.post('/api/auth/login', new URLSearchParams({ username: email, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),

  /**
   * Register a new user account with email and password.
   * Creates a new user account that requires email verification.
   *
   * @param email - Email address for the new account
   * @param password - Password for the new account
   * @returns Promise resolving to registration response
   */
  register: (email: string, password: string) =>
    api.post('/api/auth/register', { email, password }),

  /**
   * Verify a user's email address using a verification token.
   * Activates the user account after successful verification.
   *
   * @param token - Email verification token sent to the user's email
   * @returns Promise resolving to verification response
   */
  verifyEmail: (token: string) =>
    api.post('/api/auth/verify', { token }),

  /**
   * Request a new email verification token.
   * Sends a new verification email to the specified address.
   *
   * @param email - Email address to send the verification token to
   * @returns Promise resolving to request response
   */
  requestVerification: (email: string) =>
    api.post('/api/auth/request-verify-token', { email }),

  /**
   * Initiate password reset process for a user account.
   * Sends a password reset token to the specified email address.
   *
   * @param email - Email address of the account to reset
   * @returns Promise resolving to password reset request response
   */
  forgotPassword: (email: string) =>
    api.post('/api/auth/forgot-password', { email }),

  /**
   * Reset a user's password using a reset token.
   * Completes the password reset process with a new password.
   *
   * @param token - Password reset token sent to the user's email
   * @param password - New password for the account
   * @returns Promise resolving to password reset response
   */
  resetPassword: (token: string, password: string) =>
    api.post('/api/auth/reset-password', { token, password }),

  /**
   * Retrieve the currently authenticated user's profile information.
   * Returns user details including email, verification status, and preferences.
   *
   * @returns Promise resolving to the current user's profile data
   */
  me: () => api.get('/api/auth/me'),

  /**
   * Log out the currently authenticated user.
   * Invalidates the current access token and ends the session.
   *
   * @returns Promise resolving to logout response
   */
  logout: () => api.post('/api/auth/logout'),
}
