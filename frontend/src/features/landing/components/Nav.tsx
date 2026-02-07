import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Zap, Menu, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { trackEvent } from '@/lib/analytics'

const navLinks = [
  { label: 'How It Works', to: '/how-it-works' },
  { label: 'Pricing', to: '/pricing' },
  { label: 'Resources', to: '/resources' },
]

export default function Nav() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-accent">
              <Zap size={18} className="text-accent-foreground" />
            </div>
            <span className="text-lg font-bold text-foreground">Osfeed</span>
          </Link>

          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className="text-sm font-medium text-foreground-muted transition-colors hover:text-accent"
                onClick={() =>
                  trackEvent('Nav Click', {
                    item: link.label.toLowerCase().replace(/\s+/g, '-'),
                  })
                }
              >
                {link.label}
              </Link>
            ))}
            <Link
              to="/login"
              className="text-sm font-medium text-foreground-muted transition-colors hover:text-accent"
              onClick={() => trackEvent('Nav Click', { item: 'login' })}
            >
              Login
            </Link>
            <Link
              to="/signup"
              className="text-sm font-semibold px-4 py-2 rounded-lg bg-accent text-accent-foreground transition-colors hover:brightness-110"
              onClick={() => trackEvent('Nav Click', { item: 'get-started' })}
            >
              Get Started
            </Link>
          </div>

          {/* Mobile toggle */}
          <button
            className="md:hidden p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? (
              <X size={24} className="text-foreground" />
            ) : (
              <Menu size={24} className="text-foreground" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden overflow-hidden bg-card"
          >
            <div className="px-4 py-4 flex flex-col gap-4">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className="text-sm font-medium text-foreground-muted"
                  onClick={() => {
                    trackEvent('Nav Click', {
                      item: link.label.toLowerCase().replace(/\s+/g, '-'),
                    })
                    setMobileOpen(false)
                  }}
                >
                  {link.label}
                </Link>
              ))}
              <Link
                to="/login"
                className="text-sm font-medium text-foreground-muted"
                onClick={() => {
                  trackEvent('Nav Click', { item: 'login' })
                  setMobileOpen(false)
                }}
              >
                Login
              </Link>
              <Link
                to="/signup"
                className="text-sm font-semibold px-4 py-2 rounded-lg bg-accent text-accent-foreground text-center"
                onClick={() => {
                  trackEvent('Nav Click', { item: 'get-started' })
                  setMobileOpen(false)
                }}
              >
                Get Started
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}
