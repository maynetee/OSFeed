import { useState, useEffect } from 'react'
import { PageLayout } from './components/PageLayout'
import { Seo } from './components/Seo'

const sections = [
  { id: 'acceptance', title: 'Introduction & Acceptance of Terms' },
  { id: 'service', title: 'Description of Service' },
  { id: 'accounts', title: 'Account Registration & Security' },
  { id: 'payments', title: 'Subscription & Payment Terms' },
  { id: 'acceptable-use', title: 'Acceptable Use Policy' },
  { id: 'intellectual-property', title: 'Intellectual Property' },
  { id: 'warranties', title: 'Disclaimer of Warranties' },
  { id: 'liability', title: 'Limitation of Liability' },
  { id: 'termination', title: 'Termination' },
  { id: 'governing-law', title: 'Governing Law & Dispute Resolution' },
  { id: 'changes', title: 'Changes to Terms' },
  { id: 'contact', title: 'Contact Information' },
]

export function TermsPage() {
  const [activeSection, setActiveSection] = useState<string>('acceptance')
  const [isTocOpen, setIsTocOpen] = useState(false)

  useEffect(() => {
    const observers: IntersectionObserver[] = []

    sections.forEach(({ id }) => {
      const element = document.getElementById(id)
      if (!element) return

      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              setActiveSection(id)
            }
          })
        },
        { rootMargin: '-80px 0px -60% 0px', threshold: 0 },
      )

      observer.observe(element)
      observers.push(observer)
    })

    return () => {
      observers.forEach((observer) => observer.disconnect())
    }
  }, [])

  const handleTocClick = (id: string) => {
    const element = document.getElementById(id)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' })
      setIsTocOpen(false)
    }
  }

  const tocContent = (
    <nav className="space-y-1">
      {sections.map(({ id, title }) => (
        <button
          key={id}
          onClick={() => handleTocClick(id)}
          className="block w-full text-left px-3 py-2 text-sm rounded-md transition-colors"
          style={{
            color: activeSection === id ? '#00D4AA' : '#8B949E',
            backgroundColor: activeSection === id ? 'rgba(0, 212, 170, 0.1)' : 'transparent',
          }}
        >
          {title}
        </button>
      ))}
    </nav>
  )

  return (
    <PageLayout>
      <Seo
        title="Terms of Service — Osfeed"
        description="Read the Osfeed Terms of Service. Understand your rights and responsibilities when using our intelligence platform."
      />
      {/* Hero Section */}
      <section className="py-20 text-center">
        <div className="max-w-4xl mx-auto px-6">
          <h1 className="text-4xl md:text-5xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
            Terms of Service
          </h1>
          <p className="text-lg" style={{ color: '#8B949E' }}>
            Last updated: February 2026
          </p>
        </div>
      </section>

      {/* Warning Banner */}
      <div className="max-w-6xl mx-auto px-6 mb-10">
        <div
          className="rounded-lg px-6 py-4 text-sm"
          style={{
            backgroundColor: 'rgba(234, 179, 8, 0.1)',
            border: '1px solid rgba(234, 179, 8, 0.3)',
            color: '#EAB308',
          }}
        >
          <strong>Notice:</strong> These terms are provided as a template and should be reviewed by
          a qualified attorney before use in production.
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-6 pb-20">
        {/* Mobile TOC Toggle */}
        <div className="lg:hidden mb-8">
          <button
            onClick={() => setIsTocOpen(!isTocOpen)}
            className="w-full flex items-center justify-between px-4 py-3 rounded-lg text-sm font-medium"
            style={{
              backgroundColor: '#161B22',
              border: '1px solid #30363D',
              color: '#F3F4F6',
            }}
          >
            <span>Table of Contents</span>
            <svg
              className={`w-5 h-5 transition-transform ${isTocOpen ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
          {isTocOpen && (
            <div
              className="mt-2 rounded-lg p-4"
              style={{ backgroundColor: '#161B22', border: '1px solid #30363D' }}
            >
              {tocContent}
            </div>
          )}
        </div>

        <div className="flex gap-10">
          {/* Desktop Sidebar TOC */}
          <aside className="hidden lg:block w-64 flex-shrink-0">
            <div
              className="sticky top-20 max-h-[calc(100vh-8rem)] overflow-y-auto rounded-lg p-4"
              style={{ backgroundColor: '#161B22', border: '1px solid #30363D' }}
            >
              <h3 className="text-sm font-semibold mb-3" style={{ color: '#F3F4F6' }}>
                Table of Contents
              </h3>
              {tocContent}
            </div>
          </aside>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Section 1: Acceptance */}
            <section id="acceptance" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                1. Introduction & Acceptance of Terms
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  Welcome to OSFeed, an intelligence platform operated by OSFeed SAS, a company
                  incorporated under the laws of France (hereinafter referred to as "OSFeed," "we,"
                  "us," or "our"). These Terms of Service ("Terms") govern your access to and use of
                  the OSFeed platform, including our website, applications, APIs, and all related
                  services (collectively, the "Service").
                </p>
                <p>
                  By accessing or using the Service, you acknowledge that you have read, understood,
                  and agree to be bound by these Terms, as well as our Privacy Policy, which is
                  incorporated herein by reference. These Terms constitute a legally binding
                  agreement between you and OSFeed SAS.
                </p>
                <p>
                  If you are using the Service on behalf of an organization, you represent and
                  warrant that you have the authority to bind that organization to these Terms, and
                  references to "you" shall include both you individually and the organization you
                  represent.
                </p>
                <p>
                  If you do not agree with any part of these Terms, you must not access or use the
                  Service. Your continued use of the Service following the posting of any changes to
                  these Terms constitutes your acceptance of those changes.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 2: Service */}
            <section id="service" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                2. Description of Service
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  OSFeed is an open-source intelligence (OSINT) platform designed to help
                  professionals and organizations monitor, analyze, and understand publicly
                  available information. The Service provides the following core capabilities:
                </p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Source Aggregation:</strong> Collection and
                    aggregation of open-source information from publicly available channels,
                    including but not limited to Telegram channels, public forums, and other open
                    communication platforms.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>AI-Powered Translation:</strong> Automated
                    translation of multilingual content using artificial intelligence and large
                    language models to make information accessible across language barriers.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Intelligent Filtering & Analysis:</strong>{' '}
                    AI-driven noise reduction, content categorization, semantic deduplication, and
                    analytical tools to surface relevant information from large volumes of data.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Real-Time Alerts & Monitoring:</strong>{' '}
                    Configurable alert systems that notify users when specific conditions, keywords,
                    or patterns are detected in monitored sources.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Digest Generation:</strong> Automated
                    creation of daily and weekly intelligence summaries and reports tailored to
                    user-defined topics and interests.
                  </li>
                </ul>
                <p>
                  The Service is intended solely for the aggregation and analysis of publicly
                  available, open-source information. OSFeed does not provide access to classified,
                  proprietary, or otherwise restricted intelligence. We do not engage in
                  surveillance, hacking, or unauthorized access to private communications. All data
                  collected and processed by the Service is sourced from publicly accessible
                  channels.
                </p>
                <p>
                  The availability, features, and scope of the Service may change over time as we
                  continue to develop and improve the platform. We reserve the right to modify,
                  suspend, or discontinue any aspect of the Service at any time, with reasonable
                  notice to active subscribers where practicable.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 3: Accounts */}
            <section id="accounts" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                3. Account Registration & Security
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  To access certain features of the Service, you must create an account. You must be
                  at least 18 years of age to create an account and use the Service. By registering,
                  you represent and warrant that you meet this age requirement and that all
                  information you provide during registration is accurate, current, and complete.
                </p>
                <p>
                  You are responsible for maintaining the confidentiality and security of your
                  account credentials, including your password. You agree to choose a strong, unique
                  password and to not share your login credentials with any third party. You are
                  solely responsible for all activities that occur under your account, whether or
                  not authorized by you.
                </p>
                <p>
                  You must notify OSFeed immediately at{' '}
                  <span style={{ color: '#00D4AA' }}>hello@osfeed.com</span> if you become aware of
                  any unauthorized access to or use of your account, or any other breach of
                  security. OSFeed will not be liable for any loss or damage arising from your
                  failure to protect your account credentials.
                </p>
                <p>
                  Each individual is permitted to maintain only one account on the platform.
                  Creating multiple accounts to circumvent usage limits, access restrictions, or for
                  any other purpose is strictly prohibited and may result in the termination of all
                  associated accounts.
                </p>
                <p>
                  You agree to keep your account information up to date, including your email
                  address and billing information. Failure to maintain accurate account information
                  may result in your inability to access the Service or receive important
                  notifications regarding your account.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 4: Payments */}
            <section id="payments" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                4. Subscription & Payment Terms
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  OSFeed offers the following subscription plans, each designed to meet different
                  user needs:
                </p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Solo Plan — €99/month:</strong> Designed
                    for individual analysts and researchers, including core platform features, a
                    defined number of monitored sources, and standard support.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Team Plan — €399/month:</strong> Designed
                    for teams and small organizations, including collaborative features, increased
                    source limits, priority support, and shared workspaces.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Enterprise Plan — Custom Pricing:</strong>{' '}
                    Tailored solutions for large organizations with dedicated account management,
                    custom integrations, advanced security features, SLA guarantees, and
                    volume-based pricing. Contact our sales team for details.
                  </li>
                </ul>
                <p>
                  Annual billing is available for the Solo and Team plans at a 20% discount compared
                  to monthly billing. Annual subscriptions are billed in a single upfront payment
                  for the entire year.
                </p>
                <p>
                  All payments are securely processed through Stripe, our third-party payment
                  processor. By providing your payment information, you authorize OSFeed and Stripe
                  to charge your designated payment method for all fees associated with your
                  subscription. You are responsible for ensuring that your payment information
                  remains valid and current.
                </p>
                <p>
                  New subscribers are eligible for a 14-day money-back guarantee. If you are not
                  satisfied with the Service within the first 14 days of your initial subscription,
                  you may request a full refund by contacting our support team. This guarantee
                  applies only to first-time subscriptions and is not available for renewals or plan
                  upgrades.
                </p>
                <p>
                  Subscriptions automatically renew at the end of each billing cycle (monthly or
                  annually) unless cancelled before the renewal date. You may cancel your
                  subscription at any time through your account settings. Cancellation will take
                  effect at the end of the current billing period, and you will continue to have
                  access to the Service until that date.
                </p>
                <p>
                  OSFeed reserves the right to adjust subscription pricing. Any price changes will
                  be communicated to existing subscribers at least 30 days in advance via email.
                  Price changes will take effect at the start of the next billing cycle following
                  the notice period.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 5: Acceptable Use */}
            <section id="acceptable-use" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                5. Acceptable Use Policy
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  You agree to use the Service only for lawful purposes and in accordance with these
                  Terms. The following activities are expressly prohibited when using the Service:
                </p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Illegal Activities:</strong> Using the
                    Service to engage in, facilitate, or promote any activity that violates
                    applicable local, national, or international laws or regulations, including but
                    not limited to export control laws, sanctions regulations, and data protection
                    legislation.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Harassment & Threats:</strong> Using
                    information obtained through the Service to harass, threaten, stalk, intimidate,
                    or cause harm to any individual or organization. The Service is designed for
                    professional intelligence analysis, not for targeting individuals.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Reverse Engineering:</strong> Attempting to
                    reverse engineer, decompile, disassemble, or otherwise derive the source code,
                    algorithms, or underlying structure of the Service or any component thereof.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Automated Scraping:</strong> Using bots,
                    scrapers, crawlers, or any automated means to access, extract, or collect data
                    from the OSFeed platform itself, beyond what is permitted through our official
                    APIs.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Credential Sharing:</strong> Sharing,
                    transferring, or disclosing your account credentials to any third party, or
                    allowing multiple individuals to use a single account (except as permitted under
                    Team or Enterprise plans).
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Security Circumvention:</strong> Attempting
                    to circumvent, disable, or interfere with any security features, access
                    controls, or usage limitations of the Service, including rate limiting,
                    authentication mechanisms, or encryption.
                  </li>
                </ul>
                <p>
                  OSFeed reserves the right to investigate any suspected violations of this
                  Acceptable Use Policy. If we determine, in our sole discretion, that a violation
                  has occurred, we may take appropriate action, including but not limited to issuing
                  warnings, temporarily suspending access, permanently terminating accounts, and
                  reporting illegal activities to relevant authorities.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 6: Intellectual Property */}
            <section id="intellectual-property" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                6. Intellectual Property
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  The OSFeed platform, including but not limited to its software, design, user
                  interface, logos, trademarks, documentation, and all underlying technology, is the
                  exclusive property of OSFeed SAS and is protected by applicable intellectual
                  property laws, including copyright, trademark, and trade secret laws of France and
                  international treaties.
                </p>
                <p>
                  Content aggregated and displayed through the Service originates from publicly
                  available third-party sources. Such content remains the intellectual property of
                  its original authors and publishers. OSFeed does not claim ownership of
                  third-party content and provides it under applicable fair use, fair dealing, or
                  other legal provisions that permit aggregation and analysis of publicly available
                  information.
                </p>
                <p>
                  You retain full ownership and intellectual property rights to any reports,
                  exports, analyses, or other original works that you create using the Service.
                  OSFeed claims no ownership over user-generated content. However, by using the
                  Service, you grant OSFeed a limited, non-exclusive license to process and store
                  your data as necessary to provide the Service to you.
                </p>
                <p>
                  You may not reproduce, distribute, modify, or create derivative works based on the
                  OSFeed platform, branding, or proprietary technology without prior written
                  permission from OSFeed SAS. This includes but is not limited to the use of OSFeed
                  logos, trademarks, and brand elements in any medium or context.
                </p>
                <p>
                  If you believe that any content on the Service infringes upon your intellectual
                  property rights, please contact us at{' '}
                  <span style={{ color: '#00D4AA' }}>legal@osfeed.com</span> with a detailed
                  description of the alleged infringement, and we will investigate and respond in
                  accordance with applicable law.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 7: Warranties */}
            <section id="warranties" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                7. Disclaimer of Warranties
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  THE SERVICE IS PROVIDED ON AN "AS IS" AND "AS AVAILABLE" BASIS, WITHOUT WARRANTIES
                  OF ANY KIND, EITHER EXPRESS OR IMPLIED. TO THE FULLEST EXTENT PERMITTED BY
                  APPLICABLE LAW, OSFEED SAS DISCLAIMS ALL WARRANTIES, INCLUDING BUT NOT LIMITED TO
                  IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
                  NON-INFRINGEMENT, AND ANY WARRANTIES ARISING OUT OF COURSE OF DEALING OR USAGE OF
                  TRADE.
                </p>
                <p>
                  OSFeed does not warrant or guarantee the accuracy, completeness, reliability, or
                  timeliness of any content aggregated, translated, or displayed through the
                  Service. Information sourced from third-party channels may be inaccurate,
                  incomplete, outdated, or misleading. Users are responsible for independently
                  verifying any information obtained through the Service before relying on it for
                  decision-making purposes.
                </p>
                <p>
                  AI-powered translations and analyses provided by the Service are generated by
                  automated systems and may contain errors, inaccuracies, or omissions. Machine
                  translations should not be treated as authoritative and may not capture the full
                  nuance, context, or meaning of the original content. For critical decisions, we
                  recommend consulting qualified human translators or subject matter experts.
                </p>
                <p>
                  OSFeed does not warrant that the Service will be uninterrupted, error-free,
                  secure, or free from viruses or other harmful components. While we strive to
                  maintain high availability and reliability, downtime may occur due to maintenance,
                  updates, technical issues, or circumstances beyond our control. We will make
                  commercially reasonable efforts to notify users of planned maintenance in advance.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 8: Liability */}
            <section id="liability" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                8. Limitation of Liability
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL OSFEED SAS,
                  ITS DIRECTORS, OFFICERS, EMPLOYEES, AGENTS, OR AFFILIATES BE LIABLE FOR ANY
                  INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, PUNITIVE, OR EXEMPLARY DAMAGES,
                  INCLUDING BUT NOT LIMITED TO DAMAGES FOR LOSS OF PROFITS, REVENUE, DATA, GOODWILL,
                  BUSINESS OPPORTUNITIES, OR OTHER INTANGIBLE LOSSES, ARISING OUT OF OR IN
                  CONNECTION WITH YOUR USE OF OR INABILITY TO USE THE SERVICE, REGARDLESS OF THE
                  THEORY OF LIABILITY (CONTRACT, TORT, NEGLIGENCE, STRICT LIABILITY, OR OTHERWISE)
                  AND EVEN IF OSFEED HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
                </p>
                <p>
                  In no event shall OSFeed's total cumulative liability to you for all claims
                  arising out of or related to these Terms or your use of the Service exceed the
                  total amount paid by you to OSFeed during the twelve (12) months immediately
                  preceding the event giving rise to the claim. If you have not made any payments to
                  OSFeed, our maximum aggregate liability shall not exceed one hundred euros (€100).
                </p>
                <p>
                  OSFeed shall not be held responsible for any actions, decisions, investments, or
                  other activities undertaken by you or any third party based on information
                  obtained through the Service. You acknowledge that the Service provides aggregated
                  open-source intelligence for informational purposes only, and that you bear sole
                  responsibility for how you interpret and act upon such information.
                </p>
                <p>
                  Some jurisdictions do not allow the exclusion or limitation of certain warranties
                  or liabilities. In such jurisdictions, the limitations set forth in this section
                  shall apply to the fullest extent permitted by applicable law. Nothing in these
                  Terms shall limit or exclude liability for death or personal injury resulting from
                  negligence, for fraud or fraudulent misrepresentation, or for any other liability
                  that cannot be lawfully excluded or limited.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 9: Termination */}
            <section id="termination" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                9. Termination
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  You may cancel your subscription and terminate your account at any time through
                  your account settings or by contacting our support team at{' '}
                  <span style={{ color: '#00D4AA' }}>hello@osfeed.com</span>. Upon cancellation,
                  your subscription will remain active until the end of the current billing period,
                  after which your access to paid features will cease.
                </p>
                <p>
                  OSFeed reserves the right to suspend or terminate your account, with or without
                  prior notice, if we reasonably believe that you have violated these Terms, engaged
                  in fraudulent or illegal activity, or otherwise acted in a manner that could harm
                  OSFeed, other users, or third parties. In cases of severe violations, termination
                  may be immediate and without prior warning.
                </p>
                <p>
                  Upon termination of your account, whether initiated by you or by OSFeed, your
                  right to access and use the Service will cease immediately. You will no longer be
                  able to log in, access your dashboards, or retrieve data through the platform. Any
                  pending or unused subscription time will be handled in accordance with our refund
                  policy as described in the Subscription & Payment Terms section.
                </p>
                <p>
                  Following termination, OSFeed will retain and handle your data in accordance with
                  our Privacy Policy. We may retain certain information as required by law, for
                  legitimate business purposes, or to resolve disputes. You may request deletion of
                  your personal data in accordance with applicable data protection laws by
                  contacting us at <span style={{ color: '#00D4AA' }}>legal@osfeed.com</span>.
                </p>
                <p>
                  The following sections of these Terms shall survive termination: Intellectual
                  Property, Disclaimer of Warranties, Limitation of Liability, Governing Law &
                  Dispute Resolution, and any other provisions that by their nature should
                  reasonably survive termination.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 10: Governing Law */}
            <section id="governing-law" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                10. Governing Law & Dispute Resolution
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  These Terms shall be governed by and construed in accordance with the laws of the
                  French Republic, without regard to its conflict of law principles. Any legal
                  action or proceeding arising out of or relating to these Terms or your use of the
                  Service shall be subject to the exclusive jurisdiction of the competent courts of
                  Paris, France.
                </p>
                <p>
                  In the event of a dispute arising out of or relating to these Terms, the parties
                  agree to first attempt to resolve the matter through good faith negotiation.
                  Either party may initiate the negotiation process by sending a written notice to
                  the other party describing the nature of the dispute and the relief sought. The
                  parties shall use commercially reasonable efforts to resolve the dispute within
                  thirty (30) days of such notice.
                </p>
                <p>
                  If the dispute cannot be resolved through negotiation within the specified period,
                  either party may pursue formal legal proceedings before the competent courts of
                  Paris, France, as stated above.
                </p>
                <p>
                  If you are a consumer residing in the European Union, you may also be entitled to
                  submit disputes to the European Commission's Online Dispute Resolution (ODR)
                  platform, accessible at{' '}
                  <span style={{ color: '#00D4AA' }}>https://ec.europa.eu/consumers/odr</span>. The
                  ODR platform provides an out-of-court mechanism for resolving disputes between
                  consumers and businesses regarding online purchases. Nothing in these Terms shall
                  affect your statutory rights as an EU consumer.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 11: Changes */}
            <section id="changes" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                11. Changes to Terms
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  OSFeed reserves the right to modify, update, or replace these Terms at any time at
                  our sole discretion. Changes may be made to reflect updates to the Service,
                  changes in applicable law, or for other operational or legal reasons.
                </p>
                <p>
                  For material changes that significantly affect your rights or obligations, we will
                  provide notice at least thirty (30) days in advance through one or more of the
                  following methods: email notification to the address associated with your account,
                  a prominent notice on the OSFeed platform, or a notification within your account
                  dashboard. The revised Terms will indicate the date of the most recent update at
                  the top of this page.
                </p>
                <p>
                  Your continued use of the Service after the effective date of any revised Terms
                  constitutes your acceptance of and agreement to the updated Terms. If you do not
                  agree with the revised Terms, you must stop using the Service and may cancel your
                  subscription in accordance with the Termination section of these Terms.
                </p>
                <p>
                  We encourage you to periodically review these Terms to stay informed about the
                  conditions governing your use of the Service. Archived versions of previous Terms
                  may be made available upon request.
                </p>
              </div>
            </section>

            <div style={{ borderBottom: '1px solid #30363D' }} />

            {/* Section 12: Contact */}
            <section id="contact" className="py-8">
              <h2 className="text-2xl font-bold mb-6" style={{ color: '#F3F4F6' }}>
                12. Contact Information
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  If you have any questions, concerns, or feedback regarding these Terms of Service
                  or the OSFeed platform, please do not hesitate to contact us using the information
                  below:
                </p>
                <div
                  className="rounded-lg p-6 space-y-3"
                  style={{ backgroundColor: '#161B22', border: '1px solid #30363D' }}
                >
                  <p>
                    <strong style={{ color: '#F3F4F6' }}>Company:</strong> OSFeed SAS
                  </p>
                  <p>
                    <strong style={{ color: '#F3F4F6' }}>General Inquiries:</strong>{' '}
                    <span style={{ color: '#00D4AA' }}>hello@osfeed.com</span>
                  </p>
                  <p>
                    <strong style={{ color: '#F3F4F6' }}>Legal Inquiries:</strong>{' '}
                    <span style={{ color: '#00D4AA' }}>legal@osfeed.com</span>
                  </p>
                </div>
                <p>
                  We aim to respond to all inquiries within five (5) business days. For urgent
                  matters related to account security or unauthorized access, please include
                  "URGENT" in the subject line of your email to help us prioritize your request.
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </PageLayout>
  )
}
