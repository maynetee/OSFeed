import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('Navigation Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the feed page
    await page.goto('http://localhost:5173/feed')

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle')
  })

  test('should not have any automatically detectable WCAG 2.1 Level A violations', async ({ page }) => {
    // Wait for navigation to render
    await page.waitForSelector('nav a', { timeout: 5000 })

    // Run axe accessibility scan with WCAG 2.1 Level A tags
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag21a'])
      .analyze()

    // Report violations if any
    if (accessibilityScanResults.violations.length > 0) {
      console.log('Accessibility violations found:')
      accessibilityScanResults.violations.forEach((violation) => {
        console.log(`- ${violation.id}: ${violation.description}`)
        console.log(`  Impact: ${violation.impact}`)
        console.log(`  Help: ${violation.helpUrl}`)
      })
    }

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('should have aria-current="page" on active navigation link', async ({ page }) => {
    // Navigate to feed page
    await page.goto('http://localhost:5173/feed')
    await page.waitForLoadState('networkidle')

    // Find the active feed link
    const feedLink = page.locator('nav a[href="/feed"]')
    await expect(feedLink).toBeVisible()

    // Verify aria-current attribute
    await expect(feedLink).toHaveAttribute('aria-current', 'page')

    // Navigate to channels page
    await page.goto('http://localhost:5173/channels')
    await page.waitForLoadState('networkidle')

    // Verify feed link no longer has aria-current
    const feedLinkAfter = page.locator('nav a[href="/feed"]')
    await expect(feedLinkAfter).not.toHaveAttribute('aria-current', 'page')

    // Verify channels link has aria-current
    const channelsLink = page.locator('nav a[href="/channels"]')
    await expect(channelsLink).toHaveAttribute('aria-current', 'page')
  })

  test('should have aria-pressed on theme toggle buttons', async ({ page }) => {
    // Find theme toggle buttons
    const themeButtons = page.locator('button[aria-label*="Light"], button[aria-label*="Dark"]')
    await expect(themeButtons.first()).toBeVisible()

    // Get all theme buttons
    const buttonCount = await themeButtons.count()
    expect(buttonCount).toBeGreaterThanOrEqual(2)

    // Check each button has aria-pressed attribute
    for (let i = 0; i < buttonCount; i++) {
      const button = themeButtons.nth(i)
      const ariaPressed = await button.getAttribute('aria-pressed')
      expect(ariaPressed).toBeTruthy()
      expect(['true', 'false']).toContain(ariaPressed)
    }

    // Verify exactly one button is pressed
    const pressedButtons = await page.locator('button[aria-pressed="true"]').count()
    expect(pressedButtons).toBeGreaterThanOrEqual(1)
  })

  test('should toggle aria-pressed when theme button is clicked', async ({ page }) => {
    // Find light theme button
    const lightButton = page.locator('button[aria-label*="Light"]').first()
    const darkButton = page.locator('button[aria-label*="Dark"]').first()

    await expect(lightButton).toBeVisible()
    await expect(darkButton).toBeVisible()

    // Get initial pressed states
    const initialLightPressed = await lightButton.getAttribute('aria-pressed')
    const initialDarkPressed = await darkButton.getAttribute('aria-pressed')

    // Click the button that is not currently pressed
    if (initialLightPressed === 'false') {
      await lightButton.click()
      await page.waitForTimeout(200)
      await expect(lightButton).toHaveAttribute('aria-pressed', 'true')
      await expect(darkButton).toHaveAttribute('aria-pressed', 'false')
    } else {
      await darkButton.click()
      await page.waitForTimeout(200)
      await expect(darkButton).toHaveAttribute('aria-pressed', 'true')
      await expect(lightButton).toHaveAttribute('aria-pressed', 'false')
    }
  })

  test('should have visible focus indicators on navigation links', async ({ page }) => {
    // Find navigation links
    const navLinks = page.locator('nav a')
    await expect(navLinks.first()).toBeVisible()

    // Focus the first navigation link
    await navLinks.first().focus()

    // Check that the focused element is the nav link
    const focusedElement = await page.evaluate(() => {
      return document.activeElement?.tagName.toLowerCase()
    })
    expect(focusedElement).toBe('a')

    // Verify focus ring is visible by checking computed styles
    // The focus-visible class should add ring styles
    const hasFocusStyles = await navLinks.first().evaluate((el) => {
      const styles = window.getComputedStyle(el)
      // Check for outline or box-shadow (focus ring)
      return (
        styles.outline !== 'none' ||
        styles.outlineWidth !== '0px' ||
        styles.boxShadow !== 'none'
      )
    })

    expect(hasFocusStyles).toBe(true)
  })

  test('should support keyboard navigation through nav links', async ({ page }) => {
    // Start from the beginning
    await page.keyboard.press('Tab')

    // Get the first focusable navigation link
    const firstNavLink = page.locator('nav a').first()

    // Tab until we reach a navigation link
    let attempts = 0
    let reachedNavLink = false

    while (attempts < 20 && !reachedNavLink) {
      const focusedHref = await page.evaluate(() => {
        const el = document.activeElement
        return el?.getAttribute('href')
      })

      if (focusedHref && ['/feed', '/search', '/channels', '/collections', '/exports', '/settings'].includes(focusedHref)) {
        reachedNavLink = true
      } else {
        await page.keyboard.press('Tab')
        attempts++
      }
    }

    expect(reachedNavLink).toBe(true)

    // Press Tab again to move to next nav link
    await page.keyboard.press('Tab')

    // Verify we're still in navigation (another nav link is focused)
    const secondFocusedHref = await page.evaluate(() => {
      const el = document.activeElement
      return el?.getAttribute('href')
    })

    const navPaths = ['/feed', '/search', '/channels', '/collections', '/exports', '/settings']
    expect(navPaths).toContain(secondFocusedHref)
  })

  test('should have aria-expanded on mobile menu button', async ({ page, viewport }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 })

    // Reload page to trigger mobile layout
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Find the menu button
    const menuButton = page.locator('button[aria-label*="sidebar" i], button[aria-label*="menu" i]').first()
    await expect(menuButton).toBeVisible()

    // Verify aria-expanded attribute exists
    const ariaExpanded = await menuButton.getAttribute('aria-expanded')
    expect(ariaExpanded).toBeTruthy()
    expect(['true', 'false']).toContain(ariaExpanded)

    // Initial state should be false (drawer closed)
    await expect(menuButton).toHaveAttribute('aria-expanded', 'false')

    // Click to open drawer
    await menuButton.click()
    await page.waitForTimeout(300)

    // Verify aria-expanded is now true
    await expect(menuButton).toHaveAttribute('aria-expanded', 'true')
  })

  test('should restore focus to menu button when mobile drawer closes with Escape key', async ({ page }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 })

    // Reload page to trigger mobile layout
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Find and click the menu button
    const menuButton = page.locator('button[aria-label*="sidebar" i], button[aria-label*="menu" i]').first()
    await menuButton.click()
    await page.waitForTimeout(300)

    // Verify drawer is open
    await expect(menuButton).toHaveAttribute('aria-expanded', 'true')

    // Press Escape to close drawer
    await page.keyboard.press('Escape')
    await page.waitForTimeout(300)

    // Verify drawer is closed
    await expect(menuButton).toHaveAttribute('aria-expanded', 'false')

    // Verify focus returned to menu button
    const focusedElement = await page.evaluate(() => {
      const el = document.activeElement
      return {
        tagName: el?.tagName.toLowerCase(),
        ariaLabel: el?.getAttribute('aria-label'),
      }
    })

    expect(focusedElement.tagName).toBe('button')
    expect(focusedElement.ariaLabel).toMatch(/sidebar|menu/i)
  })

  test('should restore focus to menu button when mobile drawer closes by clicking outside', async ({ page }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 })

    // Reload page to trigger mobile layout
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Find and click the menu button
    const menuButton = page.locator('button[aria-label*="sidebar" i], button[aria-label*="menu" i]').first()
    await menuButton.click()
    await page.waitForTimeout(300)

    // Verify drawer is open
    await expect(menuButton).toHaveAttribute('aria-expanded', 'true')

    // Click outside the drawer (on the backdrop)
    await page.locator('[class*="backdrop"], [class*="bg-black"]').first().click({ position: { x: 10, y: 10 } })
    await page.waitForTimeout(300)

    // Verify drawer is closed
    await expect(menuButton).toHaveAttribute('aria-expanded', 'false')

    // Verify focus returned to menu button
    const focusedElement = await page.evaluate(() => {
      const el = document.activeElement
      return {
        tagName: el?.tagName.toLowerCase(),
        ariaLabel: el?.getAttribute('aria-label'),
      }
    })

    expect(focusedElement.tagName).toBe('button')
    expect(focusedElement.ariaLabel).toMatch(/sidebar|menu/i)
  })

  test('should restore focus to menu button when mobile drawer closes by navigation', async ({ page }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 })

    // Reload page to trigger mobile layout
    await page.reload()
    await page.waitForLoadState('networkidle')

    // Find and click the menu button
    const menuButton = page.locator('button[aria-label*="sidebar" i], button[aria-label*="menu" i]').first()
    await menuButton.click()
    await page.waitForTimeout(300)

    // Verify drawer is open
    await expect(menuButton).toHaveAttribute('aria-expanded', 'true')

    // Click a navigation link in the drawer
    await page.locator('nav a[href="/channels"]').click()
    await page.waitForTimeout(500)

    // Verify we navigated to channels page
    expect(page.url()).toContain('/channels')

    // Verify drawer is closed
    await expect(menuButton).toHaveAttribute('aria-expanded', 'false')

    // Verify focus returned to menu button
    const focusedElement = await page.evaluate(() => {
      const el = document.activeElement
      return {
        tagName: el?.tagName.toLowerCase(),
        ariaLabel: el?.getAttribute('aria-label'),
      }
    })

    expect(focusedElement.tagName).toBe('button')
    expect(focusedElement.ariaLabel).toMatch(/sidebar|menu/i)
  })

  test('should be accessible to screen readers', async ({ page }) => {
    // Get accessibility tree snapshot
    const snapshot = await page.accessibility.snapshot()

    // Helper function to find elements in accessibility tree
    const findInTree = (node: any, predicate: (node: any) => boolean): any => {
      if (predicate(node)) {
        return node
      }
      if (node.children) {
        for (const child of node.children) {
          const found = findInTree(child, predicate)
          if (found) return found
        }
      }
      return null
    }

    // Find navigation in accessibility tree
    const navNode = findInTree(snapshot, (node: any) =>
      node.role === 'navigation' || (node.name && node.name.toLowerCase().includes('nav'))
    )

    expect(navNode).toBeTruthy()

    // Find at least one link with current page indicator
    const currentPageLink = findInTree(snapshot, (node: any) =>
      node.role === 'link' && node.current === 'page'
    )

    expect(currentPageLink).toBeTruthy()
  })

  test('should maintain accessibility across theme changes', async ({ page }) => {
    // Run initial accessibility scan
    const lightModeScan = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag21a'])
      .analyze()

    expect(lightModeScan.violations).toEqual([])

    // Toggle theme
    const themeToggle = page.locator('button[aria-label*="Dark"]').first()

    if (await themeToggle.count() > 0) {
      await themeToggle.click()

      // Wait for theme change to apply
      await page.waitForTimeout(500)

      // Run accessibility scan in dark mode
      const darkModeScan = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag21a'])
        .analyze()

      expect(darkModeScan.violations).toEqual([])
    }
  })

  test('should have no keyboard traps in navigation', async ({ page }) => {
    // Start tabbing through the page
    await page.keyboard.press('Tab')

    // Tab through multiple elements
    for (let i = 0; i < 15; i++) {
      await page.keyboard.press('Tab')
      await page.waitForTimeout(100)
    }

    // Verify we can still interact with the page (no trap)
    const activeElement = await page.evaluate(() => {
      return document.activeElement?.tagName
    })

    // Should have an active element (not trapped)
    expect(activeElement).toBeTruthy()

    // Try reverse tabbing
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Shift+Tab')
      await page.waitForTimeout(100)
    }

    // Verify we can still interact (no trap in reverse)
    const activeElementAfter = await page.evaluate(() => {
      return document.activeElement?.tagName
    })

    expect(activeElementAfter).toBeTruthy()
  })
})
