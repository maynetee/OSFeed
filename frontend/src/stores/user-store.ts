import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  name?: string
  role?: string
}

interface AuthTokens {
  accessToken: string
  refreshToken: string
  refreshExpiresAt: string
}

interface UserState {
  user: User | null
  tokens: AuthTokens | null
  _hasHydrated: boolean
  setUser: (user: User | null) => void
  setTokens: (tokens: AuthTokens | null) => void
  logout: () => void
  setHasHydrated: (state: boolean) => void
}

// Promise-based hydration: resolves when hydration completes (success or error)
let resolveHydration: () => void = () => { }
export const hydrationPromise = new Promise<void>((resolve) => {
  resolveHydration = resolve
})

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      tokens: null,
      _hasHydrated: false,
      setUser: (user) => set({ user }),
      setTokens: (tokens) => set({ tokens }),
      logout: () => set({ user: null, tokens: null }),
      setHasHydrated: (state) => set({ _hasHydrated: state }),
    }),
    {
      name: 'osfeed-auth',
      partialize: (state) => ({ user: state.user, tokens: state.tokens }),
      onRehydrateStorage: () => (_state, error) => {
        if (error) {
          console.error('Error rehydrating auth store:', error)
        }
        // Always mark as hydrated, even on error
        useUserStore.setState({ _hasHydrated: true })
        // Resolve the hydration promise deterministically
        resolveHydration()
      },
    }
  )
)

/**
 * Wait for store hydration to complete.
 * Returns immediately if already hydrated, otherwise waits for hydration promise.
 */
export async function waitForHydration(): Promise<void> {
  if (useUserStore.getState()._hasHydrated) {
    return
  }
  await hydrationPromise
}

// SSR guard: if running in browser and hydration hasn't happened after persist init,
// manually trigger rehydrate. This handles edge cases where storage is unavailable.
if (typeof window !== 'undefined') {
  // Use persist API's rehydrate if hydration hasn't completed after store creation
  const unsubscribe = useUserStore.persist.onFinishHydration(() => {
    useUserStore.setState({ _hasHydrated: true })
    resolveHydration()
    unsubscribe()
  })

  // If already hydrated (synchronous storage), resolve immediately
  if (useUserStore.persist.hasHydrated()) {
    useUserStore.setState({ _hasHydrated: true })
    resolveHydration()
  }

  // Safety timeout: force hydration flag if it takes too long (e.g. storage issues)
  setTimeout(() => {
    if (!useUserStore.getState()._hasHydrated) {
      console.warn('Hydration timed out, forcing hydrated state')
      useUserStore.setState({ _hasHydrated: true })
      resolveHydration()
    }
  }, 500)
}
