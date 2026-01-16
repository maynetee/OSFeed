import { Navigate, Outlet } from 'react-router-dom'

import { useUserStore } from '@/stores/user-store'

export function AuthGuard() {
  const user = useUserStore((state) => state.user)

  if (!user && !import.meta.env.DEV) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
