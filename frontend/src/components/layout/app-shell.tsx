import { Outlet } from 'react-router-dom'
import { toast, Toaster } from 'sonner'

import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts'
import { useMessageStream } from '@/hooks/use-message-stream'
import { useMobile } from '@/hooks/use-mobile'
import { useUserStore } from '@/stores/user-store'

export function AppShell() {
  useKeyboardShortcuts()
  const isMobile = useMobile()
  const user = useUserStore((s) => s.user)

  useMessageStream({
    enabled: !!user,
    onAlert: (data) => {
      toast.success(data.alert_name, {
        description: data.summary,
      })
    },
  })

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
