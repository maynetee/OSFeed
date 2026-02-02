import { useMemo, useRef, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { Menu, LogOut } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/layout/theme-toggle'
import { useUiStore } from '@/stores/ui-store'
import { useUserStore } from '@/stores/user-store'
import { NotificationCenter } from '@/components/layout/notification-center'
import { authApi } from '@/lib/api/client'
import { useMobile } from '@/hooks/use-mobile'

export function Header() {
  const location = useLocation()
  const toggleSidebar = useUiStore((state) => state.toggleSidebar)
  const toggleMobileDrawer = useUiStore((state) => state.toggleMobileDrawer)
  const mobileDrawerOpen = useUiStore((state) => state.mobileDrawerOpen)
  const setMenuButtonElement = useUiStore((state) => state.setMenuButtonElement)
  const logout = useUserStore((state) => state.logout)
  const { t } = useTranslation()
  const isMobile = useMobile()
  const menuButtonRef = useRef<HTMLButtonElement>(null)

  // Register menu button element for focus restoration
  useEffect(() => {
    if (isMobile && menuButtonRef.current) {
      setMenuButtonElement(menuButtonRef.current)
    }
    return () => {
      if (isMobile) {
        setMenuButtonElement(null)
      }
    }
  }, [isMobile, setMenuButtonElement])

  const handleLogout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error('Logout failed:', error)
    } finally {
      logout()
    }
  }

  const title = useMemo(() => {
    if (location.pathname.startsWith('/digests/')) return t('digests.title')
    if (location.pathname.startsWith('/channels/')) return t('channels.title')
    if (location.pathname.startsWith('/collections/')) return t('collections.title')
    if (location.pathname === '/') return t('navigation.dashboard')
    if (location.pathname === '/feed') return t('navigation.feed')
    if (location.pathname === '/search') return t('navigation.search')
    if (location.pathname === '/digests') return t('navigation.digests')
    if (location.pathname === '/channels') return t('navigation.channels')
    if (location.pathname === '/collections') return t('navigation.collections')
    if (location.pathname === '/exports') return t('navigation.exports')
    if (location.pathname === '/settings') return t('navigation.settings')
    return 'OSFeed'
  }, [location.pathname, t])

  return (
    <header className="flex items-center justify-between border-b border-border/70 bg-background/70 px-6 py-4 backdrop-blur">
      <div className="flex items-center gap-4">
        <Button
          ref={menuButtonRef}
          variant="ghost"
          size="icon"
          onClick={isMobile ? toggleMobileDrawer : toggleSidebar}
          aria-label={t('header.toggleSidebar')}
          aria-expanded={isMobile ? mobileDrawerOpen : undefined}
        >
          <Menu className="h-4 w-4" />
        </Button>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-foreground/40">
            {t('header.workspace')}
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <NotificationCenter />
        <Button
          variant="outline"
          size="icon"
          onClick={handleLogout}
          aria-label={t('auth.signOut')}
          title={t('auth.signOut')}
        >
          <LogOut className="h-4 w-4" />
        </Button>
        <ThemeToggle />
      </div>
    </header>
  )
}
