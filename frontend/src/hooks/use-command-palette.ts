import { useMemo, type ComponentType } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, LayoutDashboard, Radio, BookOpenText, Layers, Settings, Sparkles } from 'lucide-react'
import { useTranslation } from 'react-i18next'

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
  const { t } = useTranslation()

  const commands = useMemo<CommandItem[]>(
    () => [
      {
        id: 'nav-dashboard',
        label: t('navigation.dashboard'),
        shortcut: 'Cmd H',
        icon: LayoutDashboard,
        action: () => navigate('/'),
        keywords: t('commandPalette.keywords.dashboard'),
      },
      {
        id: 'nav-feed',
        label: t('navigation.feed'),
        shortcut: 'Cmd F',
        icon: Radio,
        action: () => navigate('/feed'),
        keywords: t('commandPalette.keywords.feed'),
      },
      {
        id: 'nav-search',
        label: t('navigation.search'),
        shortcut: 'Cmd /',
        icon: Search,
        action: () => navigate('/search'),
        keywords: t('commandPalette.keywords.search'),
      },
      {
        id: 'nav-digests',
        label: t('digests.title'),
        shortcut: 'Cmd D',
        icon: BookOpenText,
        action: () => navigate('/digests'),
        keywords: t('commandPalette.keywords.digests'),
      },
      {
        id: 'nav-collections',
        label: t('navigation.collections'),
        shortcut: 'Cmd C',
        icon: Layers,
        action: () => navigate('/collections'),
        keywords: t('commandPalette.keywords.collections'),
      },
      {
        id: 'nav-exports',
        label: t('navigation.exports'),
        shortcut: 'Cmd E',
        icon: Sparkles,
        action: () => navigate('/exports'),
        keywords: t('commandPalette.keywords.exports'),
      },
      {
        id: 'nav-settings',
        label: t('navigation.settings'),
        shortcut: 'Cmd ,',
        icon: Settings,
        action: () => navigate('/settings'),
        keywords: t('commandPalette.keywords.settings'),
      },
    ],
    [navigate, t],
  )

  const handleSelect = (command: CommandItem) => {
    command.action()
    setCommandPaletteOpen(false)
  }

  return { commands, handleSelect }
}
