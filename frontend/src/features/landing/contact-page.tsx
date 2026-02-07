import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mail, Send, CheckCircle } from 'lucide-react'
import { PageLayout } from './components/PageLayout'
import { Seo } from './components/Seo'
import { trackEvent } from '@/lib/analytics'
import { api } from '@/lib/api/axios-instance'

const fadeIn = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-40px' },
  transition: { duration: 0.5, ease: 'easeOut' },
}

const slideInLeft = {
  initial: { opacity: 0, x: -32 },
  whileInView: { opacity: 1, x: 0 },
  viewport: { once: true, margin: '-40px' },
  transition: { duration: 0.5, ease: 'easeOut' },
}

const slideInRight = {
  initial: { opacity: 0, x: 32 },
  whileInView: { opacity: 1, x: 0 },
  viewport: { once: true, margin: '-40px' },
  transition: { duration: 0.5, ease: 'easeOut' },
}

const SUBJECT_OPTIONS = [
  'General Inquiry',
  'Technical Support',
  'Partnership',
  'Enterprise',
] as const

export function ContactPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [subject, setSubject] = useState<string>(SUBJECT_OPTIONS[0])
  const [message, setMessage] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !email.trim() || !message.trim()) return
    setSubmitting(true)
    setError(null)
    trackEvent('Contact Submit')
    try {
      await api.post('/api/contact-sales', {
        name,
        email,
        company: subject,
        job_title: 'N/A',
        company_size: '1-10',
        message: `[${subject}] ${message}`,
      })
      setSubmitted(true)
    } catch {
      setError('Something went wrong. Please try again later.')
    } finally {
      setSubmitting(false)
    }
  }

  const resetForm = () => {
    setName('')
    setEmail('')
    setSubject(SUBJECT_OPTIONS[0])
    setMessage('')
    setSubmitted(false)
  }

  const inputClasses =
    'w-full rounded-lg px-4 py-3 text-white placeholder-[#8B949E] border outline-none transition-colors duration-200 focus:border-[#00D4AA]'

  return (
    <PageLayout>
      <Seo
        title="Contact — Osfeed"
        description="Get in touch with the Osfeed team. Questions, feedback, or partnership inquiries — we'd love to hear from you."
      />
      {/* Hero */}
      <section className="px-6 pt-20 pb-12 text-center">
        <motion.h1
          {...fadeIn}
          className="text-4xl font-bold tracking-tight sm:text-5xl"
          style={{ color: '#FFFFFF' }}
        >
          Get in touch
        </motion.h1>
        <motion.p
          {...fadeIn}
          transition={{ duration: 0.5, ease: 'easeOut', delay: 0.1 }}
          className="mx-auto mt-4 max-w-xl text-lg"
          style={{ color: '#8B949E' }}
        >
          Questions, feedback, or partnership inquiries — we'd love to hear from you.
        </motion.p>
      </section>

      {/* Two-column layout */}
      <section className="mx-auto max-w-5xl px-6 pb-24">
        <div className="grid gap-10 lg:grid-cols-[1fr_380px]">
          {/* Left - Contact Form */}
          <motion.div {...slideInLeft}>
            <AnimatePresence mode="wait">
              {submitted ? (
                <motion.div
                  key="success"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.35, ease: 'easeOut' }}
                  className="flex flex-col items-center justify-center rounded-xl border p-12 text-center"
                  style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
                >
                  <CheckCircle size={48} style={{ color: '#3FB950' }} />
                  <h2 className="mt-4 text-2xl font-semibold" style={{ color: '#FFFFFF' }}>
                    Message sent!
                  </h2>
                  <p className="mt-2" style={{ color: '#8B949E' }}>
                    We'll get back to you within 24 hours.
                  </p>
                  <button
                    onClick={resetForm}
                    className="mt-6 text-sm font-medium hover:underline"
                    style={{ color: '#00D4AA' }}
                  >
                    Send another message
                  </button>
                </motion.div>
              ) : (
                <motion.form
                  key="form"
                  initial={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onSubmit={handleSubmit}
                  className="space-y-5"
                >
                  {/* Name */}
                  <div>
                    <label className="mb-2 block text-sm" style={{ color: '#8B949E' }}>
                      Name
                    </label>
                    <input
                      type="text"
                      required
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      placeholder="Your name"
                      className={inputClasses}
                      style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
                    />
                  </div>

                  {/* Email */}
                  <div>
                    <label className="mb-2 block text-sm" style={{ color: '#8B949E' }}>
                      Email
                    </label>
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      className={inputClasses}
                      style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
                    />
                  </div>

                  {/* Subject */}
                  <div>
                    <label className="mb-2 block text-sm" style={{ color: '#8B949E' }}>
                      Subject
                    </label>
                    <select
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      className={inputClasses}
                      style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
                    >
                      {SUBJECT_OPTIONS.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Message */}
                  <div>
                    <label className="mb-2 block text-sm" style={{ color: '#8B949E' }}>
                      Message
                    </label>
                    <textarea
                      required
                      maxLength={2000}
                      rows={6}
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="How can we help?"
                      className={`${inputClasses} resize-none`}
                      style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
                    />
                    <p className="mt-1 text-right text-xs" style={{ color: '#8B949E' }}>
                      {message.length}/2000
                    </p>
                  </div>

                  {error && (
                    <p className="text-sm" style={{ color: '#F85149' }}>
                      {error}
                    </p>
                  )}

                  {/* Submit */}
                  <button
                    type="submit"
                    disabled={submitting}
                    className="flex w-full items-center justify-center gap-2 rounded-lg px-4 py-3 font-semibold transition-opacity hover:opacity-90 disabled:opacity-50"
                    style={{ backgroundColor: '#00D4AA', color: '#0D1117' }}
                  >
                    <Send size={18} />
                    {submitting ? 'Sending...' : 'Send Message'}
                  </button>
                </motion.form>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Right - Contact Info */}
          <motion.div {...slideInRight}>
            <div
              className="rounded-xl border p-8"
              style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
            >
              <h3 className="text-lg font-semibold" style={{ color: '#FFFFFF' }}>
                Direct contact
              </h3>

              <a
                href="mailto:hello@osfeed.com"
                className="mt-6 flex items-center gap-3 transition-opacity hover:opacity-80"
                style={{ color: '#00D4AA' }}
              >
                <Mail size={20} />
                <span className="text-sm font-medium">hello@osfeed.com</span>
              </a>

              <div className="mt-8">
                <h4 className="text-sm font-semibold" style={{ color: '#FFFFFF' }}>
                  Response time
                </h4>
                <p className="mt-1 text-sm" style={{ color: '#8B949E' }}>
                  We typically respond within 24 hours.
                </p>
              </div>

              <div className="mt-8">
                <h4 className="text-sm font-semibold" style={{ color: '#FFFFFF' }}>
                  Enterprise
                </h4>
                <p className="mt-1 text-sm" style={{ color: '#8B949E' }}>
                  Looking for a custom plan or dedicated support? Reach out with "Enterprise" as the
                  subject and we'll connect you with our sales team.
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </PageLayout>
  )
}
