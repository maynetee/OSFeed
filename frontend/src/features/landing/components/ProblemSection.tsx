import { motion } from 'framer-motion'
import { Volume2, Globe, Clock } from 'lucide-react'
import { staggerContainer, staggerItem, viewportConfig, cardHover } from './animations'

const problems = [
  {
    icon: Volume2,
    headline: 'Too much noise',
    description:
      "Thousands of posts daily. Most of it is noise, duplicates, or propaganda. You're scrolling, not analyzing.",
  },
  {
    icon: Globe,
    headline: 'Lost in translation',
    description:
      'Critical intel is in Russian, Arabic, Farsi, Mandarin. Generic translators miss context and nuance.',
  },
  {
    icon: Clock,
    headline: 'Always behind',
    description: "By the time you find it, process it, and understand it — it's already old news.",
  },
]

export function ProblemSection() {
  return (
    <section className="py-24 px-6 bg-background">
      <div className="mx-auto max-w-7xl">
        <motion.h2
          className="text-3xl md:text-4xl font-bold text-center mb-16 text-foreground"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={viewportConfig}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        >
          The problem isn't access to information.
        </motion.h2>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-8"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={viewportConfig}
        >
          {problems.map((item) => (
            <motion.div
              key={item.headline}
              variants={staggerItem}
              whileHover={cardHover}
              className="rounded-xl p-8 border border-border bg-card transition-colors duration-300 hover:border-accent/30"
            >
              <div className="w-12 h-12 rounded-full flex items-center justify-center mb-6 bg-accent/10">
                <item.icon size={24} className="text-accent" />
              </div>
              <h3 className="text-xl font-bold mb-3 text-foreground">
                {item.headline}
              </h3>
              <p className="text-base leading-relaxed text-foreground-muted">
                {item.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
