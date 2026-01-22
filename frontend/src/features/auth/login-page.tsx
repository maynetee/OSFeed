import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
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
  const { setUser, setTokens } = useUserStore()
  const { t } = useTranslation()
  const [error, setError] = useState<string | null>(null)

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const handleLogin = async (values: LoginFormValues) => {
    setError(null)
    try {
      const response = await authApi.login(values.email, values.password)
      const { access_token, refresh_token, refresh_expires_at } = response.data

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
          <CardTitle className="text-2xl font-bold text-center">{t('auth.loginTitle')}</CardTitle>
          <CardDescription className="text-center">
            {t('auth.loginDescription')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium border border-destructive/20">
              {error}
            </div>
          )}
          <form className="space-y-4" onSubmit={form.handleSubmit(handleLogin)}>
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
              <div className="flex items-center justify-between">
                <Label htmlFor="password">{t('auth.password')}</Label>
                <a href="#" className="text-xs text-muted-foreground hover:text-primary transition-colors">
                  Forgot password?
                </a>
              </div>
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
            <Button
              type="submit"
              className="w-full h-10"
              disabled={form.formState.isSubmitting}
            >
              {form.formState.isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('auth.signingIn')}
                </>
              ) : (
                t('auth.signIn')
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col gap-2 border-t bg-muted/5 py-4">
          <p className="text-xs text-center text-muted-foreground">
            Don&apos;t have an account?{' '}
            <Link to="/register" className="text-primary font-medium hover:underline">
              {t('auth.createAccount')}
            </Link>
          </p>
        </CardFooter>
      </Card>

      <p className="mt-8 text-center text-xs text-muted-foreground">
        &copy; {new Date().getFullYear()} OSFeed Inc. All rights reserved.
      </p>
    </div>
  )
}
