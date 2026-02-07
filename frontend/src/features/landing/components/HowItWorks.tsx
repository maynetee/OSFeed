import { motion } from 'framer-motion'
import { Link2, Cpu, Zap, ArrowRight } from 'lucide-react'
import { staggerContainer, staggerItem, viewportConfig } from './animations'

const steps = [
  {
    number: '01',
    headline: 'Connect',
    description:
      'Add your sources or pick from our curated lists. Organized by region, topic, and relevance.',
    icon: Link2,
  },
  {
    number: '02',
    headline: 'Process',
    description:
      'Our AI translates, deduplicates, and filters in real-time. Noise becomes signal.',
    icon: Cpu,
  },
  {
    number: '03',
    headline: 'Act',
    description:
      'Get alerts, daily digests, or on-demand summaries. Your intelligence, your way.',
    icon: Zap,
  },
]

export function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 px-6" style={{ backgroundColor: '#0D1117' }}>
      <div className="mx-auto max-w-7xl">
        <motion.h2
          className="text-3xl md:text-4xl font-bold text-center mb-16"
          style={{ color: '#FFFFFF' }}
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={viewportConfig}
          transition={{ duration: 0.6, ease: 'easeOut' }}
        >
          How it works
        </motion.h2>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-6 relative"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={viewportConfig}
        >
          {steps.map((step, index) => (
            <motion.div key={step.number} variants={staggerItem} className="relative flex flex-col">
              {/* Connector arrow (desktop only, not on last) */}
              {index < steps.length - 1 && (
                <div className="hidden md:flex absolute top-1/2 -right-3 z-10 -translate-y-1/2 items-center justify-center w-6 h-6 rounded-full" style={{ backgroundColor: '#161B22', border: '1px solid #30363D' }}>
                  <ArrowRight size={12} style={{ color: '#00D4AA' }} />
                </div>
              )}

              <div
                className="rounded-xl p-8 border flex-1"
                style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
              >
                <div className="flex items-center gap-4 mb-6">
                  <span
                    className="text-4xl font-bold"
                    style={{ color: '#00D4AA' }}
                  >
                    {step.number}
                  </span>
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: 'rgba(0, 212, 170, 0.1)' }}
                  >
                    <step.icon size={20} style={{ color: '#00D4AA' }} />
                  </div>
                </div>
                <h3 className="text-xl font-bold mb-3" style={{ color: '#FFFFFF' }}>
                  {step.headline}
                </h3>
                <p className="text-base leading-relaxed" style={{ color: '#8B949E' }}>
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  )
}
