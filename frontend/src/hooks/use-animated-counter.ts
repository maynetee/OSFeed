import { useEffect, useRef, useState } from 'react'

export function useAnimatedCounter(target: number, duration = 1500) {
  const [count, setCount] = useState(0)
  const startTime = useRef<number | null>(null)
  const prevTarget = useRef(0)

  useEffect(() => {
    if (target === 0) {
      setCount(0)
      return
    }
    const from = prevTarget.current
    prevTarget.current = target
    startTime.current = null

    let animationId: number
    const animate = (timestamp: number) => {
      if (!startTime.current) startTime.current = timestamp
      const elapsed = timestamp - startTime.current
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setCount(Math.floor(from + eased * (target - from)))
      if (progress < 1) {
        animationId = requestAnimationFrame(animate)
      }
    }
    animationId = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(animationId)
  }, [target, duration])

  return count
}
