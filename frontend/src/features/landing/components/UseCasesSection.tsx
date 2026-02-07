import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Crosshair, TrendingUp, Landmark } from 'lucide-react'

const tabs = [
  {
    id: 'conflicts',
    label: 'Armed Conflicts',
    icon: Crosshair,
    headline: 'Monitor conflict zones in real-time',
    description:
      'Track military movements, rhetoric shifts, and ground-level reports from Ukraine, Middle East, and beyond. Detect escalations before they make headlines.',
    entries: [
      { text: 'Ukraine frontline update', sources: 12 },
      { text: 'IRGC naval exercise alert', sources: 8 },
      { text: 'Syria ceasefire negotiations', sources: 15 },
    ],
  },
  {
    id: 'trade',
    label: 'Trade & Sanctions',
    icon: TrendingUp,
    headline: 'Track economic warfare as it unfolds',
    description:
      'Monitor sanctions, tariffs, and trade policy shifts. Understand the signals from Beijing, Brussels, and Washington before markets react.',
    entries: [
      { text: 'EU sanctions package update', sources: 9 },
      { text: 'China rare earth export controls', sources: 11 },
      { text: 'US tariff announcement', sources: 14 },
    ],
  },
  {
    id: 'politics',
    label: 'US Politics',
    icon: Landmark,
    headline: 'Decode American political signals',
    description:
      'Follow the policy shifts, executive actions, and political narratives that shape global markets and alliances.',
    entries: [
      { text: 'Executive order analysis', sources: 7 },
      { text: 'Congressional hearing highlights', sources: 10 },
      { text: 'Campaign rhetoric tracker', sources: 6 },
    ],
  },
]

export function UseCasesSection() {
  const [activeTab, setActiveTab] = useState(0)
  const active = tabs[activeTab]

  return (
    <section id="use-cases" className="px-6 py-20 md:py-28 bg-card">
      <div className="mx-auto max-w-7xl">
        <motion.h2
          className="text-3xl md:text-4xl font-bold text-center mb-16 text-foreground"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          Built for what matters
        </motion.h2>

        {/* Tabs */}
        <div className="flex justify-center gap-2 md:gap-8 mb-12 border-b border-border">
          {tabs.map((tab, i) => {
            const Icon = tab.icon
            const isActive = i === activeTab
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(i)}
                className={`relative flex items-center gap-2 px-4 py-3 text-sm md:text-base font-medium transition-colors ${
                  isActive ? 'text-accent' : 'text-foreground-muted'
                }`}
              >
                <Icon size={18} />
                <span className="hidden sm:inline">{tab.label}</span>
                {isActive && (
                  <motion.div
                    layoutId="tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
              </button>
            )
          })}
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={active.id}
            className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* Left — text */}
            <div className="flex flex-col gap-4">
              <h3 className="text-2xl md:text-3xl font-bold text-foreground">
                {active.headline}
              </h3>
              <p className="text-lg leading-relaxed text-foreground-muted">
                {active.description}
              </p>
            </div>

            {/* Right — mockup card */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="rounded-xl p-6 bg-background border border-border"
            >
              <div className="flex items-center gap-2 mb-4">
                <div className="h-3 w-3 rounded-full bg-success" />
                <span className="text-xs font-medium text-foreground-muted">
                  Live feed
                </span>
              </div>
              <div className="flex flex-col gap-3">
                {active.entries.map((entry) => (
                  <div
                    key={entry.text}
                    className="flex items-center justify-between rounded-lg px-4 py-3 bg-card border border-border"
                  >
                    <span className="text-sm font-medium text-foreground/90">
                      {entry.text}
                    </span>
                    <span className="text-xs rounded-full px-2 py-0.5 bg-accent/10 text-accent">
                      {entry.sources} sources
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  )
}
