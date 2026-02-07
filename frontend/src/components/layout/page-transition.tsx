import { motion } from 'framer-motion'
import { pageTransition } from '@/lib/animations'

export function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div initial="hidden" animate="visible" variants={pageTransition}>
      {children}
    </motion.div>
  )
}
