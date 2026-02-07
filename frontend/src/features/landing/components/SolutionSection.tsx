import { motion } from 'framer-motion'
import { Layers, Languages, Filter, Bell } from 'lucide-react'
import { staggerContainer, staggerItem, viewportConfig, cardHover } from './animations'

const features = [
  {
    icon: Layers,
    headline: 'All your sources. One feed.',
    description:
      'Connect hundreds of intelligence sources. Add your own or explore our curated collections by topic and region.',
  },
  {
    icon: Languages,
    headline: 'Read the world.',
    description:
      'AI-powered contextual translation that understands geopolitical jargon, military acronyms, and regional expressions.',
  },
  {
    icon: Filter,
    headline: 'Zero duplicates. Zero spam.',
    description:
      'Semantic deduplication removes reposts and copypasta. See each story once, with source count.',
  },
  {
    icon: Bell,
    headline: 'Know first.',
    description:
      'Real-time alerts on topics, regions, or keywords. Get notified the moment something happens.',
  },
]

export function SolutionSection() {
  return (
    <section className="py-24 px-6" style={{ backgroundColor: '#161B22' }}>
      <div className="mx-auto max-w-7xl">
        <motion.h2
          className="text-3xl md:text-4xl font-bold text-center mb-16"
          style={{ color: '#FFFFFF' }}
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={viewportConfig}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        >
          Intelligence, not information.
        </motion.h2>

        <motion.div
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={viewportConfig}
        >
          {features.map((item) => (
            <motion.div
              key={item.headline}
              variants={staggerItem}
              whileHover={cardHover}
              className="rounded-xl p-8 border transition-colors duration-300"
              style={{
                backgroundColor: '#0D1117',
                borderColor: '#30363D',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'rgba(0, 212, 170, 0.3)'
                e.currentTarget.style.boxShadow = '0 0 20px rgba(0, 212, 170, 0.08)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#30363D'
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              <div
                className="w-12 h-12 rounded-lg flex items-center justify-center mb-6"
                style={{ backgroundColor: 'rgba(0, 212, 170, 0.1)' }}
              >
                <item.icon size={24} style={{ color: '#00D4AA' }} />
              </div>
              <h3 className="text-lg font-bold mb-3" style={{ color: '#FFFFFF' }}>
                {item.headline}
              </h3>
              <p className="text-sm leading-relaxed" style={{ color: '#8B949E' }}>
                {item.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
