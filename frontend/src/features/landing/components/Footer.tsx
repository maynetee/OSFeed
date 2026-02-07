import { useState } from 'react'
import { Link } from 'react-router-dom'
import { trackEvent } from '@/lib/analytics'
import { api } from '@/lib/api/axios-instance'

const productLinks = [
  { label: 'How It Works', to: '/how-it-works' },
  { label: 'Pricing', to: '/pricing' },
  { label: 'Resources', to: '/resources' },
]

const companyLinks = [
  { label: 'Contact', to: '/contact' },
  { label: 'Terms', to: '/terms' },
  { label: 'Privacy', to: '/privacy' },
]

export default function Footer() {
  const [nlEmail, setNlEmail] = useState('')
  const [nlStatus, setNlStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')

  const handleNewsletterSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!nlEmail.trim()) return
    setNlStatus('loading')
    trackEvent('Newsletter Subscribe')
    try {
      await api.post('/api/newsletter/subscribe', { email: nlEmail })
      setNlStatus('success')
      setNlEmail('')
    } catch {
      setNlStatus('error')
    }
  }

  return (
    <footer className="bg-background border-t border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10">
          {/* Product */}
          <div>
            <h4 className="text-sm font-bold uppercase tracking-wider mb-4 text-foreground">
              Product
            </h4>
            <ul className="flex flex-col gap-3">
              {productLinks.map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-sm transition-colors text-foreground-muted hover:text-accent"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="text-sm font-bold uppercase tracking-wider mb-4 text-foreground">
              Company
            </h4>
            <ul className="flex flex-col gap-3">
              {companyLinks.map((link) => (
                <li key={link.to}>
                  <Link
                    to={link.to}
                    className="text-sm transition-colors text-foreground-muted hover:text-accent"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter — spans 2 columns on lg */}
          <div className="sm:col-span-2">
            <h4 className="text-sm font-bold uppercase tracking-wider mb-4 text-foreground">
              Newsletter
            </h4>
            <p className="text-sm mb-4 text-foreground-muted">
              Stay informed. Subscribe to our intelligence brief.
            </p>
            {nlStatus === 'success' ? (
              <p className="text-sm font-medium text-accent">
                Subscribed! Check your inbox.
              </p>
            ) : (
              <form className="flex gap-2" onSubmit={handleNewsletterSubmit}>
                <input
                  type="email"
                  required
                  value={nlEmail}
                  onChange={(e) => setNlEmail(e.target.value)}
                  placeholder="Enter your email"
                  className="flex-1 px-4 py-2 rounded-lg text-sm outline-none transition-colors bg-card border border-border text-foreground focus:border-accent"
                />
                <button
                  type="submit"
                  disabled={nlStatus === 'loading'}
                  className="px-5 py-2 rounded-lg text-sm font-semibold transition-colors whitespace-nowrap disabled:opacity-50 bg-accent text-accent-foreground hover:opacity-90"
                >
                  {nlStatus === 'loading' ? '...' : 'Subscribe'}
                </button>
              </form>
            )}
            {nlStatus === 'error' && (
              <p className="text-sm mt-2 text-danger">
                Something went wrong. Please try again.
              </p>
            )}
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-12 pt-8 text-center text-sm border-t border-border text-foreground-muted">
          &copy; 2026 Osfeed. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
