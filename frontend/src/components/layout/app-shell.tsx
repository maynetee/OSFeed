import { Outlet } from 'react-router-dom'
import { Toaster } from 'sonner'

import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts'
import { useMobile } from '@/hooks/use-mobile'

export function AppShell() {
  useKeyboardShortcuts()
  const isMobile = useMobile()

  return (
    <>
      <div className="flex min-h-screen w-full bg-app">
        {!isMobile && <Sidebar />}
        <div className="flex flex-1 flex-col">
          <Header />
          <main className="flex-1 px-6 py-8">
            <Outlet />
          </main>
        </div>
        {isMobile && <Sidebar />}
      </div>
      <Toaster position="top-right" richColors />
    </>
  )
}
