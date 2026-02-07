import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { AxiosError } from 'axios'
import { Bot, Loader2, CheckCircle2, XCircle } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { authApi } from '@/lib/api/client'

type VerificationState = 'verifying' | 'success' | 'error'

export function VerifyEmailPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [state, setState] = useState<VerificationState>('verifying')
  const [errorMessage, setErrorMessage] = useState<string>('')

  useEffect(() => {
    const token = searchParams.get('token')

    if (!token) {
      setState('error')
      setErrorMessage('No verification token provided')
      return
    }

    const verifyEmail = async () => {
      try {
        await authApi.verifyEmail(token)
        setState('success')
      } catch (err) {
        const axiosError = err as AxiosError<{ detail: string }>
        setState('error')
        setErrorMessage(
          axiosError.response?.data?.detail ||
          'Verification failed. The token may be invalid or expired.'
        )
      }
    }

    verifyEmail()
  }, [searchParams])

  const handleRequestNewVerification = () => {
    navigate('/signup')
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
            Email Verification
          </CardTitle>
          <CardDescription className="text-center">
            {state === 'verifying' && 'Verifying your email address...'}
            {state === 'success' && 'Your email has been verified'}
            {state === 'error' && 'Verification failed'}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center space-y-6 py-8">
          {state === 'verifying' && (
            <div className="flex flex-col items-center space-y-4">
              <Loader2 className="h-16 w-16 animate-spin text-primary" />
              <p className="text-sm text-muted-foreground">
                Please wait while we verify your email address
              </p>
            </div>
          )}

          {state === 'success' && (
            <div className="flex flex-col items-center space-y-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/20">
                <CheckCircle2 className="h-10 w-10 text-green-600 dark:text-green-500" />
              </div>
              <div className="text-center space-y-2">
                <p className="text-base font-medium">
                  Your email has been verified successfully!
                </p>
                <p className="text-sm text-muted-foreground">
                  You can now log in to your account
                </p>
              </div>
              <Button
                onClick={() => navigate('/login')}
                className="w-full mt-4"
              >
                Go to Login
              </Button>
            </div>
          )}

          {state === 'error' && (
            <div className="flex flex-col items-center space-y-4 w-full">
              <div className="flex h-16 w-16 items-center justify-center rounded-full bg-destructive/15">
                <XCircle className="h-10 w-10 text-destructive" />
              </div>
              <div className="text-center space-y-2">
                <p className="text-base font-medium text-destructive">
                  Verification Failed
                </p>
                <p className="text-sm text-muted-foreground">
                  {errorMessage}
                </p>
              </div>
              <div className="w-full space-y-2 mt-4">
                <Button
                  onClick={handleRequestNewVerification}
                  variant="default"
                  className="w-full"
                >
                  Request New Verification
                </Button>
                <Button
                  onClick={() => navigate('/login')}
                  variant="outline"
                  className="w-full"
                >
                  Back to Login
                </Button>
              </div>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex flex-col gap-2 border-t bg-muted/5 py-4">
          <p className="text-xs text-center text-muted-foreground">
            Need help?{' '}
            <Link to="/support" className="text-primary font-medium hover:underline">
              Contact Support
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
