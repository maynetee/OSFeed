import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { AxiosError } from 'axios'
import { Bot, Loader2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { authApi } from '@/lib/api/client'

const resetPasswordSchema = z
  .object({
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type ResetPasswordFormValues = z.infer<typeof resetPasswordSchema>

const getErrorMessage = (detail: string | undefined): string => {
  switch (detail) {
    case 'RESET_PASSWORD_BAD_TOKEN':
      return 'Invalid or expired reset token. Please request a new password reset.'
    case 'RESET_PASSWORD_INVALID_PASSWORD':
      return 'Password is too weak. Use at least 8 characters with letters and numbers'
    default:
      return detail || 'Password reset failed. Please try again.'
  }
}

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [searchParams] = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  const [tokenError, setTokenError] = useState<string | null>(null)

  const token = searchParams.get('token')

  useEffect(() => {
    if (!token) {
      setTokenError('No reset token found. Please use the link from your email.')
    }
  }, [token])

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { password: '', confirmPassword: '' },
  })

  const handleResetPassword = async (values: ResetPasswordFormValues) => {
    if (!token) {
      setError('No reset token found')
      return
    }

    setError(null)
    try {
      await authApi.resetPassword(token, values.password)

      navigate('/login', {
        state: {
          message: 'Password reset successful! You can now log in with your new password.',
        },
      })
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
          <CardTitle className="text-2xl font-bold text-center">Reset Password</CardTitle>
          <CardDescription className="text-center">Enter your new password below</CardDescription>
        </CardHeader>
        <CardContent>
          {tokenError && (
            <div className="mb-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium border border-destructive/20">
              {tokenError}
              <div className="mt-2">
                <Link to="/login" className="text-primary hover:underline">
                  Return to login
                </Link>
              </div>
            </div>
          )}
          {error && (
            <div className="mb-4 rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium border border-destructive/20">
              {error}
            </div>
          )}
          {!tokenError && (
            <form className="space-y-4" onSubmit={form.handleSubmit(handleResetPassword)}>
              <div className="space-y-2">
                <Label htmlFor="password">New Password</Label>
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
                    {form.formState.errors.confirmPassword.message}
                  </span>
                )}
              </div>
              <Button type="submit" className="w-full h-10" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Resetting password...
                  </>
                ) : (
                  'Reset Password'
                )}
              </Button>
            </form>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-2 border-t bg-muted/5 py-4">
          <p className="text-xs text-center text-muted-foreground">
            Remember your password?{' '}
            <Link to="/login" className="text-primary font-medium hover:underline">
              {t('auth.signIn')}
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
