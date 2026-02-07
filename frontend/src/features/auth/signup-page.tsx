import { useState } from 'react'
import { useNavigate, Link, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AxiosError } from 'axios'
import { Loader2, Check, X, ChevronDown } from 'lucide-react'
import { motion } from 'framer-motion'

import { useUserStore } from '@/stores/user-store'
import { authApi } from '@/lib/api/client'
import { PageLayout } from '@/features/landing/components/PageLayout'
import { Seo } from '@/features/landing/components/Seo'
import { trackEvent } from '@/lib/analytics'

const COUNTRIES = [
  { code: 'US', name: 'United States' },
  { code: 'GB', name: 'United Kingdom' },
  { code: 'FR', name: 'France' },
  { code: 'DE', name: 'Germany' },
  { code: 'CA', name: 'Canada' },
  { code: 'AU', name: 'Australia' },
  { code: 'NL', name: 'Netherlands' },
  { code: 'BE', name: 'Belgium' },
  { code: 'CH', name: 'Switzerland' },
  { code: 'ES', name: 'Spain' },
  { code: 'IT', name: 'Italy' },
  { code: 'PT', name: 'Portugal' },
  { code: 'SE', name: 'Sweden' },
  { code: 'NO', name: 'Norway' },
  { code: 'DK', name: 'Denmark' },
  { code: 'IL', name: 'Israel' },
  { code: 'JP', name: 'Japan' },
  { code: 'SG', name: 'Singapore' },
  { code: 'BR', name: 'Brazil' },
  { code: 'IN', name: 'India' },
] as const

const signupSchema = z.object({
  username: z
    .string()
    .min(3, 'Username must be at least 3 characters')
    .max(20, 'Username must be at most 20 characters')
    .regex(/^[a-zA-Z0-9]+$/, 'Username must be alphanumeric only'),
  email: z.string().email('Please enter a valid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/\d/, 'Password must contain at least one number'),
  country: z.string().min(1, 'Please select a country'),
  plan: z.enum(['solo', 'team'], { required_error: 'Please select a plan' }),
  terms: z.literal(true, {
    errorMap: () => ({ message: 'You must accept the terms and conditions' }),
  }),
})

type SignupFormValues = z.infer<typeof signupSchema>

const fadeInUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: 'easeOut' as const },
}

