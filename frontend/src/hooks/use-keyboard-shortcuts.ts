import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

import { useUiStore } from '@/stores/ui-store'

export function useKeyboardShortcuts() {
  const navigate = useNavigate()
  const toggleCommandPalette = useUiStore((state) => state.toggleCommandPalette)

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (!(event.metaKey || event.ctrlKey)) return

      const key = event.key.toLowerCase()
      if (key === 'k') {
        event.preventDefault()
        toggleCommandPalette()
        return
      }

      if (key === 'h') {
        event.preventDefault()
        navigate('/')
      }

      if (key === 'f') {
        event.preventDefault()
        navigate('/feed')
      }

      if (key === '/') {
        event.preventDefault()
        navigate('/search')
      }

      if (key === 'd') {
        event.preventDefault()
        navigate('/digests')
      }

      if (key === 'e') {
        event.preventDefault()
        navigate('/exports')
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [navigate, toggleCommandPalette])
}
