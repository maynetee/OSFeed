import { useMemo } from 'react'
import { useLocation } from 'react-router-dom'
import { Command, Menu } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/layout/theme-toggle'
import { useUiStore } from '@/stores/ui-store'

const titleMap: Record<string, string> = {
  '/': 'Dashboard',
  '/feed': 'Live Feed',
  '/search': 'Search & Signal',
  '/digests': 'Daily Digests',
  '/channels': 'Channels',
  '/collections': 'Collections',
  '/exports': 'Exports',
  '/settings': 'Settings',
}

export function Header() {
  const location = useLocation()
  const toggleSidebar = useUiStore((state) => state.toggleSidebar)
  const setCommandPaletteOpen = useUiStore((state) => state.setCommandPaletteOpen)

  const title = useMemo(() => {
    if (location.pathname.startsWith('/digests/')) return 'Digest'
    if (location.pathname.startsWith('/channels/')) return 'Channel'
    if (location.pathname.startsWith('/collections/')) return 'Collection'
    return titleMap[location.pathname] ?? 'TeleScope'
  }, [location.pathname])

  return (
    <header className="flex items-center justify-between border-b border-border/70 bg-background/70 px-6 py-4 backdrop-blur">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={toggleSidebar} aria-label="Toggle sidebar">
          <Menu className="h-4 w-4" />
        </Button>
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-foreground/40">Workspace</p>
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          className="hidden items-center gap-2 md:flex"
          onClick={() => setCommandPaletteOpen(true)}
        >
          <Command className="h-4 w-4" />
          Command Palette
        </Button>
        <ThemeToggle />
      </div>
    </header>
  )
}
