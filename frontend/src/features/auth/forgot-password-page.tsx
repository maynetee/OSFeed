import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Bot, Loader2, CheckCircle2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { authApi } from '@/lib/api/client'

const forgotPasswordSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
})

type ForgotPasswordFormValues = z.infer<typeof forgotPasswordSchema>

export function ForgotPasswordPage() {
  const { t } = useTranslation()
  const [isSuccess, setIsSuccess] = useState(false)

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
  })

  const handleSubmit = async (values: ForgotPasswordFormValues) => {
    try {
      // Call the forgot password API (will be added in T8)
      await authApi.forgotPassword(values.email)

      // Always show success message for security (don't reveal if email exists)
      setIsSuccess(true)
    } catch (err) {
      // Even on error, show success message to prevent email enumeration
      setIsSuccess(true)
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
          <CardTitle className="text-2xl font-bold text-center">
            {t('auth.forgotPasswordTitle', 'Reset Password')}
          </CardTitle>
          <CardDescription className="text-center">
            {t('auth.forgotPasswordDescription', 'Enter your email address and we will send you a password reset link')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isSuccess ? (
            <div className="rounded-md bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-900 p-4">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-green-800 dark:text-green-300">
                    {t('auth.forgotPasswordSuccessTitle', 'Check your email')}
                  </h3>
                  <p className="mt-1 text-sm text-green-700 dark:text-green-400">
                    {t('auth.forgotPasswordSuccessMessage',
                      'If an account exists with this email, you will receive a password reset link shortly.')}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <form className="space-y-4" onSubmit={form.handleSubmit(handleSubmit)}>
              <div className="space-y-2">
                <Label htmlFor="email">{t('auth.email', 'Email')}</Label>
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
              <Button
                type="submit"
                className="w-full h-10"
                disabled={form.formState.isSubmitting}
              >
                {form.formState.isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t('auth.sendingResetLink', 'Sending...')}
                  </>
                ) : (
                  t('auth.sendResetLink', 'Send Reset Link')
                )}
              </Button>
            </form>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-2 border-t bg-muted/5 py-4">
          <p className="text-xs text-center text-muted-foreground">
            {t('auth.rememberPassword', 'Remember your password?')}{' '}
            <Link to="/login" className="text-primary font-medium hover:underline">
              {t('auth.backToLogin', 'Back to login')}
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
