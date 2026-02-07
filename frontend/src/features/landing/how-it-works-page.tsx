import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Link2, Cpu, Zap, Crosshair, TrendingUp, Landmark, ArrowRight } from 'lucide-react'
import { PageLayout } from './components/PageLayout'
import { Seo } from './components/Seo'
import {
  fadeInUp,
  staggerContainer,
  staggerItem,
  slideInRight,
  slideInLeft,
  viewportConfig,
} from './components/animations'

/* ─── Process Steps ──────────────────────────────────────────────── */

const steps = [
  {
    number: '01',
    headline: 'Connect',
    icon: Link2,
    description:
      'Add your sources or pick from our curated lists. Organized by region, topic, and relevance.',
    detail: {
      type: 'sources' as const,
      items: [
        { name: 'Ukraine Military Updates', region: 'Eastern Europe' },
        { name: 'Middle East Monitor', region: 'MENA' },
        { name: 'Global Trade Alert', region: 'Global' },
      ],
    },
  },
  {
    number: '02',
    headline: 'Process',
    icon: Cpu,
    description: 'Our AI translates, deduplicates, and filters in real-time. Noise becomes signal.',
    detail: {
      type: 'translation' as const,
      raw: 'Военные учения начались в западной части Чёрного моря с участием трёх фрегатов...',
      translated:
        'Military exercises began in the western Black Sea with the participation of three frigates...',
    },
  },
  {
    number: '03',
    headline: 'Act',
    icon: Zap,
    description: 'Get alerts, daily digests, or on-demand summaries. Your intelligence, your way.',
    detail: {
      type: 'alerts' as const,
      items: [
        { title: 'Escalation detected', subtitle: 'Ukraine — 12 correlated sources', urgent: true },
        {
          title: 'Daily digest ready',
          subtitle: 'Trade & Sanctions — 34 new items',
          urgent: false,
        },
        { title: 'Keyword match', subtitle: '"sanctions" appeared in 8 channels', urgent: false },
      ],
    },
  },
]

/* ─── Use-Case Tabs ──────────────────────────────────────────────── */

const useCases = [
  {
    id: 'conflicts',
    label: 'Armed Conflicts',
    icon: Crosshair,
    headline: 'Monitor conflict zones in real-time',
    description:
      'Track military movements, rhetoric shifts, and ground-level reports from Ukraine, Middle East, and beyond. Detect escalations before they make headlines.',
    bullets: [
      'Cross-reference multiple ground-level sources automatically',
      'Detect troop movement patterns through language analysis',
      'Real-time escalation scoring based on rhetoric intensity',
      'Historical timeline reconstruction for conflict narratives',
    ],
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
    bullets: [
      'Monitor sanctions announcements across jurisdictions',
      'Track supply chain disruptions in real-time',
      'Detect policy signals before official announcements',
      'Correlate trade actions with geopolitical events',
    ],
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
    bullets: [
      'Track executive orders and their downstream effects',
      'Monitor congressional committee activities',
      'Analyze campaign rhetoric shifts and polling signals',
      'Correlate domestic policy changes with international reactions',
    ],
    entries: [
      { text: 'Executive order analysis', sources: 7 },
      { text: 'Congressional hearing highlights', sources: 10 },
      { text: 'Campaign rhetoric tracker', sources: 6 },
    ],
  },
]

/* ─── Visual Mockup Sub-Components ───────────────────────────────── */

