import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AxiosError } from 'axios'
import { Bot, Loader2, Check, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useUserStore } from '@/stores/user-store'
import { authApi } from '@/lib/api/client'

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string()
    .min(8, "Password must be at least 8 characters long")
    .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
    .regex(/[a-z]/, "Password must contain at least one lowercase letter")
    .regex(/\d/, "Password must contain at least one digit")
    .regex(/[!@#$%^&*(),.?":{}|<>]/, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
})

type RegisterFormValues = z.infer<typeof registerSchema>

const getErrorMessage = (detail: string | { code: string; reason: string } | undefined): string => {
  // Handle object-shaped error details (e.g. REGISTER_INVALID_PASSWORD returns {code, reason})
  if (typeof detail === 'object' && detail !== null) {
    switch (detail.code) {
      case 'REGISTER_INVALID_PASSWORD':
        return detail.reason || 'Password is too weak. Use at least 8 characters with letters and numbers'
      default:
        return detail.reason || 'Registration failed. Please try again.'
    }
  }

  switch (detail) {
    case 'REGISTER_USER_ALREADY_EXISTS':
      return 'An account with this email already exists'
    case 'REGISTER_INVALID_PASSWORD':
      return 'Password is too weak. Use at least 8 characters with letters and numbers'
    case 'REGISTER_UNEXPECTED_ERROR':
      return 'An unexpected error occurred. Please try again later.'
    case 'LOGIN_BAD_CREDENTIALS':
      return 'Invalid email or password'
    case 'LOGIN_USER_NOT_VERIFIED':
      return 'Please verify your email before logging in'
    default:
      return typeof detail === 'string' && detail ? detail : 'Registration failed. Please try again.'
  }
}

