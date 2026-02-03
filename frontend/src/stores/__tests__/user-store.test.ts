import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { useUserStore, waitForHydration, hydrationPromise } from '../user-store'

describe('useUserStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useUserStore.setState({
      user: null,
      tokens: null,
      _hasHydrated: true, // Set to true to prevent hydration delays in tests
    })

    // Clear localStorage to prevent persistence interference
    localStorage.clear()

    // Clear console mocks
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('should have user as null initially', () => {
      const state = useUserStore.getState()
      expect(state.user).toBeNull()
    })

    it('should have tokens as null initially', () => {
      const state = useUserStore.getState()
      expect(state.tokens).toBeNull()
    })

    it('should have _hasHydrated as true after reset', () => {
      const state = useUserStore.getState()
      expect(state._hasHydrated).toBe(true)
    })
  })

  describe('setUser', () => {
    it('should set user with complete user data', () => {
      const { setUser } = useUserStore.getState()
      const mockUser = {
        id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
        role: 'admin',
      }

      setUser(mockUser)

      expect(useUserStore.getState().user).toEqual(mockUser)
    })

    it('should set user with minimal user data', () => {
      const { setUser } = useUserStore.getState()
      const mockUser = {
        id: 'user-456',
        email: 'minimal@example.com',
      }

      setUser(mockUser)

      expect(useUserStore.getState().user).toEqual(mockUser)
    })

    it('should update user when called multiple times', () => {
      const { setUser } = useUserStore.getState()
      const firstUser = {
        id: 'user-1',
        email: 'first@example.com',
        name: 'First User',
      }
      const secondUser = {
        id: 'user-2',
        email: 'second@example.com',
        name: 'Second User',
      }

      setUser(firstUser)
      expect(useUserStore.getState().user).toEqual(firstUser)

      setUser(secondUser)
      expect(useUserStore.getState().user).toEqual(secondUser)
    })

    it('should set user to null to clear user data', () => {
      const { setUser } = useUserStore.getState()
      const mockUser = {
        id: 'user-789',
        email: 'clear@example.com',
      }

      setUser(mockUser)
      expect(useUserStore.getState().user).toEqual(mockUser)

      setUser(null)
      expect(useUserStore.getState().user).toBeNull()
    })
  })

  describe('setTokens', () => {
    it('should set tokens with complete token data', () => {
      const { setTokens } = useUserStore.getState()
      const mockTokens = {
        accessToken: 'access-token-123',
        refreshToken: 'refresh-token-456',
        refreshExpiresAt: '2026-12-31T23:59:59Z',
      }

      setTokens(mockTokens)

      expect(useUserStore.getState().tokens).toEqual(mockTokens)
    })

    it('should update tokens when called multiple times', () => {
      const { setTokens } = useUserStore.getState()
      const firstTokens = {
        accessToken: 'access-1',
        refreshToken: 'refresh-1',
        refreshExpiresAt: '2026-01-01T00:00:00Z',
      }
      const secondTokens = {
        accessToken: 'access-2',
        refreshToken: 'refresh-2',
        refreshExpiresAt: '2026-02-01T00:00:00Z',
      }

      setTokens(firstTokens)
      expect(useUserStore.getState().tokens).toEqual(firstTokens)

      setTokens(secondTokens)
      expect(useUserStore.getState().tokens).toEqual(secondTokens)
    })

    it('should set tokens to null to clear token data', () => {
      const { setTokens } = useUserStore.getState()
      const mockTokens = {
        accessToken: 'access-token',
        refreshToken: 'refresh-token',
        refreshExpiresAt: '2026-03-01T00:00:00Z',
      }

      setTokens(mockTokens)
      expect(useUserStore.getState().tokens).toEqual(mockTokens)

      setTokens(null)
      expect(useUserStore.getState().tokens).toBeNull()
    })
  })

  describe('logout', () => {
    it('should clear both user and tokens', () => {
      const { setUser, setTokens, logout } = useUserStore.getState()

      // Set up user and tokens
      setUser({
        id: 'user-999',
        email: 'logout@example.com',
        name: 'Logout User',
      })
      setTokens({
        accessToken: 'access-logout',
        refreshToken: 'refresh-logout',
        refreshExpiresAt: '2026-06-01T00:00:00Z',
      })

      expect(useUserStore.getState().user).not.toBeNull()
      expect(useUserStore.getState().tokens).not.toBeNull()

      // Logout
      logout()

      expect(useUserStore.getState().user).toBeNull()
      expect(useUserStore.getState().tokens).toBeNull()
    })

    it('should work when user and tokens are already null', () => {
      const { logout } = useUserStore.getState()

      expect(useUserStore.getState().user).toBeNull()
      expect(useUserStore.getState().tokens).toBeNull()

      logout()

      expect(useUserStore.getState().user).toBeNull()
      expect(useUserStore.getState().tokens).toBeNull()
    })

    it('should clear user when only user is set', () => {
      const { setUser, logout } = useUserStore.getState()

      setUser({
        id: 'user-only',
        email: 'useronly@example.com',
      })

      logout()

      expect(useUserStore.getState().user).toBeNull()
      expect(useUserStore.getState().tokens).toBeNull()
    })

    it('should clear tokens when only tokens are set', () => {
      const { setTokens, logout } = useUserStore.getState()

      setTokens({
        accessToken: 'access-only',
        refreshToken: 'refresh-only',
        refreshExpiresAt: '2026-07-01T00:00:00Z',
      })

      logout()

      expect(useUserStore.getState().user).toBeNull()
      expect(useUserStore.getState().tokens).toBeNull()
    })
  })

  describe('setHasHydrated', () => {
    it('should set _hasHydrated to true', () => {
      const { setHasHydrated } = useUserStore.getState()

      useUserStore.setState({ _hasHydrated: false })
      expect(useUserStore.getState()._hasHydrated).toBe(false)

      setHasHydrated(true)
      expect(useUserStore.getState()._hasHydrated).toBe(true)
    })

    it('should set _hasHydrated to false', () => {
      const { setHasHydrated } = useUserStore.getState()

      useUserStore.setState({ _hasHydrated: true })
      expect(useUserStore.getState()._hasHydrated).toBe(true)

      setHasHydrated(false)
      expect(useUserStore.getState()._hasHydrated).toBe(false)
    })

    it('should toggle _hasHydrated multiple times', () => {
      const { setHasHydrated } = useUserStore.getState()

      setHasHydrated(false)
      expect(useUserStore.getState()._hasHydrated).toBe(false)

      setHasHydrated(true)
      expect(useUserStore.getState()._hasHydrated).toBe(true)

      setHasHydrated(false)
      expect(useUserStore.getState()._hasHydrated).toBe(false)
    })
  })

  describe('waitForHydration', () => {
    it('should resolve immediately when already hydrated', async () => {
      useUserStore.setState({ _hasHydrated: true })

      const start = Date.now()
      await waitForHydration()
      const duration = Date.now() - start

      // Should resolve almost immediately (< 10ms)
      expect(duration).toBeLessThan(10)
    })

    it('should return a promise that resolves', async () => {
      useUserStore.setState({ _hasHydrated: true })

      const result = waitForHydration()

      expect(result).toBeInstanceOf(Promise)
      await expect(result).resolves.toBeUndefined()
    })
  })

  describe('hydrationPromise', () => {
    it('should be a Promise', () => {
      expect(hydrationPromise).toBeInstanceOf(Promise)
    })
  })

  describe('state independence', () => {
    it('should not affect tokens when setting user', () => {
      const { setUser, setTokens } = useUserStore.getState()

      const mockTokens = {
        accessToken: 'access-independent',
        refreshToken: 'refresh-independent',
        refreshExpiresAt: '2026-08-01T00:00:00Z',
      }
      setTokens(mockTokens)

      setUser({
        id: 'user-independent',
        email: 'independent@example.com',
      })

      expect(useUserStore.getState().tokens).toEqual(mockTokens)
    })

    it('should not affect user when setting tokens', () => {
      const { setUser, setTokens } = useUserStore.getState()

      const mockUser = {
        id: 'user-independent-2',
        email: 'independent2@example.com',
        name: 'Independent User',
      }
      setUser(mockUser)

      setTokens({
        accessToken: 'access-independent-2',
        refreshToken: 'refresh-independent-2',
        refreshExpiresAt: '2026-09-01T00:00:00Z',
      })

      expect(useUserStore.getState().user).toEqual(mockUser)
    })

    it('should not affect _hasHydrated when setting user or tokens', () => {
      const { setUser, setTokens, setHasHydrated } = useUserStore.getState()

      setHasHydrated(false)

      setUser({
        id: 'user-hydrated',
        email: 'hydrated@example.com',
      })
      expect(useUserStore.getState()._hasHydrated).toBe(false)

      setTokens({
        accessToken: 'access-hydrated',
        refreshToken: 'refresh-hydrated',
        refreshExpiresAt: '2026-10-01T00:00:00Z',
      })
      expect(useUserStore.getState()._hasHydrated).toBe(false)
    })
  })

  describe('persistence', () => {
    it('should persist user to localStorage', () => {
      const { setUser } = useUserStore.getState()
      const mockUser = {
        id: 'user-persist',
        email: 'persist@example.com',
        name: 'Persist User',
      }

      setUser(mockUser)

      const stored = localStorage.getItem('osfeed-auth')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.user).toEqual(mockUser)
    })

    it('should persist tokens to localStorage', () => {
      const { setTokens } = useUserStore.getState()
      const mockTokens = {
        accessToken: 'access-persist',
        refreshToken: 'refresh-persist',
        refreshExpiresAt: '2026-11-01T00:00:00Z',
      }

      setTokens(mockTokens)

      const stored = localStorage.getItem('osfeed-auth')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.tokens).toEqual(mockTokens)
    })

    it('should persist both user and tokens to localStorage', () => {
      const { setUser, setTokens } = useUserStore.getState()
      const mockUser = {
        id: 'user-both',
        email: 'both@example.com',
      }
      const mockTokens = {
        accessToken: 'access-both',
        refreshToken: 'refresh-both',
        refreshExpiresAt: '2026-12-01T00:00:00Z',
      }

      setUser(mockUser)
      setTokens(mockTokens)

      const stored = localStorage.getItem('osfeed-auth')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.user).toEqual(mockUser)
      expect(parsed.state.tokens).toEqual(mockTokens)
    })

    it('should not persist _hasHydrated to localStorage (partialize)', () => {
      const { setHasHydrated, setUser } = useUserStore.getState()

      setUser({
        id: 'user-no-hydrate',
        email: 'nohydrate@example.com',
      })
      setHasHydrated(false)

      const stored = localStorage.getItem('osfeed-auth')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      // _hasHydrated should not be in the persisted state due to partialize
      expect(parsed.state._hasHydrated).toBeUndefined()
      // But user should be persisted
      expect(parsed.state.user).toBeDefined()
    })

    it('should persist null values when logging out', () => {
      const { setUser, setTokens, logout } = useUserStore.getState()

      // Set up data
      setUser({
        id: 'user-logout-persist',
        email: 'logoutpersist@example.com',
      })
      setTokens({
        accessToken: 'access-logout-persist',
        refreshToken: 'refresh-logout-persist',
        refreshExpiresAt: '2027-01-01T00:00:00Z',
      })

      // Logout
      logout()

      const stored = localStorage.getItem('osfeed-auth')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.user).toBeNull()
      expect(parsed.state.tokens).toBeNull()
    })
  })
})
