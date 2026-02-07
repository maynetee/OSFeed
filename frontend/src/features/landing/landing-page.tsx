import { useNavigate } from 'react-router-dom'
import { useUserStore } from '@/stores/user-store'
import { Seo } from './components/Seo'

import Nav from './components/Nav'
import { HeroSection } from './components/HeroSection'
import { ProblemSection } from './components/ProblemSection'
import { SolutionSection } from './components/SolutionSection'
import { HowItWorks } from './components/HowItWorks'
import { UseCasesSection } from './components/UseCasesSection'
import { PricingPreview } from './components/PricingPreview'
import { CtaFinal } from './components/CtaFinal'
import Footer from './components/Footer'

export function LandingPage() {
  const navigate = useNavigate()
  const { user } = useUserStore()

  if (user) {
    navigate('/feed')
    return null
  }

  return (
    <div className="min-h-screen font-sans antialiased" style={{ backgroundColor: '#0D1117', color: '#F3F4F6' }}>
      <Seo title="Osfeed — Real-time Intelligence Platform" description="Monitor, translate, and analyze Telegram channels in real time. Osfeed is the OSINT platform built for intelligence professionals, journalists, and security teams." />
      {/* Background glows */}
      <div className="fixed inset-0 pointer-events-none">
        <div
          className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] blur-[120px] rounded-full"
          style={{ backgroundColor: 'rgba(0, 212, 170, 0.04)' }}
        />
        <div
          className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] blur-[120px] rounded-full"
          style={{ backgroundColor: 'rgba(0, 212, 170, 0.04)' }}
        />
      </div>

      <Nav />

      <main className="relative z-10 pt-16">
        <HeroSection />
        <ProblemSection />
        <SolutionSection />
        <HowItWorks />
        <UseCasesSection />
        <PricingPreview />
        <CtaFinal />
      </main>

      <Footer />
    </div>
  )
}
