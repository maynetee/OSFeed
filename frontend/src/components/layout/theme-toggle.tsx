import { Moon, SunMedium, Monitor } from 'lucide-react'
import { useTranslation } from 'react-i18next'

import { Button } from '@/components/ui/button'
import { useUiStore, type ThemeMode } from '@/stores/ui-store'

export function ThemeToggle() {
  const theme = useUiStore((state) => state.theme)
  const setTheme = useUiStore((state) => state.setTheme)
  const { t } = useTranslation()

  const themeOptions: { value: ThemeMode; icon: typeof SunMedium; label: string }[] = [
    { value: 'light', icon: SunMedium, label: t('theme.light') },
    { value: 'dark', icon: Moon, label: t('theme.dark') },
    { value: 'system', icon: Monitor, label: t('theme.system') },
  ]

  return (
    <div className="flex items-center gap-1 rounded-full border border-border/60 bg-background/80 p-1">
      {themeOptions.map((option) => {
        const Icon = option.icon
        const isActive = theme === option.value
        return (
          <Button
            key={option.value}
            variant={isActive ? 'default' : 'ghost'}
            size="icon"
            className={isActive ? 'h-8 w-8' : 'h-8 w-8 text-foreground/60'}
            onClick={() => setTheme(option.value)}
            aria-label={option.label}
          >
            <Icon className="h-4 w-4" />
          </Button>
        )
      })}
    </div>
  )
}
