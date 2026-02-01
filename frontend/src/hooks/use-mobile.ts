import { useEffect, useState } from 'react'

const isMobileViewport = () =>
  typeof window !== 'undefined' && window.matchMedia('(max-width: 767px)').matches

export function useMobile() {
  const [isMobile, setIsMobile] = useState(isMobileViewport())

  useEffect(() => {
    const media = window.matchMedia('(max-width: 767px)')
    const handler = () => {
      setIsMobile(media.matches)
    }
    media.addEventListener('change', handler)
    return () => media.removeEventListener('change', handler)
  }, [])

  return isMobile
}
