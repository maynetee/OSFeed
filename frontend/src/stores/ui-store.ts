import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ThemeMode = 'light' | 'dark' | 'system'

interface UiState {
  theme: ThemeMode
  sidebarCollapsed: boolean
  mobileDrawerOpen: boolean
  setTheme: (theme: ThemeMode) => void
  toggleSidebar: () => void
  toggleMobileDrawer: () => void
  closeMobileDrawer: () => void
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      theme: 'system',
      sidebarCollapsed: false,
      mobileDrawerOpen: false,
      setTheme: (theme) => set({ theme }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      toggleMobileDrawer: () => set((state) => ({ mobileDrawerOpen: !state.mobileDrawerOpen })),
      closeMobileDrawer: () => set({ mobileDrawerOpen: false }),
    }),
    {
      name: 'osfeed-ui',
    },
  ),
)
