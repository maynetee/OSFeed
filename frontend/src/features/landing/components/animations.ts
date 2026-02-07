import { Variants } from 'framer-motion'

// Fade in + slide up (for sections entering viewport)
export const fadeInUp: Variants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } }
}

// Fade in only
export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.6, ease: 'easeOut' } }
}

// Slide in from right (for mockups)
export const slideInRight: Variants = {
  hidden: { opacity: 0, x: 40 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }
}

// Slide in from left
export const slideInLeft: Variants = {
  hidden: { opacity: 0, x: -40 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }
}

// Stagger container (for card grids)
export const staggerContainer: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1
    }
  }
}

// Individual stagger item
export const staggerItem: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' } }
}

// Hero-specific staggered animations
export const heroStagger = {
  badge: { delay: 0 },
  headline: { delay: 0.2 },
  subheadline: { delay: 0.4 },
  ctas: { delay: 0.6 },
  mockup: { delay: 0.3 }
}

// Viewport config for whileInView
export const viewportConfig = {
  once: true,
  amount: 0.2
} as const

// Hover animation for cards
export const cardHover = {
  scale: 1.02,
  transition: { duration: 0.3, ease: 'easeOut' }
}

// Tab content crossfade
export const tabCrossfade: Variants = {
  enter: { opacity: 0, x: 20 },
  center: { opacity: 1, x: 0, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, x: -20, transition: { duration: 0.2, ease: 'easeIn' } }
}
