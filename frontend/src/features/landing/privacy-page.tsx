import { useState, useEffect } from 'react'
import { PageLayout } from './components/PageLayout'
import { Seo } from './components/Seo'

const sections = [
  { id: 'introduction', label: 'Introduction' },
  { id: 'collection', label: 'Information We Collect' },
  { id: 'use', label: 'How We Use Your Information' },
  { id: 'sharing', label: 'Information Sharing & Disclosure' },
  { id: 'retention', label: 'Data Retention' },
  { id: 'rights', label: 'Your Rights (GDPR)' },
  { id: 'cookies', label: 'Cookies & Tracking' },
  { id: 'security', label: 'Security' },
  { id: 'transfers', label: 'International Transfers' },
  { id: 'children', label: "Children's Privacy" },
  { id: 'changes', label: 'Changes to This Policy' },
  { id: 'contact', label: 'Contact Us' },
]

export function PrivacyPage() {
  const [activeSection, setActiveSection] = useState('introduction')
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const observers: IntersectionObserver[] = []

    sections.forEach(({ id }) => {
      const el = document.getElementById(id)
      if (!el) return

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setActiveSection(id)
          }
        },
        { rootMargin: '-80px 0px -60% 0px', threshold: 0.1 },
      )

      observer.observe(el)
      observers.push(observer)
    })

    return () => observers.forEach((o) => o.disconnect())
  }, [])

  const scrollToSection = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setMobileMenuOpen(false)
    }
  }

  const TOCLinks = (
    <nav className="space-y-1">
      {sections.map(({ id, label }) => (
        <button
          key={id}
          onClick={() => scrollToSection(id)}
          className="block w-full text-left px-3 py-2 rounded-md text-sm transition-colors"
          style={{
            color: activeSection === id ? '#00D4AA' : '#8B949E',
            backgroundColor: activeSection === id ? 'rgba(0, 212, 170, 0.08)' : 'transparent',
          }}
        >
          {label}
        </button>
      ))}
    </nav>
  )

  return (
    <PageLayout>
      <Seo
        title="Privacy Policy — Osfeed"
        description="Learn how Osfeed collects, uses, and protects your personal data. GDPR compliant privacy policy."
      />
      {/* Hero */}
      <section className="py-16 text-center">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">Privacy Policy</h1>
        <p className="text-lg" style={{ color: '#8B949E' }}>
          Last updated: February 2026
        </p>
      </section>

      {/* Warning Banner */}
      <div className="max-w-5xl mx-auto px-4 mb-10">
        <div
          className="rounded-lg border px-6 py-4 text-sm"
          style={{
            backgroundColor: 'rgba(234, 179, 8, 0.08)',
            borderColor: 'rgba(234, 179, 8, 0.3)',
            color: '#EAB308',
          }}
        >
          <strong>Notice:</strong> This privacy policy is provided as a template and should be
          reviewed by a qualified attorney before use in production.
        </div>
      </div>

      {/* Mobile TOC Toggle */}
      <div className="lg:hidden max-w-5xl mx-auto px-4 mb-6">
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="w-full flex items-center justify-between rounded-lg border px-4 py-3 text-sm font-medium"
          style={{ backgroundColor: '#161B22', borderColor: '#30363D', color: '#F3F4F6' }}
        >
          <span>Table of Contents</span>
          <svg
            className={`w-4 h-4 transition-transform ${mobileMenuOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {mobileMenuOpen && (
          <div
            className="mt-2 rounded-lg border p-4"
            style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
          >
            {TOCLinks}
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-4 pb-20">
        <div className="lg:flex lg:gap-10">
          {/* Desktop Sidebar */}
          <aside className="hidden lg:block lg:w-64 flex-shrink-0">
            <div
              className="sticky top-20 max-h-[calc(100vh-8rem)] overflow-y-auto rounded-lg border p-4"
              style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
            >
              <h3 className="text-sm font-semibold mb-3" style={{ color: '#F3F4F6' }}>
                Table of Contents
              </h3>
              {TOCLinks}
            </div>
          </aside>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* 1. Introduction */}
            <section id="introduction" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                1. Introduction
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  OSFeed SAS (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;) operates the
                  osfeed.com platform and related services (collectively, the &quot;Service&quot;).
                  We are committed to protecting your privacy and ensuring the security of your
                  personal data. This Privacy Policy explains how we collect, use, disclose, and
                  safeguard your information when you use our Service.
                </p>
                <p>
                  OSFeed SAS, registered in France, acts as the data controller for the personal
                  data processed through our platform. This means we determine the purposes and
                  means of processing your personal data and are responsible for compliance with
                  applicable data protection laws, including the General Data Protection Regulation
                  (EU) 2016/679 (&quot;GDPR&quot;) and the French Data Protection Act (Loi
                  Informatique et Libert&eacute;s).
                </p>
                <p>
                  This Privacy Policy applies to all users of our platform, including visitors to
                  our website, registered account holders, trial users, and paying subscribers. By
                  accessing or using our Service, you acknowledge that you have read and understood
                  this Privacy Policy. If you do not agree with our practices described herein,
                  please do not use our Service.
                </p>
              </div>
            </section>

            {/* 2. Information We Collect */}
            <section id="collection" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                2. Information We Collect
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  We collect information that you provide directly to us, as well as information
                  that is generated automatically when you use our Service. The categories of
                  personal data we process include:
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Account Data
                </h3>
                <p>
                  When you create an account, we collect your username, email address, hashed
                  password, and country of residence. Your password is never stored in plain text;
                  it is cryptographically hashed using bcrypt before storage, and we cannot retrieve
                  your original password.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Payment Data
                </h3>
                <p>
                  Payment processing is handled entirely by our third-party payment processor,
                  Stripe. When you subscribe to a paid plan, your payment details (credit card
                  number, expiration date, CVC) are collected and processed directly by Stripe. We
                  do not store, process, or have access to your full credit card numbers. We receive
                  only a limited set of information from Stripe, such as the last four digits of
                  your card, card brand, expiration date, and billing country, for the purpose of
                  displaying payment information in your account settings.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Usage Data
                </h3>
                <p>
                  We automatically collect certain information when you access or use our Service,
                  including server logs, your IP address, browser type and version, operating
                  system, referring URL, pages visited within our platform, features used,
                  interaction timestamps, and session duration. This data helps us understand how
                  our Service is used and identify areas for improvement.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Newsletter Data
                </h3>
                <p>
                  If you subscribe to our newsletter, we collect your email address. Newsletter
                  subscription is entirely optional and is not required to use our Service. You can
                  unsubscribe at any time using the link provided in each newsletter email.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Communications
                </h3>
                <p>
                  When you contact us via email or through our contact forms, we collect the content
                  of your messages, your email address, and any other information you choose to
                  provide. We retain these communications to respond to your inquiries and improve
                  our services.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Legal Basis for Processing
                </h3>
                <p>
                  Under the GDPR, we process your personal data on the following legal bases: (a)
                  contract performance — processing necessary to provide you with our Service and
                  fulfill our contractual obligations; (b) legitimate interests — processing
                  necessary for our legitimate business interests, such as fraud prevention,
                  security, and service improvement, provided these interests are not overridden by
                  your rights; and (c) consent — for optional processing activities such as
                  newsletter subscriptions and marketing communications, which you may withdraw at
                  any time.
                </p>
              </div>
            </section>

            {/* 3. How We Use Your Information */}
            <section id="use" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                3. How We Use Your Information
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>We use the information we collect for the following purposes:</p>
                <ul className="list-disc pl-6 space-y-3">
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>
                      Provide, maintain, and improve our services:
                    </strong>{' '}
                    We use your data to operate the OSFeed platform, deliver the features you
                    request, and continuously improve the quality and reliability of our Service.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>
                      Process subscriptions and payments:
                    </strong>{' '}
                    We use your account and payment-related information to manage your subscription,
                    process transactions through Stripe, and provide billing support.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>
                      Send service-related communications:
                    </strong>{' '}
                    We may send you transactional emails related to your account, such as
                    registration confirmations, password reset instructions, subscription changes,
                    and important service updates or security notices.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Send marketing communications:</strong>{' '}
                    With your explicit consent, we may send you promotional emails about new
                    features, product updates, and special offers. You can opt out of marketing
                    communications at any time by clicking the unsubscribe link in any marketing
                    email or by updating your preferences in your account settings.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>
                      Monitor and analyze usage patterns:
                    </strong>{' '}
                    We analyze aggregated usage data to understand how users interact with our
                    platform, identify trends, and make data-driven decisions about product
                    development and feature prioritization.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Detect and prevent fraud or abuse:</strong>{' '}
                    We use technical and behavioral data to identify and prevent unauthorized
                    access, fraudulent activity, abuse of our Service, and violations of our Terms
                    of Service.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Comply with legal obligations:</strong> We
                    process certain data as required by applicable laws, regulations, or legal
                    proceedings, including tax and accounting requirements and responses to lawful
                    requests from public authorities.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Personalize your experience:</strong> We
                    may use your usage patterns and preferences to customize the content and
                    features presented to you within the platform, ensuring a more relevant and
                    efficient experience.
                  </li>
                </ul>
              </div>
            </section>

            {/* 4. Information Sharing & Disclosure */}
            <section id="sharing" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                4. Information Sharing & Disclosure
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  We value your privacy and are committed to limiting the disclosure of your
                  personal information. We do not sell, rent, or trade your personal data to third
                  parties for their marketing purposes. We may share your information in the
                  following limited circumstances:
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Service Providers
                </h3>
                <p>
                  We share data with trusted third-party service providers who assist us in
                  operating our platform. These include Stripe for payment processing, email service
                  providers for transactional and marketing emails, and cloud hosting providers for
                  infrastructure. All service providers are contractually bound to process your data
                  only on our behalf and in accordance with our instructions, and they are required
                  to implement appropriate security measures.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Legal Requirements
                </h3>
                <p>
                  We may disclose your personal data if required to do so by law, in response to a
                  valid court order, subpoena, or request from a governmental authority with
                  jurisdiction, or where disclosure is necessary to protect our legal rights,
                  enforce our Terms of Service, or ensure the safety of our users.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Business Transfers
                </h3>
                <p>
                  In the event of a merger, acquisition, reorganization, bankruptcy, or sale of all
                  or a portion of our assets, your personal data may be transferred as part of that
                  transaction. We will notify you via email and/or a prominent notice on our
                  platform of any change in ownership or uses of your personal data, as well as any
                  choices you may have regarding your data.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  With Your Consent
                </h3>
                <p>
                  We may share your personal data with third parties when you have given us your
                  explicit consent to do so, for a specific purpose that has been clearly
                  communicated to you.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Aggregated and Anonymized Data
                </h3>
                <p>
                  We may share aggregated, de-identified, or anonymized data that cannot reasonably
                  be used to identify you for purposes such as industry analysis, benchmarking, and
                  platform usage analytics. This data does not constitute personal data under the
                  GDPR.
                </p>
              </div>
            </section>

            {/* 5. Data Retention */}
            <section id="retention" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                5. Data Retention
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  We retain your personal data only for as long as necessary to fulfill the purposes
                  for which it was collected, comply with our legal obligations, resolve disputes,
                  and enforce our agreements. The specific retention periods are as follows:
                </p>
                <ul className="list-disc pl-6 space-y-3">
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Account data:</strong> Retained for the
                    duration of your active account plus 30 days following account deletion. This
                    grace period allows you to reactivate your account if the deletion was
                    unintentional.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Payment records:</strong> Retained for 7
                    years from the date of the transaction, as required by French commercial and tax
                    law (Code de commerce, Article L123-22).
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Usage logs:</strong> Retained for 12 months
                    from the date of collection, after which they are automatically purged from our
                    systems.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Newsletter data:</strong> Retained until
                    you unsubscribe from our newsletter. Upon unsubscription, your email address is
                    removed from our marketing lists within 48 hours.
                  </li>
                </ul>
                <p>
                  We conduct regular reviews of the data we hold and securely delete or anonymize
                  personal data that is no longer necessary for the purposes outlined in this
                  Privacy Policy. When data is deleted, it is removed from our active systems and
                  backups within a reasonable timeframe consistent with our backup rotation
                  schedule.
                </p>
              </div>
            </section>

            {/* 6. Your Rights (GDPR) */}
            <section id="rights" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                6. Your Rights (GDPR)
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  Under the General Data Protection Regulation and applicable French data protection
                  law, you have the following rights regarding your personal data:
                </p>
                <ul className="list-disc pl-6 space-y-3">
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Right of access:</strong> You have the
                    right to request a copy of the personal data we hold about you, together with
                    information about how and why we process it. We will provide this information in
                    a commonly used, machine-readable electronic format.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Right to rectification:</strong> You have
                    the right to request that we correct any inaccurate personal data we hold about
                    you, and to have incomplete data completed.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>
                      Right to erasure (&quot;right to be forgotten&quot;):
                    </strong>{' '}
                    You have the right to request the deletion of your personal data where there is
                    no compelling reason for us to continue processing it, subject to certain legal
                    exceptions such as compliance with legal obligations or the establishment,
                    exercise, or defense of legal claims.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>
                      Right to restriction of processing:
                    </strong>{' '}
                    You have the right to request that we limit the processing of your personal data
                    in certain circumstances, such as when you contest the accuracy of the data or
                    when you have objected to processing pending verification of our legitimate
                    grounds.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Right to data portability:</strong> You
                    have the right to receive the personal data you have provided to us in a
                    structured, commonly used, and machine-readable format (such as JSON or CSV),
                    and to transmit that data to another controller without hindrance from us.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Right to object:</strong> You have the
                    right to object to the processing of your personal data where we rely on
                    legitimate interests as our legal basis, including profiling based on those
                    interests. We will cease processing unless we can demonstrate compelling
                    legitimate grounds that override your interests, rights, and freedoms.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Right to withdraw consent:</strong> Where
                    processing is based on your consent, you have the right to withdraw that consent
                    at any time. Withdrawal of consent does not affect the lawfulness of processing
                    carried out before the withdrawal.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Right to lodge a complaint:</strong> You
                    have the right to lodge a complaint with a supervisory authority. For users in
                    France, the competent authority is the Commission Nationale de
                    l&apos;Informatique et des Libert&eacute;s (CNIL). You may also contact the
                    supervisory authority in your country of residence.
                  </li>
                </ul>
                <p>
                  To exercise any of these rights, please contact us at{' '}
                  <a href="mailto:privacy@osfeed.com" style={{ color: '#00D4AA' }}>
                    privacy@osfeed.com
                  </a>
                  . We will respond to your request within 30 days of receipt. If we require
                  additional time due to the complexity or volume of requests, we will inform you of
                  the extension within the initial 30-day period and provide the reasons for the
                  delay. We may request verification of your identity before processing your request
                  to ensure the security of your personal data.
                </p>
              </div>
            </section>

            {/* 7. Cookies & Tracking */}
            <section id="cookies" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                7. Cookies & Tracking
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  Our platform uses cookies and similar tracking technologies to enhance your
                  experience and collect information about how our Service is used. Cookies are
                  small text files stored on your device by your web browser.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Essential Cookies
                </h3>
                <p>
                  These cookies are strictly necessary for the operation of our platform. They
                  enable core functionality such as user authentication, session management, and
                  security features. Without these cookies, our Service cannot function properly.
                  Essential cookies do not require your consent under the GDPR, as they are
                  necessary for the provision of the Service you have requested.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Analytics Cookies
                </h3>
                <p>
                  We use analytics cookies to collect aggregated information about how visitors
                  interact with our platform, including pages visited, time spent on each page, and
                  navigation patterns. This data helps us understand usage trends and improve our
                  Service. Analytics cookies are placed only with your consent, and you can opt out
                  at any time through our cookie consent settings or your browser preferences.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Third-Party Advertising Cookies
                </h3>
                <p>
                  We do not use third-party advertising cookies. We do not serve advertisements on
                  our platform, and we do not allow third-party advertisers to place cookies on your
                  device through our Service.
                </p>
                <h3 className="text-lg font-semibold mt-6 mb-2" style={{ color: '#F3F4F6' }}>
                  Managing Your Cookie Preferences
                </h3>
                <p>
                  You can manage your cookie preferences through our cookie consent banner, which is
                  displayed upon your first visit to our platform. Additionally, most web browsers
                  allow you to control cookies through their settings. You can typically set your
                  browser to refuse all cookies, accept only certain cookies, or notify you when a
                  cookie is set. Please note that disabling essential cookies may impair the
                  functionality of our Service.
                </p>
              </div>
            </section>

            {/* 8. Security */}
            <section id="security" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                8. Security
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  We take the security of your personal data seriously and implement appropriate
                  technical and organizational measures to protect it against unauthorized access,
                  alteration, disclosure, or destruction. Our security practices include:
                </p>
                <ul className="list-disc pl-6 space-y-3">
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Encryption in transit:</strong> All data
                    transmitted between your browser and our servers is encrypted using Transport
                    Layer Security (TLS/SSL) protocols, ensuring that your information cannot be
                    intercepted during transmission.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Encryption at rest:</strong> Sensitive data
                    stored in our databases is encrypted at rest using industry-standard encryption
                    algorithms, providing an additional layer of protection against unauthorized
                    access.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Password hashing:</strong> User passwords
                    are hashed using the bcrypt algorithm with appropriate salt rounds before
                    storage. We never store passwords in plain text and cannot retrieve your
                    original password.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Regular security audits:</strong> We
                    conduct periodic security assessments and code reviews to identify and address
                    potential vulnerabilities in our systems and applications.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Access controls and monitoring:</strong>{' '}
                    Access to personal data is restricted to authorized personnel on a need-to-know
                    basis. We maintain audit logs of data access and monitor our systems for
                    suspicious activity.
                  </li>
                </ul>
                <p>
                  While we strive to protect your personal data, no method of electronic
                  transmission or storage is 100% secure. We cannot guarantee absolute security, but
                  we are committed to promptly addressing any security incidents in accordance with
                  applicable laws and regulations.
                </p>
                <p>
                  If you discover a security vulnerability in our platform, we encourage responsible
                  disclosure. Please report any security concerns to{' '}
                  <a href="mailto:security@osfeed.com" style={{ color: '#00D4AA' }}>
                    security@osfeed.com
                  </a>
                  . We appreciate your help in keeping our platform safe and will acknowledge
                  receipt of your report within 48 hours.
                </p>
              </div>
            </section>

            {/* 9. International Transfers */}
            <section id="transfers" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                9. International Transfers
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  Your personal data is primarily stored and processed within the European Union.
                  However, some of our third-party service providers may process data in countries
                  outside the EU/European Economic Area (EEA), which may not provide the same level
                  of data protection as the EU.
                </p>
                <p>
                  When we transfer personal data outside the EU/EEA, we ensure that appropriate
                  safeguards are in place to protect your data in accordance with the GDPR. These
                  safeguards include:
                </p>
                <ul className="list-disc pl-6 space-y-3">
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>
                      Standard Contractual Clauses (SCCs):
                    </strong>{' '}
                    We enter into the European Commission&apos;s Standard Contractual Clauses with
                    service providers located outside the EU/EEA, ensuring that they provide
                    adequate protection for your personal data.
                  </li>
                  <li>
                    <strong style={{ color: '#F3F4F6' }}>Adequacy decisions:</strong> Where
                    available, we rely on adequacy decisions issued by the European Commission,
                    which recognize that certain countries provide an adequate level of data
                    protection comparable to that of the EU.
                  </li>
                </ul>
                <p>
                  We will inform you of any material changes to the countries in which your personal
                  data is processed or the safeguards we employ for international transfers. You may
                  contact us at any time to request further information about the specific
                  safeguards applied to international transfers of your data.
                </p>
              </div>
            </section>

            {/* 10. Children's Privacy */}
            <section id="children" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                10. Children&apos;s Privacy
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  Our Service is not directed at individuals under the age of 18, and we do not
                  knowingly collect personal data from minors. We do not specifically market to or
                  target children, and our platform is designed for use by adults and professionals.
                </p>
                <p>
                  If we become aware that we have inadvertently collected personal data from a
                  person under the age of 18 without appropriate parental or guardian consent, we
                  will take prompt steps to delete such data from our systems. If you are a parent
                  or guardian and believe that your child has provided personal data to us, please
                  contact us immediately at{' '}
                  <a href="mailto:privacy@osfeed.com" style={{ color: '#00D4AA' }}>
                    privacy@osfeed.com
                  </a>{' '}
                  so that we can take the necessary action.
                </p>
              </div>
            </section>

            {/* 11. Changes to This Policy */}
            <section id="changes" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                11. Changes to This Policy
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  We may update this Privacy Policy from time to time to reflect changes in our
                  practices, technologies, legal requirements, or other factors. When we make
                  changes, we will update the &quot;Last updated&quot; date at the top of this page.
                </p>
                <p>
                  For material changes that significantly affect how we process your personal data
                  or your rights, we will provide prominent notice through one or more of the
                  following methods: an email notification to the address associated with your
                  account, a prominent banner or notice on our platform, or a direct in-app
                  notification. We encourage you to review this Privacy Policy periodically to stay
                  informed about how we protect your data.
                </p>
                <p>
                  Your continued use of our Service after any changes to this Privacy Policy
                  constitutes your acceptance of the updated terms. If you do not agree with the
                  revised Privacy Policy, you should discontinue your use of the Service and may
                  request deletion of your account and associated data. Previous versions of this
                  Privacy Policy are available upon request by contacting us at{' '}
                  <a href="mailto:privacy@osfeed.com" style={{ color: '#00D4AA' }}>
                    privacy@osfeed.com
                  </a>
                  .
                </p>
              </div>
            </section>

            {/* 12. Contact Us */}
            <section id="contact" className="py-8">
              <h2 className="text-2xl font-bold mb-4" style={{ color: '#F3F4F6' }}>
                12. Contact Us
              </h2>
              <div className="space-y-4 text-base leading-relaxed" style={{ color: '#8B949E' }}>
                <p>
                  If you have any questions, concerns, or requests regarding this Privacy Policy or
                  our data processing practices, please do not hesitate to contact us using the
                  information below:
                </p>
                <div
                  className="rounded-lg border p-6 mt-4 space-y-3"
                  style={{ backgroundColor: '#161B22', borderColor: '#30363D' }}
                >
                  <div>
                    <span className="font-semibold" style={{ color: '#F3F4F6' }}>
                      General inquiries:{' '}
                    </span>
                    <a href="mailto:hello@osfeed.com" style={{ color: '#00D4AA' }}>
                      hello@osfeed.com
                    </a>
                  </div>
                  <div>
                    <span className="font-semibold" style={{ color: '#F3F4F6' }}>
                      Privacy inquiries:{' '}
                    </span>
                    <a href="mailto:privacy@osfeed.com" style={{ color: '#00D4AA' }}>
                      privacy@osfeed.com
                    </a>
                  </div>
                  <div>
                    <span className="font-semibold" style={{ color: '#F3F4F6' }}>
                      Data Protection Officer:{' '}
                    </span>
                    <a href="mailto:dpo@osfeed.com" style={{ color: '#00D4AA' }}>
                      dpo@osfeed.com
                    </a>
                  </div>
                  <div>
                    <span className="font-semibold" style={{ color: '#F3F4F6' }}>
                      Company:{' '}
                    </span>
                    OSFeed SAS, France
                  </div>
                  <div>
                    <span className="font-semibold" style={{ color: '#F3F4F6' }}>
                      Supervisory Authority:{' '}
                    </span>
                    CNIL (Commission Nationale de l&apos;Informatique et des Libert&eacute;s) —{' '}
                    <a
                      href="https://www.cnil.fr"
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ color: '#00D4AA' }}
                    >
                      www.cnil.fr
                    </a>
                  </div>
                </div>
                <p className="mt-4">
                  We are committed to resolving any concerns you may have about your privacy and our
                  data practices. If you are not satisfied with our response, you have the right to
                  lodge a complaint with the CNIL or your local data protection supervisory
                  authority.
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </PageLayout>
  )
}
