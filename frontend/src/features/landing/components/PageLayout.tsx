import Nav from './Nav'
import Footer from './Footer'

interface PageLayoutProps {
  children: React.ReactNode
}

export function PageLayout({ children }: PageLayoutProps) {
  return (
    <div className="min-h-screen font-sans antialiased" style={{ backgroundColor: '#0D1117', color: '#F3F4F6' }}>
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
        {children}
      </main>

      <Footer />
    </div>
  )
}
