import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { useUiStore } from '../ui-store'
import type { ThemeMode } from '../ui-store'

describe('useUiStore', () => {
  beforeEach(() => {
    // Reset store to initial state before each test
    useUiStore.setState({
      theme: 'system',
      sidebarCollapsed: false,
      mobileDrawerOpen: false,
      menuButtonElement: null,
    })

    // Clear localStorage to prevent persistence interference
    localStorage.clear()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('initial state', () => {
    it('should have correct initial theme', () => {
      const state = useUiStore.getState()
      expect(state.theme).toBe('system')
    })

    it('should have sidebar not collapsed initially', () => {
      const state = useUiStore.getState()
      expect(state.sidebarCollapsed).toBe(false)
    })

    it('should have mobile drawer closed initially', () => {
      const state = useUiStore.getState()
      expect(state.mobileDrawerOpen).toBe(false)
    })

    it('should have no menu button element initially', () => {
      const state = useUiStore.getState()
      expect(state.menuButtonElement).toBeNull()
    })
  })

  describe('setTheme', () => {
    it('should set theme to light', () => {
      const { setTheme } = useUiStore.getState()

      setTheme('light')

      expect(useUiStore.getState().theme).toBe('light')
    })

    it('should set theme to dark', () => {
      const { setTheme } = useUiStore.getState()

      setTheme('dark')

      expect(useUiStore.getState().theme).toBe('dark')
    })

    it('should set theme to system', () => {
      const { setTheme } = useUiStore.getState()

      // First change to light
      setTheme('light')
      expect(useUiStore.getState().theme).toBe('light')

      // Then back to system
      setTheme('system')
      expect(useUiStore.getState().theme).toBe('system')
    })

    it('should allow switching between different theme modes', () => {
      const { setTheme } = useUiStore.getState()

      const themes: ThemeMode[] = ['light', 'dark', 'system', 'light']

      themes.forEach((theme) => {
        setTheme(theme)
        expect(useUiStore.getState().theme).toBe(theme)
      })
    })
  })

  describe('toggleSidebar', () => {
    it('should toggle sidebar from collapsed to expanded', () => {
      const { toggleSidebar } = useUiStore.getState()

      // Initial state is not collapsed
      expect(useUiStore.getState().sidebarCollapsed).toBe(false)

      // Toggle to collapsed
      toggleSidebar()
      expect(useUiStore.getState().sidebarCollapsed).toBe(true)
    })

    it('should toggle sidebar from expanded to collapsed', () => {
      const { toggleSidebar } = useUiStore.getState()

      // Set to collapsed first
      useUiStore.setState({ sidebarCollapsed: true })

      // Toggle to expanded
      toggleSidebar()
      expect(useUiStore.getState().sidebarCollapsed).toBe(false)
    })

    it('should toggle sidebar multiple times correctly', () => {
      const { toggleSidebar } = useUiStore.getState()

      expect(useUiStore.getState().sidebarCollapsed).toBe(false)

      toggleSidebar() // true
      expect(useUiStore.getState().sidebarCollapsed).toBe(true)

      toggleSidebar() // false
      expect(useUiStore.getState().sidebarCollapsed).toBe(false)

      toggleSidebar() // true
      expect(useUiStore.getState().sidebarCollapsed).toBe(true)
    })
  })

  describe('toggleMobileDrawer', () => {
    it('should toggle mobile drawer from closed to open', () => {
      const { toggleMobileDrawer } = useUiStore.getState()

      // Initial state is closed
      expect(useUiStore.getState().mobileDrawerOpen).toBe(false)

      // Toggle to open
      toggleMobileDrawer()
      expect(useUiStore.getState().mobileDrawerOpen).toBe(true)
    })

    it('should toggle mobile drawer from open to closed', () => {
      const { toggleMobileDrawer } = useUiStore.getState()

      // Set to open first
      useUiStore.setState({ mobileDrawerOpen: true })

      // Toggle to closed
      toggleMobileDrawer()
      expect(useUiStore.getState().mobileDrawerOpen).toBe(false)
    })

    it('should toggle mobile drawer multiple times correctly', () => {
      const { toggleMobileDrawer } = useUiStore.getState()

      expect(useUiStore.getState().mobileDrawerOpen).toBe(false)

      toggleMobileDrawer() // true
      expect(useUiStore.getState().mobileDrawerOpen).toBe(true)

      toggleMobileDrawer() // false
      expect(useUiStore.getState().mobileDrawerOpen).toBe(false)

      toggleMobileDrawer() // true
      expect(useUiStore.getState().mobileDrawerOpen).toBe(true)
    })
  })

  describe('closeMobileDrawer', () => {
    it('should close mobile drawer when open', () => {
      const { closeMobileDrawer } = useUiStore.getState()

      // Set to open first
      useUiStore.setState({ mobileDrawerOpen: true })
      expect(useUiStore.getState().mobileDrawerOpen).toBe(true)

      // Close drawer
      closeMobileDrawer()
      expect(useUiStore.getState().mobileDrawerOpen).toBe(false)
    })

    it('should keep mobile drawer closed when already closed', () => {
      const { closeMobileDrawer } = useUiStore.getState()

      // Initial state is closed
      expect(useUiStore.getState().mobileDrawerOpen).toBe(false)

      // Close drawer (should remain closed)
      closeMobileDrawer()
      expect(useUiStore.getState().mobileDrawerOpen).toBe(false)
    })

    it('should close mobile drawer multiple times without side effects', () => {
      const { closeMobileDrawer } = useUiStore.getState()

      // Set to open
      useUiStore.setState({ mobileDrawerOpen: true })

      closeMobileDrawer()
      expect(useUiStore.getState().mobileDrawerOpen).toBe(false)

      closeMobileDrawer()
      expect(useUiStore.getState().mobileDrawerOpen).toBe(false)

      closeMobileDrawer()
      expect(useUiStore.getState().mobileDrawerOpen).toBe(false)
    })
  })

  describe('setMenuButtonElement', () => {
    it('should set menu button element', () => {
      const { setMenuButtonElement } = useUiStore.getState()
      const mockElement = document.createElement('button')

      setMenuButtonElement(mockElement)

      expect(useUiStore.getState().menuButtonElement).toBe(mockElement)
    })

    it('should update menu button element to a new element', () => {
      const { setMenuButtonElement } = useUiStore.getState()
      const firstElement = document.createElement('button')
      const secondElement = document.createElement('div')

      setMenuButtonElement(firstElement)
      expect(useUiStore.getState().menuButtonElement).toBe(firstElement)

      setMenuButtonElement(secondElement)
      expect(useUiStore.getState().menuButtonElement).toBe(secondElement)
    })

    it('should set menu button element to null', () => {
      const { setMenuButtonElement } = useUiStore.getState()
      const mockElement = document.createElement('button')

      // First set to an element
      setMenuButtonElement(mockElement)
      expect(useUiStore.getState().menuButtonElement).toBe(mockElement)

      // Then set to null
      setMenuButtonElement(null)
      expect(useUiStore.getState().menuButtonElement).toBeNull()
    })

    it('should handle setting null when already null', () => {
      const { setMenuButtonElement } = useUiStore.getState()

      // Initial state is null
      expect(useUiStore.getState().menuButtonElement).toBeNull()

      // Set to null again
      setMenuButtonElement(null)
      expect(useUiStore.getState().menuButtonElement).toBeNull()
    })
  })

  describe('state independence', () => {
    it('should not affect other state when setting theme', () => {
      const { setTheme, toggleSidebar } = useUiStore.getState()

      // Set some initial state
      toggleSidebar()
      useUiStore.setState({ mobileDrawerOpen: true })

      const beforeTheme = {
        sidebarCollapsed: useUiStore.getState().sidebarCollapsed,
        mobileDrawerOpen: useUiStore.getState().mobileDrawerOpen,
      }

      // Change theme
      setTheme('dark')

      // Other state should be unchanged
      expect(useUiStore.getState().sidebarCollapsed).toBe(beforeTheme.sidebarCollapsed)
      expect(useUiStore.getState().mobileDrawerOpen).toBe(beforeTheme.mobileDrawerOpen)
    })

    it('should not affect other state when toggling sidebar', () => {
      const { setTheme, toggleSidebar } = useUiStore.getState()

      // Set some initial state
      setTheme('dark')
      useUiStore.setState({ mobileDrawerOpen: true })

      const beforeToggle = {
        theme: useUiStore.getState().theme,
        mobileDrawerOpen: useUiStore.getState().mobileDrawerOpen,
      }

      // Toggle sidebar
      toggleSidebar()

      // Other state should be unchanged
      expect(useUiStore.getState().theme).toBe(beforeToggle.theme)
      expect(useUiStore.getState().mobileDrawerOpen).toBe(beforeToggle.mobileDrawerOpen)
    })

    it('should not affect other state when toggling mobile drawer', () => {
      const { setTheme, toggleSidebar, toggleMobileDrawer } = useUiStore.getState()

      // Set some initial state
      setTheme('light')
      toggleSidebar()

      const beforeToggle = {
        theme: useUiStore.getState().theme,
        sidebarCollapsed: useUiStore.getState().sidebarCollapsed,
      }

      // Toggle mobile drawer
      toggleMobileDrawer()

      // Other state should be unchanged
      expect(useUiStore.getState().theme).toBe(beforeToggle.theme)
      expect(useUiStore.getState().sidebarCollapsed).toBe(beforeToggle.sidebarCollapsed)
    })
  })

  describe('persistence', () => {
    it('should persist theme to localStorage', () => {
      const { setTheme } = useUiStore.getState()

      setTheme('dark')

      const stored = localStorage.getItem('osfeed-ui')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.theme).toBe('dark')
    })

    it('should persist sidebar state to localStorage', () => {
      const { toggleSidebar } = useUiStore.getState()

      toggleSidebar()

      const stored = localStorage.getItem('osfeed-ui')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.sidebarCollapsed).toBe(true)
    })

    it('should persist mobile drawer state to localStorage', () => {
      const { toggleMobileDrawer } = useUiStore.getState()

      toggleMobileDrawer()

      const stored = localStorage.getItem('osfeed-ui')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.mobileDrawerOpen).toBe(true)
    })

    it('should persist all state changes to localStorage', () => {
      const { setTheme, toggleSidebar, toggleMobileDrawer } = useUiStore.getState()

      setTheme('light')
      toggleSidebar()
      toggleMobileDrawer()

      const stored = localStorage.getItem('osfeed-ui')
      expect(stored).toBeTruthy()

      const parsed = JSON.parse(stored!)
      expect(parsed.state.theme).toBe('light')
      expect(parsed.state.sidebarCollapsed).toBe(true)
      expect(parsed.state.mobileDrawerOpen).toBe(true)
    })
  })
})