function SourceListMockup({ items }: { items: { name: string; region: string }[] }) {
  return (
    <div
      className="rounded-xl p-6"
      style={{ backgroundColor: '#0D1117', border: '1px solid #30363D' }}
    >
      <div className="flex items-center gap-2 mb-4">
        <div className="h-3 w-3 rounded-full" style={{ backgroundColor: '#3FB950' }} />
        <span className="text-xs font-medium" style={{ color: '#8B949E' }}>
          Source library
        </span>
      </div>
      <div className="flex flex-col gap-3">
        {items.map((item) => (
          <div
            key={item.name}
            className="flex items-center justify-between rounded-lg px-4 py-3"
            style={{ backgroundColor: '#161B22', border: '1px solid #21262D' }}
          >
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: '#00D4AA' }} />
              <span className="text-sm font-medium" style={{ color: '#E6EDF3' }}>
                {item.name}
              </span>
            </div>
            <span
              className="text-xs rounded-full px-2 py-0.5"
              style={{ backgroundColor: 'rgba(0, 212, 170, 0.1)', color: '#00D4AA' }}
            >
              {item.region}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function TranslationMockup({ raw, translated }: { raw: string; translated: string }) {
  return (
    <div
      className="rounded-xl p-6"
      style={{ backgroundColor: '#0D1117', border: '1px solid #30363D' }}
    >
      <div className="flex items-center gap-2 mb-4">
        <Cpu size={14} style={{ color: '#8B949E' }} />
        <span className="text-xs font-medium" style={{ color: '#8B949E' }}>
          AI Translation Engine
        </span>
      </div>
      <div className="flex flex-col gap-4">
        <div
          className="rounded-lg px-4 py-3"
          style={{ backgroundColor: '#161B22', border: '1px solid #21262D' }}
        >
          <span className="text-xs font-medium block mb-1" style={{ color: '#8B949E' }}>
            Original (RU)
          </span>
          <p className="text-sm" style={{ color: '#E6EDF3' }}>
            {raw}
          </p>
        </div>
        <div className="flex justify-center">
          <motion.div
            animate={{ y: [0, 4, 0] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          >
            <ArrowRight size={16} style={{ color: '#00D4AA', transform: 'rotate(90deg)' }} />
          </motion.div>
        </div>
        <div
          className="rounded-lg px-4 py-3"
          style={{
            backgroundColor: 'rgba(0, 212, 170, 0.05)',
            border: '1px solid rgba(0, 212, 170, 0.2)',
          }}
        >
          <span className="text-xs font-medium block mb-1" style={{ color: '#00D4AA' }}>
            Translated (EN)
          </span>
          <p className="text-sm" style={{ color: '#E6EDF3' }}>
            {translated}
          </p>
        </div>
      </div>
    </div>
  )
}

function AlertsMockup({
  items,
}: {
  items: { title: string; subtitle: string; urgent: boolean }[]
}) {
  return (
    <div
      className="rounded-xl p-6"
      style={{ backgroundColor: '#0D1117', border: '1px solid #30363D' }}
    >
      <div className="flex items-center gap-2 mb-4">
        <Zap size={14} style={{ color: '#8B949E' }} />
        <span className="text-xs font-medium" style={{ color: '#8B949E' }}>
          Intelligence alerts
        </span>
      </div>
      <div className="flex flex-col gap-3">
        {items.map((item) => (
          <div
            key={item.title}
            className="flex items-center gap-3 rounded-lg px-4 py-3"
            style={{ backgroundColor: '#161B22', border: '1px solid #21262D' }}
          >
            <div
              className="w-2 h-2 rounded-full flex-shrink-0"
              style={{ backgroundColor: item.urgent ? '#F85149' : '#00D4AA' }}
            />
            <div className="flex-1 min-w-0">
              <span className="text-sm font-medium block" style={{ color: '#E6EDF3' }}>
                {item.title}
              </span>
              <span className="text-xs" style={{ color: '#8B949E' }}>
                {item.subtitle}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function StepMockup({ step }: { step: (typeof steps)[number] }) {
  const { detail } = step
  if (detail.type === 'sources') return <SourceListMockup items={detail.items} />
  if (detail.type === 'translation')
    return <TranslationMockup raw={detail.raw} translated={detail.translated} />
  return <AlertsMockup items={detail.items} />
}

/* ─── Page ────────────────────────────────────────────────────────── */

export function HowItWorksPage() {
  const [activeTab, setActiveTab] = useState(0)
  const active = useCases[activeTab]

  return (
    <PageLayout>
      <Seo
        title="How It Works — Osfeed"
        description="Learn how Osfeed collects, translates, deduplicates, and summarizes intelligence from Telegram channels in real time."
      />
      {/* ── Hero ── */}
      <section className="py-24 md:py-32 px-6 text-center">
        <div className="mx-auto max-w-3xl">
          <motion.h1
            className="text-4xl md:text-6xl font-bold mb-6"
            style={{ color: '#FFFFFF' }}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          >
            How <span style={{ color: '#00D4AA' }}>Osfeed</span> works
          </motion.h1>
          <motion.p
            className="text-lg md:text-xl leading-relaxed"
            style={{ color: '#8B949E' }}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: 'easeOut', delay: 0.2 }}
          >
            From raw data to actionable intelligence in three steps.
          </motion.p>
        </div>
      </section>

      {/* ── The Process ── */}
      <section className="py-20 md:py-28 px-6" style={{ backgroundColor: '#0D1117' }}>
        <div className="mx-auto max-w-7xl">
          <motion.h2
            className="text-3xl md:text-4xl font-bold text-center mb-20"
            style={{ color: '#FFFFFF' }}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={viewportConfig}
            transition={{ duration: 0.6, ease: 'easeOut' }}
          >
            The process
          </motion.h2>

          <div className="flex flex-col gap-24 md:gap-32">
            {steps.map((step, index) => {
              const isReversed = index % 2 === 1
              const Icon = step.icon
              return (
                <motion.div
                  key={step.number}
                  className={`grid grid-cols-1 lg:grid-cols-2 gap-12 items-center ${isReversed ? 'lg:direction-rtl' : ''}`}
                  variants={staggerContainer}
                  initial="hidden"
                  whileInView="visible"
                  viewport={viewportConfig}
                >
                  {/* Text side */}
                  <motion.div
                    className={`flex flex-col gap-4 ${isReversed ? 'lg:order-2' : ''}`}
                    variants={isReversed ? slideInRight : slideInLeft}
                  >
                    <div className="flex items-center gap-4 mb-2">
                      <span className="text-5xl font-bold" style={{ color: '#00D4AA' }}>
                        {step.number}
                      </span>
                      <div
                        className="w-12 h-12 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: 'rgba(0, 212, 170, 0.1)' }}
                      >
                        <Icon size={24} style={{ color: '#00D4AA' }} />
                      </div>
                    </div>
                    <h3 className="text-2xl md:text-3xl font-bold" style={{ color: '#FFFFFF' }}>
                      {step.headline}
                    </h3>
                    <p className="text-lg leading-relaxed" style={{ color: '#8B949E' }}>
                      {step.description}
                    </p>
                  </motion.div>

                  {/* Visual mockup side */}
                  <motion.div
                    className={isReversed ? 'lg:order-1' : ''}
                    variants={isReversed ? slideInLeft : slideInRight}
                  >
                    <StepMockup step={step} />
                  </motion.div>
                </motion.div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── Use Cases ── */}
      <section className="px-6 py-20 md:py-28" style={{ backgroundColor: '#161B22' }}>
        <div className="mx-auto max-w-7xl">
          <motion.h2
            className="text-3xl md:text-4xl font-bold text-center mb-16"
            style={{ color: '#FFFFFF' }}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={viewportConfig}
            transition={{ duration: 0.6 }}
          >
            Built for what matters
          </motion.h2>

          {/* Tabs */}
          <div
            className="flex justify-center gap-2 md:gap-8 mb-12 border-b"
            style={{ borderColor: '#30363D' }}
          >
            {useCases.map((tab, i) => {
              const Icon = tab.icon
              const isActive = i === activeTab
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(i)}
                  className="relative flex items-center gap-2 px-4 py-3 text-sm md:text-base font-medium transition-colors"
                  style={{ color: isActive ? '#00D4AA' : '#8B949E' }}
                >
                  <Icon size={18} />
                  <span className="hidden sm:inline">{tab.label}</span>
                  {isActive && (
                    <motion.div
                      layoutId="hiw-tab-indicator"
                      className="absolute bottom-0 left-0 right-0 h-0.5"
                      style={{ backgroundColor: '#00D4AA' }}
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                </button>
              )
            })}
          </div>

          {/* Tab Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={active.id}
              className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              {/* Left — text + bullets */}
              <div className="flex flex-col gap-4">
                <h3 className="text-2xl md:text-3xl font-bold" style={{ color: '#FFFFFF' }}>
                  {active.headline}
                </h3>
                <p className="text-lg leading-relaxed" style={{ color: '#8B949E' }}>
                  {active.description}
                </p>
                <ul className="flex flex-col gap-2 mt-2">
                  {active.bullets.map((bullet) => (
                    <li
                      key={bullet}
                      className="flex items-start gap-2 text-sm"
                      style={{ color: '#8B949E' }}
                    >
                      <span
                        className="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: '#00D4AA' }}
                      />
                      {bullet}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Right — mockup card */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.1 }}
                className="rounded-xl p-6"
                style={{ backgroundColor: '#0D1117', border: '1px solid #30363D' }}
              >
                <div className="flex items-center gap-2 mb-4">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: '#3FB950' }} />
                  <span className="text-xs font-medium" style={{ color: '#8B949E' }}>
                    Live feed
                  </span>
                </div>
                <div className="flex flex-col gap-3">
                  {active.entries.map((entry) => (
                    <div
                      key={entry.text}
                      className="flex items-center justify-between rounded-lg px-4 py-3"
                      style={{ backgroundColor: '#161B22', border: '1px solid #21262D' }}
                    >
                      <span className="text-sm font-medium" style={{ color: '#E6EDF3' }}>
                        {entry.text}
                      </span>
                      <span
                        className="text-xs rounded-full px-2 py-0.5"
                        style={{ backgroundColor: 'rgba(0, 212, 170, 0.1)', color: '#00D4AA' }}
                      >
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

      {/* ── CTA ── */}
      <section
        className="relative py-24 md:py-32 px-6 overflow-hidden"
        style={{ backgroundColor: '#0D1117' }}
      >
        {/* Background glow */}
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full blur-[160px] pointer-events-none"
          style={{ backgroundColor: 'rgba(0, 212, 170, 0.06)' }}
        />

        <motion.div
          className="relative mx-auto max-w-2xl text-center flex flex-col items-center gap-8"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={viewportConfig}
        >
          <motion.h2
            className="text-3xl md:text-5xl font-bold"
            style={{ color: '#FFFFFF' }}
            variants={fadeInUp}
          >
            Ready to see it in action?
          </motion.h2>

          <motion.div className="flex flex-col sm:flex-row gap-4" variants={staggerItem}>
            <Link
              to="/signup"
              className="inline-flex items-center justify-center gap-2 rounded-lg px-8 py-3 text-base font-semibold transition-opacity hover:opacity-90"
              style={{ backgroundColor: '#00D4AA', color: '#0D1117' }}
            >
              Get Started
              <ArrowRight size={18} />
            </Link>
            <Link
              to="/contact"
              className="inline-flex items-center justify-center gap-2 rounded-lg px-8 py-3 text-base font-semibold transition-colors hover:bg-white/5"
              style={{ border: '1px solid #30363D', color: '#FFFFFF' }}
            >
              Contact Sales
              <ArrowRight size={18} />
            </Link>
          </motion.div>
        </motion.div>
      </section>
    </PageLayout>
  )
}