export function RegisterPage() {
  const navigate = useNavigate()
  const { setUser, setTokens } = useUserStore()
  const { t } = useTranslation()
  const [error, setError] = useState<string | null>(null)
  const [registrationSuccess, setRegistrationSuccess] = useState(false)
  const [registeredEmail, setRegisteredEmail] = useState('')
  const [resendSent, setResendSent] = useState(false)

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: '', password: '', confirmPassword: '' },
  })

  const password = form.watch('password')

  // Password requirement checks
  const requirements = [
    { label: 'At least 8 characters', met: (password?.length || 0) >= 8 },
    { label: 'One uppercase letter', met: /[A-Z]/.test(password || '') },
    { label: 'One lowercase letter', met: /[a-z]/.test(password || '') },
    { label: 'One number', met: /\d/.test(password || '') },
    { label: 'One special character', met: /[!@#$%^&*(),.?":{}|<>]/.test(password || '') },
  ]

  const handleRegister = async (values: RegisterFormValues) => {
    setError(null)
    try {
      // Create the account
      const response = await authApi.register(values.email, values.password)

      // Check if email verification is required (is_verified will be false)
      if (response.data.is_verified === false) {
        // Email verification required - show success message, DON'T auto-login
        setRegisteredEmail(values.email)
        setRegistrationSuccess(true)
      } else {
        // No email verification (email_enabled=false or already verified) - auto-login
        const loginResponse = await authApi.login(values.email, values.password)
        const { access_token, refresh_token, refresh_expires_at } = loginResponse.data

        setTokens({
          accessToken: access_token,
          refreshToken: refresh_token,
          refreshExpiresAt: refresh_expires_at,
        })

        // Fetch user profile
        const userResponse = await authApi.me()
        setUser({
          id: userResponse.data.id,
          email: userResponse.data.email,
          name: userResponse.data.email.split('@')[0],
        })

        navigate('/feed')
      }
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string | { code: string; reason: string } }>
      setError(getErrorMessage(axiosError.response?.data?.detail))
    }
  }

  const handleResendVerification = async () => {
    if (!registeredEmail) return
    try {
      await authApi.requestVerification(registeredEmail)
      setResendSent(true)
    } catch {
      // Silently fail - don't reveal if email exists
      setResendSent(true)
    }
  }

  if (registrationSuccess) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30 px-4 py-8 sm:px-6 lg:px-8">
        <div className="flex items-center gap-2 mb-8">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
            <Bot className="h-6 w-6" />
          </div>
          <span className="text-2xl font-bold tracking-tight">OSFeed</span>
        </div>

        <Card className="w-full max-w-sm sm:max-w-md shadow-lg border-muted">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">Check your email</CardTitle>
            <CardDescription className="text-center">
              We've sent a verification link to your email address
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-muted-foreground mb-4">
              Please click the link in the email to verify your account and complete registration.
            </p>
            {resendSent ? (
              <p className="text-sm text-muted-foreground">
                A new verification email has been sent. Please check your inbox.
              </p>
            ) : (
              <p className="text-sm text-muted-foreground">
                Didn't receive the email? Check your spam folder or{' '}
                <button type="button" className="text-primary font-medium hover:underline" onClick={handleResendVerification}>
                  request a new link
                </button>
              </p>
            )}
          </CardContent>
          <CardFooter className="justify-center border-t bg-muted/5 py-4">
            <Link to="/login" className="text-primary font-medium hover:underline">
              Back to login
            </Link>
          </CardFooter>
        </Card>

        <p className="mt-8 text-center text-xs text-muted-foreground">
          &copy; {new Date().getFullYear()} OSFeed Inc. All rights reserved.
        </p>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-muted/30 px-4 py-8 sm:px-6 lg:px-8">
      <div className="flex items-center gap-2 mb-8">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <Bot className="h-6 w-6" />
        </div>
        <span className="text-2xl font-bold tracking-tight">OSFeed</span>
      </div>

      <Card className="w-full max-w-sm sm:max-w-md shadow-lg border-muted">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">{t('auth.createAccountTitle')}</CardTitle>
          <CardDescription className="text-center">
            {t('auth.createAccountDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium border border-destructive/20">
              {error}
            </div>
          )}
          <form className="space-y-4" onSubmit={form.handleSubmit(handleRegister)}>
            <div className="space-y-2">
              <Label htmlFor="email">{t('auth.email')}</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                className="h-10"
                {...form.register('email')}
              />
              {form.formState.errors.email && (
                <span className="text-xs text-destructive font-medium">
                  {form.formState.errors.email.message}
                </span>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">{t('auth.password')}</Label>
              <Input
                id="password"
                type="password"
                className="h-10"
                {...form.register('password')}
              />
              {form.formState.errors.password && (
                <span className="text-xs text-destructive font-medium">
                  {form.formState.errors.password.message}
                </span>
              )}
              <div className="mt-3 space-y-2">
                <p className="text-xs font-medium text-muted-foreground">Password requirements:</p>
                <ul className="space-y-1.5">
                  {requirements.map((req, index) => (
                    <li key={index} className="flex items-center gap-2 text-xs">
                      {req.met ? (
                        <Check className="h-4 w-4 text-green-600" />
                      ) : (
                        <X className="h-4 w-4 text-muted-foreground/40" />
                      )}
                      <span className={req.met ? 'text-green-600 font-medium' : 'text-muted-foreground'}>
                        {req.label}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                className="h-10"
                {...form.register('confirmPassword')}
              />
              {form.formState.errors.confirmPassword && (
                <span className="text-xs text-destructive font-medium">
                  {t('auth.passwordsDoNotMatch')}
                </span>
              )}
            </div>
            <Button
              type="submit"
              className="w-full h-10"
              disabled={form.formState.isSubmitting}
            >
              {form.formState.isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('auth.signingUp')}
                </>
              ) : (
                t('auth.signUp')
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-2 border-t bg-muted/5 py-4">
          <p className="text-xs text-center text-muted-foreground">
            {t('auth.alreadyHaveAccount')}
          </p>
        </CardFooter>
      </Card>

      <p className="mt-8 text-center text-xs text-muted-foreground">
        &copy; {new Date().getFullYear()} OSFeed Inc. All rights reserved.
      </p>
    </div>
  )
}
