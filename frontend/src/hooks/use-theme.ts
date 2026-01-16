import { useEffect } from 'react'

import { useUiStore } from '@/stores/ui-store'

const prefersDark = () =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches

export function useTheme() {
  const theme = useUiStore((state) => state.theme)

  useEffect(() => {
    const root = document.documentElement
    const resolvedTheme = theme === 'system' ? (prefersDark() ? 'dark' : 'light') : theme

    root.classList.remove('light', 'dark')
    root.classList.add(resolvedTheme)
  }, [theme])

  useEffect(() => {
    if (theme !== 'system') return
    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => {
      const root = document.documentElement
      root.classList.toggle('dark', media.matches)
      root.classList.toggle('light', !media.matches)
    }
    media.addEventListener('change', handler)
    return () => media.removeEventListener('change', handler)
  }, [theme])

  return theme
}
