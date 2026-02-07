import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AxiosError } from 'axios'
import { Loader2 } from 'lucide-react'
import { motion } from 'framer-motion'

import { useUserStore } from '@/stores/user-store'
import { authApi } from '@/lib/api/client'
import { PageLayout } from '../landing/components/PageLayout'
import { Seo } from '../landing/components/Seo'
import { trackEvent } from '@/lib/analytics'

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1, "Password is required"),
})

type LoginFormValues = z.infer<typeof loginSchema>

const getErrorMessage = (detail: string | undefined): string => {
  switch (detail) {
    case 'LOGIN_BAD_CREDENTIALS':
      return 'Invalid email or password'
    case 'LOGIN_USER_NOT_VERIFIED':
      return 'Please verify your email before logging in'
    default:
      return detail || 'Login failed. Please try again.'
  }
}

export function LoginPage() {
  const navigate = useNavigate()
  const { setUser } = useUserStore()
  const [error, setError] = useState<string | null>(null)

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const handleLogin = async (values: LoginFormValues) => {
    setError(null)
    trackEvent("Login Submit")
    try {
      // Login - tokens are set as httpOnly cookies automatically
      const response = await authApi.login(values.email, values.password)

      // Extract user info from login response
      setUser({
        id: response.data.user.id,
        email: response.data.user.email,
        name: response.data.user.email.split('@')[0],
      })

      navigate('/feed')
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(getErrorMessage(axiosError.response?.data?.detail))
    }
  }

  return (
    <PageLayout>
      <Seo title="Login — Osfeed" description="Sign in to your Osfeed account to access your intelligence dashboard." />
      <section className="flex items-center justify-center px-4 py-20 sm:py-32">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, ease: 'easeOut' }}
          className="w-full max-w-md rounded-2xl border p-8"
          style={{
            backgroundColor: '#161B22',
            borderColor: '#30363D',
          }}
        >
          <h1 className="text-3xl font-bold text-center mb-8" style={{ color: '#FFFFFF' }}>
            Welcome back
          </h1>

          {error && (
            <div
              className="mb-6 rounded-lg p-3 text-sm font-medium border"
              style={{
                backgroundColor: 'rgba(248, 81, 73, 0.1)',
                borderColor: 'rgba(248, 81, 73, 0.3)',
                color: '#F85149',
              }}
            >
              {error}
            </div>
          )}

          <form className="space-y-5" onSubmit={form.handleSubmit(handleLogin)}>
            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium" style={{ color: '#8B949E' }}>
                Email
              </label>
              <input
                id="email"
                type="email"
                placeholder="name@example.com"
                className="w-full h-11 rounded-lg border px-3 text-sm outline-none transition-colors"
                style={{
                  backgroundColor: '#0D1117',
                  borderColor: '#30363D',
                  color: '#FFFFFF',
                }}
                {...form.register('email')}
                onFocus={(e) => { e.target.style.borderColor = '#00D4AA' }}
                onBlur={(e) => { e.target.style.borderColor = '#30363D'; form.register('email').onBlur(e) }}
              />
              {form.formState.errors.email && (
                <span className="text-xs font-medium" style={{ color: '#F85149' }}>
                  {form.formState.errors.email.message}
                </span>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label htmlFor="password" className="block text-sm font-medium" style={{ color: '#8B949E' }}>
                  Password
                </label>
                <Link
                  to="/forgot-password"
                  className="text-xs transition-colors"
                  style={{ color: '#8B949E' }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = '#00D4AA' }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = '#8B949E' }}
                >
                  Forgot password?
                </Link>
              </div>
              <input
                id="password"
                type="password"
                className="w-full h-11 rounded-lg border px-3 text-sm outline-none transition-colors"
                style={{
                  backgroundColor: '#0D1117',
                  borderColor: '#30363D',
                  color: '#FFFFFF',
                }}
                {...form.register('password')}
                onFocus={(e) => { e.target.style.borderColor = '#00D4AA' }}
                onBlur={(e) => { e.target.style.borderColor = '#30363D'; form.register('password').onBlur(e) }}
              />
              {form.formState.errors.password && (
                <span className="text-xs font-medium" style={{ color: '#F85149' }}>
                  {form.formState.errors.password.message}
                </span>
              )}
            </div>

            <button
              type="submit"
              disabled={form.formState.isSubmitting}
              className="w-full h-11 rounded-lg text-sm font-semibold transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
              style={{
                backgroundColor: '#00D4AA',
                color: '#0D1117',
              }}
            >
              {form.formState.isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Log in'
              )}
            </button>
          </form>

          <p className="mt-6 text-center text-sm" style={{ color: '#8B949E' }}>
            Don&apos;t have an account?{' '}
            <Link
              to="/signup"
              className="font-medium transition-colors"
              style={{ color: '#00D4AA' }}
              onMouseEnter={(e) => { e.currentTarget.style.color = '#FFFFFF' }}
              onMouseLeave={(e) => { e.currentTarget.style.color = '#00D4AA' }}
            >
              Sign up
            </Link>
          </p>
        </motion.div>
      </section>
    </PageLayout>
  )
}
