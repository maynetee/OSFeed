import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'

export function useKeyboardShortcuts() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if (!(event.metaKey || event.ctrlKey)) return

      const key = event.key.toLowerCase()

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

      if (key === 'e') {
        event.preventDefault()
        navigate('/exports')
      }

      if (key === 'r') {
        event.preventDefault()
        queryClient.invalidateQueries()
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [navigate, queryClient])
}
