import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Check, Minus, ChevronDown } from 'lucide-react'
import { PageLayout } from './components/PageLayout'
import { Seo } from './components/Seo'
import { trackEvent } from '@/lib/analytics'

const fadeInUp = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-40px' },
  transition: { duration: 0.5, ease: 'easeOut' },
}

interface Feature {
  name: string
  included: boolean
}

interface Plan {
  name: string
  label: string
  monthlyPrice: string
  yearlyPrice: string
  users: string
  features: Feature[]
  cta: string
  ctaLink: string
  highlighted?: boolean
  outlined?: boolean
}

const plans: Plan[] = [
  {
    name: 'Solo',
    label: 'For individuals',
    monthlyPrice: '€99',
    yearlyPrice: '€79',
    users: '1',
    features: [
      { name: 'Unlimited sources', included: true },
      { name: 'Real-time translation', included: true },
      { name: 'Semantic deduplication', included: true },
      { name: 'Custom alerts', included: true },
      { name: 'Daily digests', included: true },
      { name: 'On-demand summaries', included: true },
      { name: 'Shared workspace', included: false },
      { name: 'Priority support', included: false },
      { name: 'SSO/SAML', included: false },
      { name: 'Dedicated account manager', included: false },
      { name: 'Custom integrations', included: false },
    ],
    cta: 'Get Started',
    ctaLink: '/signup?plan=solo',
  },
  {
    name: 'Team',
    label: 'For teams up to 5',
    monthlyPrice: '€399',
    yearlyPrice: '€319',
    users: 'Up to 5',
    features: [
      { name: 'Unlimited sources', included: true },
      { name: 'Real-time translation', included: true },
      { name: 'Semantic deduplication', included: true },
      { name: 'Custom alerts', included: true },
      { name: 'Daily digests', included: true },
      { name: 'On-demand summaries', included: true },
      { name: 'Shared workspace', included: true },
      { name: 'Priority support', included: true },
      { name: 'SSO/SAML', included: false },
      { name: 'Dedicated account manager', included: false },
      { name: 'Custom integrations', included: false },
    ],
    cta: 'Get Started',
    ctaLink: '/signup?plan=team',
    highlighted: true,
  },
  {
    name: 'Enterprise',
    label: 'For organizations',
    monthlyPrice: 'Custom',
    yearlyPrice: 'Custom',
    users: 'Unlimited',
    features: [
      { name: 'Unlimited sources', included: true },
      { name: 'Real-time translation', included: true },
      { name: 'Semantic deduplication', included: true },
      { name: 'Custom alerts', included: true },
      { name: 'Daily digests', included: true },
      { name: 'On-demand summaries', included: true },
      { name: 'Shared workspace', included: true },
      { name: 'Priority support', included: true },
      { name: 'SSO/SAML', included: true },
      { name: 'Dedicated account manager', included: true },
      { name: 'Custom integrations', included: true },
    ],
    cta: 'Contact Sales',
    ctaLink: '/contact-sales',
    outlined: true,
  },
]

const faqs = [
  {
    question: 'Is there a free trial?',
    answer:
      "We don't offer a free trial, but you can cancel your subscription within the first 14 days for a full refund.",
  },
  {
    question: 'Can I upgrade later?',
    answer: 'Yes, you can upgrade anytime. Your billing will be prorated.',
  },
  {
    question: 'What payment methods do you accept?',
    answer:
      'Credit card for Solo and Team. Wire transfer available for Enterprise.',
  },
  {
    question: 'Can I cancel anytime?',
    answer:
      'Yes. Monthly plans can be cancelled anytime. Yearly plans are non-refundable but you keep access until the end of the period.',
  },
]

