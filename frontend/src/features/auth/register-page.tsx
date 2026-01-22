import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AxiosError } from 'axios'
import { Bot, Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useUserStore } from '@/stores/user-store'
import { authApi } from '@/lib/api/client'

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords do not match",
  path: ["confirmPassword"],
})

type RegisterFormValues = z.infer<typeof registerSchema>

const getErrorMessage = (detail: string | undefined): string => {
  switch (detail) {
    case 'REGISTER_USER_ALREADY_EXISTS':
      return 'An account with this email already exists'
    case 'REGISTER_INVALID_PASSWORD':
      return 'Password is too weak. Use at least 8 characters with letters and numbers'
    case 'LOGIN_BAD_CREDENTIALS':
      return 'Invalid email or password'
    case 'LOGIN_USER_NOT_VERIFIED':
      return 'Please verify your email before logging in'
    default:
      return detail || 'Registration failed. Please try again.'
  }
}

export function RegisterPage() {
  const navigate = useNavigate()
  const { setUser, setTokens } = useUserStore()
  const { t } = useTranslation()
  const [error, setError] = useState<string | null>(null)

  const form = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: '', password: '', confirmPassword: '' },
  })

  const handleRegister = async (values: RegisterFormValues) => {
    setError(null)
    try {
      // First, create the account
      await authApi.register(values.email, values.password)

      // Then, login to get the tokens
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

      navigate('/dashboard')
    } catch (err) {
      const axiosError = err as AxiosError<{ detail: string }>
      setError(getErrorMessage(axiosError.response?.data?.detail))
    }
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
