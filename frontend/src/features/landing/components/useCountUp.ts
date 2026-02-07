import { useState, useEffect, useRef } from 'react'

interface UseCountUpOptions {
  end: number
  duration?: number
  start?: number
  separator?: string
  startOnMount?: boolean
}

export function useCountUp({
  end,
  duration = 2000,
  start = 0,
  separator = ',',
  startOnMount = true,
}: UseCountUpOptions) {
  const [count, setCount] = useState(start)
  const [isComplete, setIsComplete] = useState(false)
  const rafRef = useRef<number>()
  const startTimeRef = useRef<number>()

  const startCounting = () => {
    setIsComplete(false)
    startTimeRef.current = undefined

    const animate = (timestamp: number) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp
      const progress = Math.min((timestamp - startTimeRef.current) / duration, 1)

      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = Math.floor(start + (end - start) * eased)

      setCount(current)

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(animate)
      } else {
        setIsComplete(true)
      }
    }

    rafRef.current = requestAnimationFrame(animate)
  }

  useEffect(() => {
    if (startOnMount) {
      startCounting()
    }
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const formattedCount = count.toString().replace(/\B(?=(\d{3})+(?!\d))/g, separator)

  return { count, formattedCount, isComplete, startCounting }
}
