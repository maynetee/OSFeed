import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { PageLayout } from './components/PageLayout'

const fadeInUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5, ease: 'easeOut' },
}

export function NotFoundPage() {
  return (
    <PageLayout>
      <section className="flex flex-col items-center justify-center px-6 py-32 text-center">
        <motion.h1
          className="text-7xl font-bold"
          style={{ color: '#00D4AA' }}
          {...fadeInUp}
        >
          404
        </motion.h1>
        <motion.p
          className="mt-4 text-2xl font-semibold"
          style={{ color: '#FFFFFF' }}
          {...fadeInUp}
          transition={{ ...fadeInUp.transition, delay: 0.1 }}
        >
          Page not found
        </motion.p>
        <motion.p
          className="mt-2 max-w-md text-base"
          style={{ color: '#8B949E' }}
          {...fadeInUp}
          transition={{ ...fadeInUp.transition, delay: 0.2 }}
        >
          The page you're looking for doesn't exist or has been moved.
        </motion.p>
        <motion.div
          {...fadeInUp}
          transition={{ ...fadeInUp.transition, delay: 0.3 }}
        >
          <Link
            to="/"
            className="mt-8 inline-block rounded-lg px-6 py-3 text-sm font-semibold transition-opacity hover:opacity-90"
            style={{ backgroundColor: '#00D4AA', color: '#0D1117' }}
          >
            Back to homepage
          </Link>
        </motion.div>
      </section>
    </PageLayout>
  )
}
