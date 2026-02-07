import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion } from 'framer-motion'
import { PageLayout } from './components/PageLayout'
import { Seo } from './components/Seo'
import { api } from '@/lib/api/axios-instance'
import { trackEvent } from '@/lib/analytics'

const contactSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(100, 'Name must be at most 100 characters'),
  email: z.string().email('Please enter a valid email address'),
  company: z.string().min(2, 'Company must be at least 2 characters').max(100, 'Company must be at most 100 characters'),
  job_title: z.string().min(2, 'Job title must be at least 2 characters').max(100, 'Job title must be at most 100 characters'),
  company_size: z.enum(['1-10', '11-50', '51-200', '201-500', '500+'], {
    required_error: 'Please select a company size',
  }),
  message: z.string().max(2000, 'Message must be at most 2000 characters').optional().or(z.literal('')),
})

type ContactFormData = z.infer<typeof contactSchema>

const fadeInUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-40px' },
  transition: { duration: 0.5, ease: 'easeOut' },
}

const companySizes = ['1-10', '11-50', '51-200', '201-500', '500+'] as const

const inputStyle = {
  backgroundColor: 'transparent',
  borderColor: '#30363D',
  color: '#FFFFFF',
}

const focusClass = 'focus:outline-none focus:border-[#00D4AA]'

export function ContactSalesPage() {
  const [submitted, setSubmitted] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema),
  })

  const onSubmit = async (data: ContactFormData) => {
    setSubmitError(null)
    trackEvent("Contact Sales Submit")
    try {
      await api.post('/api/contact-sales', data)
      setSubmitted(true)
    } catch {
      setSubmitError('Something went wrong. Please try again later.')
    }
  }

  return (
    <PageLayout>
      <Seo title="Contact Sales — Osfeed" description="Talk to our sales team about Enterprise plans, custom integrations, and dedicated support for your organization." />
      <section className="px-6 py-20 md:py-28">
        <div className="mx-auto max-w-2xl">
          <motion.h1
            className="text-4xl md:text-5xl font-bold text-center"
            style={{ color: '#FFFFFF' }}
            {...fadeInUp}
          >
            Let&apos;s talk
          </motion.h1>
          <motion.p
            className="mt-4 text-lg text-center"
            style={{ color: '#8B949E' }}
            {...fadeInUp}
            transition={{ ...fadeInUp.transition, delay: 0.1 }}
          >
            Tell us about your organization and we&apos;ll get back to you within 24 hours.
          </motion.p>

          <motion.div
            className="mt-12 rounded-2xl p-8 md:p-10"
            style={{ backgroundColor: '#161B22', border: '1px solid #30363D' }}
            {...fadeInUp}
            transition={{ ...fadeInUp.transition, delay: 0.2 }}
          >
            {submitted ? (
              <motion.div
                className="text-center py-12"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
              >
                <div
                  className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full"
                  style={{ backgroundColor: 'rgba(0, 212, 170, 0.1)' }}
                >
                  <svg className="h-8 w-8" style={{ color: '#00D4AA' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold" style={{ color: '#FFFFFF' }}>
                  Thank you!
                </h2>
                <p className="mt-2 text-base" style={{ color: '#8B949E' }}>
                  We&apos;ll get back to you within 24 hours.
                </p>
              </motion.div>
            ) : (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#F3F4F6' }}>
                      Name <span style={{ color: '#00D4AA' }}>*</span>
                    </label>
                    <input
                      type="text"
                      {...register('name')}
                      className={`w-full rounded-lg border px-4 py-3 text-sm ${focusClass} transition-colors`}
                      style={inputStyle}
                      placeholder="Your name"
                    />
                    {errors.name && (
                      <p className="mt-1 text-sm" style={{ color: '#F85149' }}>{errors.name.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#F3F4F6' }}>
                      Email <span style={{ color: '#00D4AA' }}>*</span>
                    </label>
                    <input
                      type="email"
                      {...register('email')}
                      className={`w-full rounded-lg border px-4 py-3 text-sm ${focusClass} transition-colors`}
                      style={inputStyle}
                      placeholder="you@company.com"
                    />
                    {errors.email && (
                      <p className="mt-1 text-sm" style={{ color: '#F85149' }}>{errors.email.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#F3F4F6' }}>
                      Company <span style={{ color: '#00D4AA' }}>*</span>
                    </label>
                    <input
                      type="text"
                      {...register('company')}
                      className={`w-full rounded-lg border px-4 py-3 text-sm ${focusClass} transition-colors`}
                      style={inputStyle}
                      placeholder="Company name"
                    />
                    {errors.company && (
                      <p className="mt-1 text-sm" style={{ color: '#F85149' }}>{errors.company.message}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2" style={{ color: '#F3F4F6' }}>
                      Job Title <span style={{ color: '#00D4AA' }}>*</span>
                    </label>
                    <input
                      type="text"
                      {...register('job_title')}
                      className={`w-full rounded-lg border px-4 py-3 text-sm ${focusClass} transition-colors`}
                      style={inputStyle}
                      placeholder="Your role"
                    />
                    {errors.job_title && (
                      <p className="mt-1 text-sm" style={{ color: '#F85149' }}>{errors.job_title.message}</p>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: '#F3F4F6' }}>
                    Company Size <span style={{ color: '#00D4AA' }}>*</span>
                  </label>
                  <select
                    {...register('company_size')}
                    className={`w-full rounded-lg border px-4 py-3 text-sm ${focusClass} transition-colors appearance-none`}
                    style={inputStyle}
                    defaultValue=""
                  >
                    <option value="" disabled style={{ backgroundColor: '#161B22' }}>
                      Select company size
                    </option>
                    {companySizes.map((size) => (
                      <option key={size} value={size} style={{ backgroundColor: '#161B22' }}>
                        {size} employees
                      </option>
                    ))}
                  </select>
                  {errors.company_size && (
                    <p className="mt-1 text-sm" style={{ color: '#F85149' }}>{errors.company_size.message}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2" style={{ color: '#F3F4F6' }}>
                    Message
                  </label>
                  <textarea
                    {...register('message')}
                    rows={4}
                    className={`w-full rounded-lg border px-4 py-3 text-sm ${focusClass} transition-colors resize-none`}
                    style={inputStyle}
                    placeholder="Tell us about your needs..."
                  />
                  {errors.message && (
                    <p className="mt-1 text-sm" style={{ color: '#F85149' }}>{errors.message.message}</p>
                  )}
                </div>

                {submitError && (
                  <p className="text-sm" style={{ color: '#F85149' }}>{submitError}</p>
                )}

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full rounded-lg py-3 text-sm font-semibold transition-opacity hover:opacity-90 disabled:opacity-50"
                  style={{ backgroundColor: '#00D4AA', color: '#0D1117' }}
                >
                  {isSubmitting ? 'Submitting...' : 'Submit'}
                </button>
              </form>
            )}
          </motion.div>
        </div>
      </section>
    </PageLayout>
  )
}