export function SignupPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { setUser } = useUserStore()
  const [error, setError] = useState<string | null>(null)
  const [registrationSuccess, setRegistrationSuccess] = useState(false)
  const [registeredEmail, setRegisteredEmail] = useState('')
  const [resendSent, setResendSent] = useState(false)

  const preselectedPlan = searchParams.get('plan')
  const defaultPlan = preselectedPlan === 'team' ? 'team' : 'solo'

  const form = useForm<SignupFormValues>({
    resolver: zodResolver(signupSchema),
    defaultValues: {
      username: '',
      email: '',
      password: '',
      country: '',
      plan: defaultPlan,
      terms: false as unknown as true,
    },
    mode: 'onChange',
  })

  const password = form.watch('password')
  const selectedPlan = form.watch('plan')

  const requirements = [
    { label: 'At least 8 characters', met: (password?.length || 0) >= 8 },
    { label: 'One uppercase letter', met: /[A-Z]/.test(password || '') },
    { label: 'One number', met: /\d/.test(password || '') },
  ]

  const handleSignup = async (values: SignupFormValues) => {
    setError(null)
    trackEvent("Signup Submit")
    try {
      const response = await authApi.register(values.email, values.password, {
        username: values.username,
        country: values.country,
        plan: values.plan,
      })

      if (response.data.is_verified === false) {
        setRegisteredEmail(values.email)
        setRegistrationSuccess(true)
      } else {
        const loginResponse = await authApi.login(values.email, values.password)
        setUser({
          id: loginResponse.data.user.id,
          email: loginResponse.data.user.email,
          name: values.username,
        })
        navigate('/feed')
      }
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string | { code: string; reason: string } }>
      const detail = axiosError.response?.data?.detail
      if (typeof detail === 'object' && detail !== null) {
        setError(detail.reason || 'Registration failed. Please try again.')
      } else if (detail === 'REGISTER_USER_ALREADY_EXISTS') {
        setError('An account with this email already exists')
      } else {
        setError(typeof detail === 'string' ? detail : 'Registration failed. Please try again.')
      }
    }
  }

  const handleResendVerification = async () => {
    if (!registeredEmail) return
    try {
      await authApi.requestVerification(registeredEmail)
      setResendSent(true)
    } catch {
      setResendSent(true)
    }
  }

  if (registrationSuccess) {
    return (
      <PageLayout>
        <section className="px-6 py-20 md:py-28">
          <motion.div
            className="mx-auto max-w-md rounded-2xl p-8 text-center"
            style={{ backgroundColor: '#161B22', border: '1px solid #30363D' }}
            {...fadeInUp}
          >
            <div
              className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full"
              style={{ backgroundColor: 'rgba(0, 212, 170, 0.1)' }}
            >
              <Check className="h-8 w-8" style={{ color: '#00D4AA' }} />
            </div>
            <h2 className="text-2xl font-bold mb-2" style={{ color: '#FFFFFF' }}>
              Check your email
            </h2>
            <p className="text-sm mb-6" style={{ color: '#8B949E' }}>
              We've sent a verification link to <strong style={{ color: '#FFFFFF' }}>{registeredEmail}</strong>.
              Please click the link to verify your account.
            </p>
            {resendSent ? (
              <p className="text-sm" style={{ color: '#8B949E' }}>
                A new verification email has been sent.
              </p>
            ) : (
              <p className="text-sm" style={{ color: '#8B949E' }}>
                Didn't receive it?{' '}
                <button
                  type="button"
                  className="font-medium hover:underline"
                  style={{ color: '#00D4AA' }}
                  onClick={handleResendVerification}
                >
                  Resend verification email
                </button>
              </p>
            )}
            <div className="mt-6 pt-6" style={{ borderTop: '1px solid #30363D' }}>
              <Link
                to="/login"
                className="text-sm font-medium hover:underline"
                style={{ color: '#00D4AA' }}
              >
                Back to login
              </Link>
            </div>
          </motion.div>
        </section>
      </PageLayout>
    )
  }

  return (
    <PageLayout>
      <Seo title="Sign Up — Osfeed" description="Create your Osfeed account and start monitoring Telegram channels with real-time translation and intelligence." />
      <section className="px-6 py-20 md:py-28">
        <div className="mx-auto max-w-lg">
          <motion.div className="text-center mb-10" {...fadeInUp}>
            <h1 className="text-3xl md:text-4xl font-bold" style={{ color: '#FFFFFF' }}>
              Create your account
            </h1>
            <p className="mt-3 text-base" style={{ color: '#8B949E' }}>
              Start monitoring OSINT sources in minutes.
            </p>
          </motion.div>

          <motion.div
            className="rounded-2xl p-8"
            style={{ backgroundColor: '#161B22', border: '1px solid #30363D' }}
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut', delay: 0.1 }}
          >
            {error && (
              <div
                className="mb-6 rounded-lg p-3 text-sm font-medium"
                style={{
                  backgroundColor: 'rgba(248, 81, 73, 0.1)',
                  border: '1px solid rgba(248, 81, 73, 0.3)',
                  color: '#F85149',
                }}
              >
                {error}
              </div>
            )}

            <form className="space-y-5" onSubmit={form.handleSubmit(handleSignup)}>
              {/* Username */}
              <div className="space-y-2">
                <label htmlFor="username" className="block text-sm font-medium" style={{ color: '#FFFFFF' }}>
                  Username
                </label>
                <input
                  id="username"
                  type="text"
                  placeholder="johndoe"
                  className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-colors"
                  style={{
                    backgroundColor: '#0D1117',
                    border: form.formState.errors.username ? '1px solid #F85149' : '1px solid #30363D',
                    color: '#FFFFFF',
                  }}
                  {...form.register('username')}
                  onFocus={(e) => {
                    if (!form.formState.errors.username) e.currentTarget.style.borderColor = '#00D4AA'
                  }}
                />
                {form.formState.errors.username && (
                  <p className="text-xs font-medium" style={{ color: '#F85149' }}>
                    {form.formState.errors.username.message}
                  </p>
                )}
              </div>

              {/* Email */}
              <div className="space-y-2">
                <label htmlFor="email" className="block text-sm font-medium" style={{ color: '#FFFFFF' }}>
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-colors"
                  style={{
                    backgroundColor: '#0D1117',
                    border: form.formState.errors.email ? '1px solid #F85149' : '1px solid #30363D',
                    color: '#FFFFFF',
                  }}
                  {...form.register('email')}
                  onFocus={(e) => {
                    if (!form.formState.errors.email) e.currentTarget.style.borderColor = '#00D4AA'
                  }}
                />
                {form.formState.errors.email && (
                  <p className="text-xs font-medium" style={{ color: '#F85149' }}>
                    {form.formState.errors.email.message}
                  </p>
                )}
              </div>

              {/* Password */}
              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium" style={{ color: '#FFFFFF' }}>
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-colors"
                  style={{
                    backgroundColor: '#0D1117',
                    border: form.formState.errors.password ? '1px solid #F85149' : '1px solid #30363D',
                    color: '#FFFFFF',
                  }}
                  {...form.register('password')}
                  onFocus={(e) => {
                    if (!form.formState.errors.password) e.currentTarget.style.borderColor = '#00D4AA'
                  }}
                />
                {form.formState.errors.password && (
                  <p className="text-xs font-medium" style={{ color: '#F85149' }}>
                    {form.formState.errors.password.message}
                  </p>
                )}
                <div className="mt-2 space-y-1.5">
                  {requirements.map((req, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs">
                      {req.met ? (
                        <Check className="h-3.5 w-3.5" style={{ color: '#00D4AA' }} />
                      ) : (
                        <X className="h-3.5 w-3.5" style={{ color: '#484F58' }} />
                      )}
                      <span style={{ color: req.met ? '#00D4AA' : '#8B949E' }}>{req.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Country */}
              <div className="space-y-2">
                <label htmlFor="country" className="block text-sm font-medium" style={{ color: '#FFFFFF' }}>
                  Country
                </label>
                <div className="relative">
                  <select
                    id="country"
                    className="w-full appearance-none rounded-lg px-4 py-2.5 text-sm outline-none transition-colors"
                    style={{
                      backgroundColor: '#0D1117',
                      border: form.formState.errors.country ? '1px solid #F85149' : '1px solid #30363D',
                      color: form.watch('country') ? '#FFFFFF' : '#8B949E',
                    }}
                    {...form.register('country')}
                    onFocus={(e) => {
                      if (!form.formState.errors.country) e.currentTarget.style.borderColor = '#00D4AA'
                    }}
                  >
                    <option value="">Select your country</option>
                    {COUNTRIES.map((c) => (
                      <option key={c.code} value={c.code}>
                        {c.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown
                    className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4"
                    style={{ color: '#8B949E' }}
                  />
                </div>
                {form.formState.errors.country && (
                  <p className="text-xs font-medium" style={{ color: '#F85149' }}>
                    {form.formState.errors.country.message}
                  </p>
                )}
              </div>

              {/* Plan Selector */}
              <div className="space-y-2">
                <label className="block text-sm font-medium" style={{ color: '#FFFFFF' }}>
                  Plan
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { value: 'solo' as const, label: 'Solo', price: '€99/mo', desc: '1 user' },
                    { value: 'team' as const, label: 'Team', price: '€399/mo', desc: 'Up to 5 users' },
                  ].map((plan) => (
                    <label
                      key={plan.value}
                      className="relative flex cursor-pointer flex-col rounded-lg p-4 transition-colors"
                      style={{
                        backgroundColor: '#0D1117',
                        border:
                          selectedPlan === plan.value
                            ? '2px solid #00D4AA'
                            : '1px solid #30363D',
                      }}
                    >
                      <input
                        type="radio"
                        value={plan.value}
                        className="sr-only"
                        {...form.register('plan')}
                      />
                      <span className="text-sm font-semibold" style={{ color: '#FFFFFF' }}>
                        {plan.label}
                      </span>
                      <span className="mt-1 text-lg font-bold" style={{ color: '#00D4AA' }}>
                        {plan.price}
                      </span>
                      <span className="mt-0.5 text-xs" style={{ color: '#8B949E' }}>
                        {plan.desc}
                      </span>
                      {selectedPlan === plan.value && (
                        <div
                          className="absolute top-2 right-2 flex h-5 w-5 items-center justify-center rounded-full"
                          style={{ backgroundColor: '#00D4AA' }}
                        >
                          <Check className="h-3 w-3" style={{ color: '#0D1117' }} />
                        </div>
                      )}
                    </label>
                  ))}
                </div>
                {form.formState.errors.plan && (
                  <p className="text-xs font-medium" style={{ color: '#F85149' }}>
                    {form.formState.errors.plan.message}
                  </p>
                )}
              </div>

              {/* Terms */}
              <div className="space-y-2">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    className="mt-0.5 h-4 w-4 rounded border-gray-600 accent-[#00D4AA]"
                    {...form.register('terms')}
                  />
                  <span className="text-sm" style={{ color: '#8B949E' }}>
                    I agree to the{' '}
                    <Link to="/terms" className="font-medium hover:underline" style={{ color: '#00D4AA' }}>
                      Terms of Service
                    </Link>{' '}
                    and{' '}
                    <Link to="/privacy" className="font-medium hover:underline" style={{ color: '#00D4AA' }}>
                      Privacy Policy
                    </Link>
                  </span>
                </label>
                {form.formState.errors.terms && (
                  <p className="text-xs font-medium" style={{ color: '#F85149' }}>
                    {form.formState.errors.terms.message}
                  </p>
                )}
              </div>

              {/* Submit */}
              <button
                type="submit"
                disabled={form.formState.isSubmitting}
                className="w-full rounded-lg py-3 text-sm font-semibold transition-opacity hover:opacity-90 disabled:opacity-50"
                style={{ backgroundColor: '#00D4AA', color: '#0D1117' }}
              >
                {form.formState.isSubmitting ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Creating account...
                  </span>
                ) : (
                  'Create Account'
                )}
              </button>
            </form>

            <p className="mt-6 text-center text-sm" style={{ color: '#8B949E' }}>
              Already have an account?{' '}
              <Link to="/login" className="font-medium hover:underline" style={{ color: '#00D4AA' }}>
                Log in
              </Link>
            </p>
          </motion.div>
        </div>
      </section>
    </PageLayout>
  )
}
