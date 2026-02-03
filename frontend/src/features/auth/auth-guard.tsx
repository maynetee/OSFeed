import { Navigate, Outlet } from 'react-router-dom'
import { useTranslation } from 'react-i18next'

import { useUserStore } from '@/stores/user-store'

export function AuthGuard() {
  const { t } = useTranslation()
  const user = useUserStore((state) => state.user)
  const hasHydrated = useUserStore((state) => state._hasHydrated)

  // Wait for store hydration before checking auth
  if (!hasHydrated) {
    return <div className="flex h-screen items-center justify-center text-foreground/60">{t('common.loading')}</div>
  }

  // Require authentication - check for user (tokens are in httpOnly cookies)
  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
