import { motion } from 'framer-motion'
import { Volume2, Globe, Clock } from 'lucide-react'
import { staggerContainer, staggerItem, viewportConfig, cardHover } from './animations'

const problems = [
  {
    icon: Volume2,
    headline: 'Too much noise',
    description:
      'Thousands of posts daily. Most of it is noise, duplicates, or propaganda. You\'re scrolling, not analyzing.',
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
    description:
      'By the time you find it, process it, and understand it — it\'s already old news.',
  },
]

export function ProblemSection() {
  return (
    <section className="py-24 px-6" style={{ backgroundColor: '#0D1117' }}>
      <div className="mx-auto max-w-7xl">
        <motion.h2
          className="text-3xl md:text-4xl font-bold text-center mb-16"
          style={{ color: '#FFFFFF' }}
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
              className="rounded-xl p-8 border transition-colors duration-300"
              style={{
                backgroundColor: '#161B22',
                borderColor: '#30363D',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'rgba(0, 212, 170, 0.3)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#30363D'
              }}
            >
              <div
                className="w-12 h-12 rounded-full flex items-center justify-center mb-6"
                style={{ backgroundColor: 'rgba(0, 212, 170, 0.1)' }}
              >
                <item.icon size={24} style={{ color: '#00D4AA' }} />
              </div>
              <h3 className="text-xl font-bold mb-3" style={{ color: '#FFFFFF' }}>
                {item.headline}
              </h3>
              <p className="text-base leading-relaxed" style={{ color: '#8B949E' }}>
                {item.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
