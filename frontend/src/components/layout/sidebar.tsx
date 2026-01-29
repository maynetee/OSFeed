import { NavLink } from 'react-router-dom'
import {
  Layers,
  Newspaper,
  Radio,
  Search,
  Settings,
  Sparkles,
} from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'

import { cn } from '@/lib/cn'
import { useUiStore } from '@/stores/ui-store'
import { statsApi } from '@/lib/api/client'

const navItems = [
  { key: 'feed', to: '/feed', icon: Radio },
  { key: 'search', to: '/search', icon: Search },
  { key: 'channels', to: '/channels', icon: Newspaper },
  { key: 'collections', to: '/collections', icon: Layers },
  { key: 'exports', to: '/exports', icon: Sparkles },
  { key: 'settings', to: '/settings', icon: Settings },
]

export function Sidebar() {
  const collapsed = useUiStore((state) => state.sidebarCollapsed)
  const { t } = useTranslation()

  const { data: stats } = useQuery({
    queryKey: ['stats', 'overview'],
    queryFn: async () => (await statsApi.overview()).data,
    staleTime: 60000, // 1 minute
  })

  const statusMessages = stats?.messages_last_24h ?? 0
  const statusDuplicates = stats?.duplicates_last_24h && stats?.messages_last_24h
    ? Math.round((stats.duplicates_last_24h / stats.messages_last_24h) * 100)
    : 0

  return (
    <aside
      className={cn(
        'flex h-full flex-col border-r border-sidebar-border bg-sidebar-bg px-4 py-6',
        collapsed ? 'w-20' : 'w-64',
      )}
    >
      <div className={cn('flex items-center gap-3 px-2', collapsed && 'justify-center')}>
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
          <span className="text-lg font-semibold">O</span>
        </div>
        {!collapsed && (
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-foreground-muted">
              OSFeed
            </p>
            <p className="text-xs text-foreground-muted">{t('branding.tagline')}</p>
          </div>
        )}
      </div>

      <nav className="mt-10 flex flex-1 flex-col gap-1">
        {navItems.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary/15 text-primary'
                    : 'text-foreground-muted hover:bg-muted hover:text-foreground',
                  collapsed && 'justify-center px-2',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {!collapsed && <span>{t(`navigation.${item.key}`)}</span>}
            </NavLink>
          )
        })}
      </nav>

      <div className={cn('mt-auto rounded-xl border border-border bg-card p-4', collapsed && 'p-3')}>
        <p className={cn('text-xs font-semibold uppercase tracking-wide text-foreground-muted', collapsed && 'text-center')}>
          {t('sidebar.status')}
        </p>
        {!collapsed && (
          <p className="mt-2 text-xs text-foreground-muted">
            {t('sidebar.statusSummary', {
              duplicates: statusDuplicates,
              messages: statusMessages.toLocaleString(),
            })}
          </p>
        )}
      </div>
    </aside>
  )
}
