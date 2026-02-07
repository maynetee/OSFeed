import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { trackEvent } from '@/lib/analytics'

export function CtaFinal() {
  return (
    <section
      className="relative px-6 py-24 md:py-32 overflow-hidden"
      style={{
        background: 'linear-gradient(180deg, hsl(var(--card)) 0%, hsl(var(--background)) 100%)',
      }}
    >
      {/* Subtle glow */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full blur-3xl opacity-10 pointer-events-none bg-accent"
      />

      <motion.div
        className="relative mx-auto max-w-2xl text-center flex flex-col items-center gap-6"
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
      >
        <h2 className="text-3xl md:text-4xl font-bold text-foreground">
          Ready to cut through the noise?
        </h2>
        <p className="text-lg text-foreground-muted">
          Start monitoring in minutes.
        </p>

        <div className="flex flex-wrap justify-center gap-4 mt-4">
          <Link
            to="/signup"
            className="rounded-lg px-8 py-3 font-semibold text-base transition-opacity hover:opacity-90 bg-accent text-accent-foreground"
            onClick={() => trackEvent('CTA Click', { button: 'get-started-bottom' })}
          >
            Get Started →
          </Link>
          <Link
            to="/contact-sales"
            className="rounded-lg px-8 py-3 font-semibold text-base transition-opacity hover:opacity-90 border border-border text-foreground"
            onClick={() => trackEvent('CTA Click', { button: 'contact-sales-bottom' })}
          >
            Contact Sales →
          </Link>
        </div>
      </motion.div>
    </section>
  )
}