function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false)

  return (
    <div
      className="border-b"
      style={{ borderColor: '#30363D' }}
    >
      <button
        className="flex w-full items-center justify-between py-5 text-left"
        onClick={() => setOpen(!open)}
      >
        <span className="text-base font-medium" style={{ color: '#FFFFFF' }}>
          {question}
        </span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="h-5 w-5" style={{ color: '#8B949E' }} />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <p className="pb-5 text-sm leading-relaxed" style={{ color: '#8B949E' }}>
              {answer}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export function PricingPage() {
  const [yearly, setYearly] = useState(false)

  return (
    <PageLayout>
      <Seo title="Pricing — Osfeed" description="Choose the right plan for your intelligence needs. Solo, Team, and Enterprise options with full platform access." />
      {/* Hero */}
      <section className="px-6 py-20 md:py-28 text-center">
        <div className="mx-auto max-w-3xl">
          <motion.h1
            className="text-4xl md:text-5xl font-bold"
            style={{ color: '#FFFFFF' }}
            {...fadeInUp}
          >
            Choose your plan
          </motion.h1>
          <motion.p
            className="mt-4 text-lg"
            style={{ color: '#8B949E' }}
            {...fadeInUp}
            transition={{ ...fadeInUp.transition, delay: 0.1 }}
          >
            Start with Solo or scale with your team. All plans include full access to our intelligence platform.
          </motion.p>

          {/* Toggle */}
          <motion.div
            className="mt-10 inline-flex items-center gap-3 rounded-full px-1 py-1"
            style={{ backgroundColor: '#161B22', border: '1px solid #30363D' }}
            {...fadeInUp}
            transition={{ ...fadeInUp.transition, delay: 0.2 }}
          >
            <button
              className="rounded-full px-5 py-2 text-sm font-medium transition-colors"
              style={{
                backgroundColor: !yearly ? '#00D4AA' : 'transparent',
                color: !yearly ? '#0D1117' : '#8B949E',
              }}
              onClick={() => { setYearly(false); trackEvent("Pricing Toggle", { period: "monthly" }) }}
            >
              Monthly
            </button>
            <button
              className="relative rounded-full px-5 py-2 text-sm font-medium transition-colors"
              style={{
                backgroundColor: yearly ? '#00D4AA' : 'transparent',
                color: yearly ? '#0D1117' : '#8B949E',
              }}
              onClick={() => { setYearly(true); trackEvent("Pricing Toggle", { period: "yearly" }) }}
            >
              Yearly
              <span
                className="absolute -top-3 -right-3 rounded-full px-2 py-0.5 text-[10px] font-bold"
                style={{ backgroundColor: '#00D4AA', color: '#0D1117' }}
              >
                Save 20%
              </span>
            </button>
          </motion.div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-6xl grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map((plan, i) => (
            <motion.div
              key={plan.name}
              className="relative rounded-2xl p-8 flex flex-col"
              style={{
                backgroundColor: '#161B22',
                border: plan.highlighted
                  ? '2px solid #00D4AA'
                  : '1px solid #30363D',
              }}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-40px' }}
              transition={{ duration: 0.5, ease: 'easeOut', delay: i * 0.1 }}
            >
              {plan.highlighted && (
                <span
                  className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full px-3 py-1 text-xs font-bold"
                  style={{ backgroundColor: '#00D4AA', color: '#0D1117' }}
                >
                  Popular
                </span>
              )}

              <p className="text-sm font-medium" style={{ color: '#8B949E' }}>
                {plan.label}
              </p>
              <h3 className="mt-2 text-2xl font-bold" style={{ color: '#FFFFFF' }}>
                {plan.name}
              </h3>

              <div className="mt-4 flex items-baseline gap-1">
                {plan.monthlyPrice !== 'Custom' ? (
                  <>
                    <span className="text-4xl font-bold" style={{ color: '#FFFFFF' }}>
                      {yearly ? plan.yearlyPrice : plan.monthlyPrice}
                    </span>
                    <span className="text-sm" style={{ color: '#8B949E' }}>
                      /mo
                    </span>
                  </>
                ) : (
                  <span className="text-4xl font-bold" style={{ color: '#FFFFFF' }}>
                    Custom
                  </span>
                )}
              </div>

              <p className="mt-2 text-sm" style={{ color: '#8B949E' }}>
                {plan.users} {plan.users === '1' ? 'user' : 'users'}
              </p>

              <div className="my-6 h-px" style={{ backgroundColor: '#30363D' }} />

              <ul className="flex-1 space-y-3">
                {plan.features.map((f) => (
                  <li key={f.name} className="flex items-center gap-2 text-sm">
                    {f.included ? (
                      <Check className="h-4 w-4 flex-shrink-0" style={{ color: '#00D4AA' }} />
                    ) : (
                      <Minus className="h-4 w-4 flex-shrink-0" style={{ color: '#30363D' }} />
                    )}
                    <span style={{ color: f.included ? '#FFFFFF' : '#8B949E' }}>
                      {f.name}
                    </span>
                  </li>
                ))}
              </ul>

              <Link
                to={plan.ctaLink}
                className="mt-8 block rounded-lg py-3 text-center text-sm font-semibold transition-opacity hover:opacity-90"
                style={
                  plan.outlined
                    ? {
                        border: '1px solid #00D4AA',
                        color: '#00D4AA',
                        backgroundColor: 'transparent',
                      }
                    : {
                        backgroundColor: '#00D4AA',
                        color: '#0D1117',
                      }
                }
                onClick={() => trackEvent("Plan Select", { plan: plan.name.toLowerCase() })}
              >
                {plan.cta}
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-2xl">
          <motion.h2
            className="text-3xl font-bold text-center mb-10"
            style={{ color: '#FFFFFF' }}
            {...fadeInUp}
          >
            Frequently asked questions
          </motion.h2>
          <motion.div
            className="rounded-xl p-6 md:p-8"
            style={{ backgroundColor: '#161B22', border: '1px solid #30363D' }}
            {...fadeInUp}
            transition={{ ...fadeInUp.transition, delay: 0.1 }}
          >
            {faqs.map((faq) => (
              <FAQItem key={faq.question} question={faq.question} answer={faq.answer} />
            ))}
          </motion.div>
        </div>
      </section>
    </PageLayout>
  )
}
