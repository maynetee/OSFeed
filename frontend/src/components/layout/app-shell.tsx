import { Outlet } from 'react-router-dom'

import { Header } from '@/components/layout/header'
import { Sidebar } from '@/components/layout/sidebar'
import { CommandPalette } from '@/components/layout/command-palette'
import { useKeyboardShortcuts } from '@/hooks/use-keyboard-shortcuts'

export function AppShell() {
  useKeyboardShortcuts()

  return (
    <div className="flex min-h-screen w-full bg-app">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header />
        <main className="flex-1 px-6 py-8">
          <Outlet />
        </main>
      </div>
      <CommandPalette />
    </div>
  )
}
