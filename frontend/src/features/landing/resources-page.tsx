import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Calendar, Tag, ArrowRight, Clock } from 'lucide-react'
import { PageLayout } from './components/PageLayout'
import { Seo } from './components/Seo'

export interface Article {
  title: string
  slug: string
  date: string
  category: 'Analysis' | 'Methodology' | 'Product Updates'
  excerpt: string
  readTime: string
}

export const articles: Article[] = [
  {
    title: 'Understanding the Signal-to-Noise Problem in Intelligence',
    slug: 'signal-to-noise-problem',
    date: 'February 3, 2026',
    category: 'Analysis',
    excerpt:
      'In an era of information overload, the ability to separate critical intelligence from noise has become the defining challenge for analysts and decision-makers worldwide.',
    readTime: '8 min read',
  },
  {
    title: 'How AI is Transforming Geopolitical Analysis',
    slug: 'ai-geopolitical-analysis',
    date: 'January 28, 2026',
    category: 'Methodology',
    excerpt:
      'Artificial intelligence is reshaping how we process, analyze, and act on geopolitical intelligence. From real-time translation to semantic deduplication, the tools are evolving fast.',
    readTime: '6 min read',
  },
  {
    title: 'Weekly Intelligence Brief: Global Tensions Update',
    slug: 'weekly-brief-global-tensions',
    date: 'January 21, 2026',
    category: 'Analysis',
    excerpt:
      "This week's intelligence brief covers escalating trade disputes, military movements in Eastern Europe, and shifting alliances in the Middle East.",
    readTime: '5 min read',
  },
  {
    title: 'Getting Started with Osfeed: A Complete Guide',
    slug: 'getting-started-guide',
    date: 'January 15, 2026',
    category: 'Product Updates',
    excerpt:
      'Everything you need to know to set up your intelligence feeds, configure alerts, and start monitoring the sources that matter most to your work.',
    readTime: '10 min read',
  },
]

const categories = ['All', 'Analysis', 'Methodology', 'Product Updates'] as const

const categoryColors: Record<string, { bg: string; text: string }> = {
  Analysis: { bg: 'rgba(0, 212, 170, 0.1)', text: '#00D4AA' },
  Methodology: { bg: 'rgba(130, 80, 255, 0.1)', text: '#8250FF' },
  'Product Updates': { bg: 'rgba(56, 139, 253, 0.1)', text: '#388BFD' },
}

export function ResourcesPage() {
  const [activeTab, setActiveTab] = useState<string>('All')

  const filtered = activeTab === 'All' ? articles : articles.filter((a) => a.category === activeTab)

  return (
    <PageLayout>
      <Seo title="Intelligence Brief — Osfeed" description="Read the latest intelligence briefs, analysis, and guides on OSINT methodology and Telegram monitoring." />
      {/* Hero */}
      <section className="py-24 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-5xl md:text-6xl font-bold tracking-tight"
            style={{ color: '#FFFFFF' }}
          >
            Intelligence Brief
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-4 text-lg"
            style={{ color: '#8B949E' }}
          >
            Analysis, insights, and perspectives on global events.
          </motion.p>
        </div>
      </section>

      {/* Filter Tabs */}
      <section className="px-6">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-1 border-b" style={{ borderColor: '#30363D' }}>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setActiveTab(cat)}
                className="relative px-4 py-3 text-sm font-medium transition-colors"
                style={{ color: activeTab === cat ? '#FFFFFF' : '#8B949E' }}
              >
                {cat}
                {activeTab === cat && (
                  <motion.div
                    layoutId="tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5"
                    style={{ backgroundColor: '#00D4AA' }}
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Articles */}
      <section className="py-12 px-6">
        <div className="max-w-4xl mx-auto">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col gap-6"
            >
              {filtered.map((article, i) => (
                <motion.div
                  key={article.slug}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: i * 0.1 }}
                >
                  <Link to={`/resources/${article.slug}`} className="block group">
                    <div
                      className="rounded-xl p-6 border transition-all duration-300 group-hover:shadow-lg"
                      style={{
                        backgroundColor: '#161B22',
                        borderColor: '#30363D',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = 'rgba(0, 212, 170, 0.4)'
                        e.currentTarget.style.boxShadow = '0 0 20px rgba(0, 212, 170, 0.08)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = '#30363D'
                        e.currentTarget.style.boxShadow = 'none'
                      }}
                    >
                      <span
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
                        style={{
                          backgroundColor: categoryColors[article.category]?.bg,
                          color: categoryColors[article.category]?.text,
                        }}
                      >
                        <Tag size={12} />
                        {article.category}
                      </span>

                      <h2
                        className="mt-3 text-xl font-bold group-hover:underline"
                        style={{ color: '#FFFFFF' }}
                      >
                        {article.title}
                      </h2>

                      <div className="mt-2 flex items-center gap-3 text-xs" style={{ color: '#8B949E' }}>
                        <span className="flex items-center gap-1">
                          <Calendar size={12} />
                          {article.date}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock size={12} />
                          {article.readTime}
                        </span>
                      </div>

                      <p className="mt-3 text-sm leading-relaxed line-clamp-3" style={{ color: '#8B949E' }}>
                        {article.excerpt}
                      </p>

                      <span
                        className="mt-4 inline-flex items-center gap-1 text-sm font-medium"
                        style={{ color: '#00D4AA' }}
                      >
                        Read more <ArrowRight size={14} />
                      </span>
                    </div>
                  </Link>
                </motion.div>
              ))}

              {filtered.length === 0 && (
                <p className="text-center py-12" style={{ color: '#8B949E' }}>
                  No articles in this category yet.
                </p>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </section>
    </PageLayout>
  )
}
