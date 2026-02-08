import { useEffect, useRef, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { api } from '@/lib/api/axios-instance'
import { useUserStore } from '@/stores/user-store'

export function AuthGuard() {
  const { t } = useTranslation()
  const user = useUserStore((state) => state.user)
  const logout = useUserStore((state) => state.logout)
  const hasHydrated = useUserStore((state) => state._hasHydrated)

  const [isValidating, setIsValidating] = useState(false)
  const [isValidated, setIsValidated] = useState(false)
  const validationAttempted = useRef(false)

  useEffect(() => {
    if (!hasHydrated || !user || validationAttempted.current) return

    validationAttempted.current = true
    setIsValidating(true)

    api.post('/api/auth/refresh')
      .then(() => {
        setIsValidated(true)
      })
      .catch(() => {
        logout()
      })
      .finally(() => {
        setIsValidating(false)
      })
  }, [hasHydrated, user, logout])

  // Wait for store hydration before checking auth
  if (!hasHydrated) {
    return (
      <div className="flex h-screen items-center justify-center text-foreground/60">
        {t('common.loading')}
      </div>
    )
  }

  // No user after hydration — redirect to login
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // Validating session with server
  if (isValidating || !isValidated) {
    return (
      <div className="flex h-screen items-center justify-center text-foreground/60">
        {t('common.loading')}
      </div>
    )
  }

  return <Outlet />
}
