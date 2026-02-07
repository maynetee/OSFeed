import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Calendar, Tag, ArrowLeft, Clock } from 'lucide-react'
import { PageLayout } from './components/PageLayout'
import { articles } from './resources-page'

const categoryColors: Record<string, { bg: string; text: string }> = {
  Analysis: { bg: 'rgba(0, 212, 170, 0.1)', text: '#00D4AA' },
  Methodology: { bg: 'rgba(130, 80, 255, 0.1)', text: '#8250FF' },
  'Product Updates': { bg: 'rgba(56, 139, 253, 0.1)', text: '#388BFD' },
}

export function ResourceDetailPage() {
  const { slug } = useParams<{ slug: string }>()
  const article = articles.find((a) => a.slug === slug)

  if (!article) {
    return (
      <PageLayout>
        <section className="py-32 px-6 text-center">
          <h1 className="text-3xl font-bold" style={{ color: '#FFFFFF' }}>
            Article not found
          </h1>
          <Link
            to="/resources"
            className="mt-4 inline-flex items-center gap-1 text-sm font-medium"
            style={{ color: '#00D4AA' }}
          >
            <ArrowLeft size={14} /> Back to Resources
          </Link>
        </section>
      </PageLayout>
    )
  }

  return (
    <PageLayout>
      <article className="py-24 px-6">
        <div className="max-w-3xl mx-auto">
          {/* Back link */}
          <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Link
              to="/resources"
              className="inline-flex items-center gap-1.5 text-sm font-medium transition-colors hover:opacity-80"
              style={{ color: '#8B949E' }}
            >
              <ArrowLeft size={14} /> Back to Resources
            </Link>
          </motion.div>

          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-8"
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

            <h1
              className="mt-4 text-4xl md:text-5xl font-bold tracking-tight leading-tight"
              style={{ color: '#FFFFFF' }}
            >
              {article.title}
            </h1>

            <div className="mt-4 flex items-center gap-4 text-sm" style={{ color: '#8B949E' }}>
              <span className="flex items-center gap-1.5">
                <Calendar size={14} />
                {article.date}
              </span>
              <span className="flex items-center gap-1.5">
                <Clock size={14} />
                {article.readTime}
              </span>
            </div>
          </motion.div>

          {/* Divider */}
          <div className="my-8 border-t" style={{ borderColor: '#30363D' }} />

          {/* Body */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="prose-custom space-y-6"
          >
            <p className="text-base leading-relaxed" style={{ color: '#C9D1D9' }}>
              {article.excerpt} The landscape of open-source intelligence continues to evolve at an
              unprecedented pace, driven by the convergence of advanced natural language processing,
              real-time data collection, and sophisticated analytical frameworks. Understanding
              these dynamics is essential for anyone working in the intelligence space today.
            </p>

            <p className="text-base leading-relaxed" style={{ color: '#C9D1D9' }}>
              Modern OSINT practitioners face a dual challenge: the volume of available information
              grows exponentially while the time available for analysis continues to shrink.
              Traditional methods of manual review and keyword-based filtering are no longer
              sufficient. Instead, analysts must leverage semantic understanding, automated
              translation pipelines, and vector-based deduplication to maintain operational
              awareness across dozens or even hundreds of sources simultaneously.
            </p>

            <p className="text-base leading-relaxed" style={{ color: '#C9D1D9' }}>
              The implications extend beyond the technical. As intelligence tools become more
              accessible, the competitive advantage shifts from data access to analytical
              capability. Organizations that invest in structured workflows — combining automated
              collection with human-in-the-loop validation — consistently outperform those relying
              on either approach in isolation. The key lies in building systems that amplify human
              judgment rather than replace it.
            </p>

            <p className="text-base leading-relaxed" style={{ color: '#C9D1D9' }}>
              Looking ahead, the integration of multi-modal intelligence sources — text, imagery,
              geospatial data, and network analysis — will define the next generation of OSINT
              platforms. Practitioners who develop fluency across these domains, supported by tools
              that unify collection and analysis, will be best positioned to deliver actionable
              intelligence in an increasingly complex global environment.
            </p>
          </motion.div>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="mt-16 rounded-xl p-8 text-center border"
            style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
          >
            <h3 className="text-2xl font-bold" style={{ color: '#FFFFFF' }}>
              Start your intelligence journey
            </h3>
            <p className="mt-2 text-sm" style={{ color: '#8B949E' }}>
              Set up your feeds, configure alerts, and monitor the sources that matter.
            </p>
            <Link
              to="/signup"
              className="mt-6 inline-flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-semibold transition-opacity hover:opacity-90"
              style={{ backgroundColor: '#00D4AA', color: '#0D1117' }}
            >
              Get Started
            </Link>
          </motion.div>
        </div>
      </article>
    </PageLayout>
  )
}
