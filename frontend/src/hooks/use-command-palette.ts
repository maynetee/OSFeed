import { useMemo, type ComponentType } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, LayoutDashboard, Radio, BookOpenText, Layers, Settings, Sparkles } from 'lucide-react'

import { useUiStore } from '@/stores/ui-store'

export interface CommandItem {
  id: string
  label: string
  shortcut?: string
  icon?: ComponentType<{ className?: string }>
  action: () => void
  keywords?: string
}

export function useCommandPalette() {
  const navigate = useNavigate()
  const setCommandPaletteOpen = useUiStore((state) => state.setCommandPaletteOpen)

  const commands = useMemo<CommandItem[]>(
    () => [
      {
        id: 'nav-dashboard',
        label: 'Dashboard',
        shortcut: 'Cmd H',
        icon: LayoutDashboard,
        action: () => navigate('/'),
        keywords: 'home overview metrics',
      },
      {
        id: 'nav-feed',
        label: 'Feed',
        shortcut: 'Cmd F',
        icon: Radio,
        action: () => navigate('/feed'),
        keywords: 'messages live',
      },
      {
        id: 'nav-search',
        label: 'Search',
        shortcut: 'Cmd /',
        icon: Search,
        action: () => navigate('/search'),
        keywords: 'query explore',
      },
      {
        id: 'nav-digests',
        label: 'Daily Digest',
        shortcut: 'Cmd D',
        icon: BookOpenText,
        action: () => navigate('/digests'),
        keywords: 'summary brief',
      },
      {
        id: 'nav-collections',
        label: 'Collections',
        shortcut: 'Cmd C',
        icon: Layers,
        action: () => navigate('/collections'),
        keywords: 'themes',
      },
      {
        id: 'nav-exports',
        label: 'Exports',
        shortcut: 'Cmd E',
        icon: Sparkles,
        action: () => navigate('/exports'),
        keywords: 'export pdf csv',
      },
      {
        id: 'nav-settings',
        label: 'Settings',
        shortcut: 'Cmd ,',
        icon: Settings,
        action: () => navigate('/settings'),
        keywords: 'preferences',
      },
    ],
    [navigate],
  )

  const handleSelect = (command: CommandItem) => {
    command.action()
    setCommandPaletteOpen(false)
  }

  return { commands, handleSelect }
}
