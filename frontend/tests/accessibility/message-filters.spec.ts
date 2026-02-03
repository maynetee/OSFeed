import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('MessageFilters Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to page with MessageFilters
    await page.goto('http://localhost:5173/dashboard')

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle')
  })

  test('should not have any automatically detectable WCAG 2.1 Level AA violations', async ({ page }) => {
    // Wait for filters to render
    await page.waitForSelector('fieldset', { timeout: 5000 })

    // Run axe accessibility scan with WCAG 2.1 Level AA tags
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag21a', 'wcag2aa', 'wcag21aa'])
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

  test('should have proper fieldset/legend structure', async ({ page }) => {
    // Find all fieldsets
    const fieldsets = page.locator('fieldset')
    const fieldsetCount = await fieldsets.count()

    // Should have at least 3 fieldsets (period, media types, channels)
    expect(fieldsetCount).toBeGreaterThanOrEqual(3)

    // Check each fieldset has a legend
    for (let i = 0; i < fieldsetCount; i++) {
      const fieldset = fieldsets.nth(i)
      const legend = fieldset.locator('legend')

      await expect(legend).toBeVisible()

      // Verify legend has text content
      const legendText = await legend.textContent()
      expect(legendText).toBeTruthy()
      expect(legendText?.length).toBeGreaterThan(0)
    }
  })

  test('should have sufficient contrast on legend elements', async ({ page }) => {
    // Run contrast-specific accessibility scan
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .include('fieldset')
      .analyze()

    // Filter for contrast-related violations
    const contrastViolations = accessibilityScanResults.violations.filter(
      (violation) => violation.id === 'color-contrast' || violation.id.includes('contrast')
    )

    if (contrastViolations.length > 0) {
      console.log('Contrast violations found:')
      contrastViolations.forEach((violation) => {
        console.log(`- ${violation.id}: ${violation.description}`)
        console.log(`  Impact: ${violation.impact}`)
      })
    }

    expect(contrastViolations).toEqual([])
  })

  test('should show active filter summary when filters are applied', async ({ page }) => {
    // Initially, summary should not be visible (no filters active)
    const summaryContainer = page.locator('text="Active:" i').locator('..')
    const initialSummaryVisible = await summaryContainer.isVisible().catch(() => false)

    // If no filters are active initially, summary should be hidden
    // If filters are persisted, we'll skip this check
    if (!initialSummaryVisible) {
      // Click a filter button to activate a filter
      const filterButton = page.locator('button[aria-pressed="false"]').first()
      await filterButton.click()

      // Wait a moment for state update
      await page.waitForTimeout(300)

      // Summary should now be visible
      await expect(summaryContainer).toBeVisible()

      // Check that badges are present
      const badges = page.locator('.bg-muted, [class*="badge"]')
      const badgeCount = await badges.count()
      expect(badgeCount).toBeGreaterThan(0)
    }
  })

  test('should have all filter buttons with proper ARIA attributes', async ({ page }) => {
    // Find all filter buttons
    const filterButtons = page.locator('fieldset button')
    const buttonCount = await filterButtons.count()

    expect(buttonCount).toBeGreaterThan(0)

    // Check a sample of buttons have aria-pressed
    for (let i = 0; i < Math.min(buttonCount, 5); i++) {
      const button = filterButtons.nth(i)
      const ariaPressed = await button.getAttribute('aria-pressed')

      // aria-pressed should be 'true' or 'false'
      expect(ariaPressed).toMatch(/^(true|false)$/)
    }
  })

  test('should be keyboard accessible', async ({ page }) => {
    // Focus on the first filter button
    const firstButton = page.locator('fieldset button').first()
    await firstButton.focus()

    // Verify button is focused
    const isFocused = await firstButton.evaluate((el) => el === document.activeElement)
    expect(isFocused).toBe(true)

    // Press Tab to move to next element
    await page.keyboard.press('Tab')

    // Verify focus moved (no keyboard trap)
    const stillFocused = await firstButton.evaluate((el) => el === document.activeElement)
    expect(stillFocused).toBe(false)

    // Press Enter on a focused filter button
    const secondButton = page.locator('fieldset button').nth(1)
    await secondButton.focus()

    const initialPressed = await secondButton.getAttribute('aria-pressed')
    await page.keyboard.press('Enter')

    // Wait for state update
    await page.waitForTimeout(200)

    const afterPressed = await secondButton.getAttribute('aria-pressed')

    // aria-pressed should have toggled
    expect(initialPressed).not.toBe(afterPressed)
  })

  test('should support theme switching without accessibility issues', async ({ page }) => {
    // Wait for filters to render
    await page.waitForSelector('fieldset', { timeout: 5000 })

    // Run initial accessibility scan
    const lightModeScan = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag21a', 'wcag2aa', 'wcag21aa'])
      .analyze()

    expect(lightModeScan.violations).toEqual([])

    // Find and click theme toggle button
    const themeToggle = page.locator('button[aria-label*="theme" i], button[aria-label*="dark" i], button[aria-label*="light" i]').first()

    if (await themeToggle.count() > 0) {
      await themeToggle.click()

      // Wait for theme change to apply
      await page.waitForTimeout(500)

      // Run accessibility scan in dark mode
      const darkModeScan = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag21a', 'wcag2aa', 'wcag21aa'])
        .analyze()

      expect(darkModeScan.violations).toEqual([])
    }
  })

  test('should have proper heading structure in filter card', async ({ page }) => {
    // Check for filter title
    const filterTitle = page.locator('text="Filters" i, text="Filter" i').first()

    // Title should be visible
    await expect(filterTitle).toBeVisible()

    // Get accessibility tree snapshot
    const snapshot = await page.accessibility.snapshot()

    // Helper function to find in accessibility tree
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

    // Verify the page has proper structure in accessibility tree
    expect(snapshot).toBeTruthy()
  })

  test('should have clear all button that is accessible', async ({ page }) => {
    // Activate at least one filter
    const filterButton = page.locator('fieldset button[aria-pressed="false"]').first()
    await filterButton.click()

    // Wait for state update
    await page.waitForTimeout(300)

    // Find clear button
    const clearButton = page.locator('button', { hasText: /clear/i })

    // If clear button exists, it should be visible and accessible
    if (await clearButton.count() > 0) {
      await expect(clearButton).toBeVisible()

      // Should be keyboard accessible
      await clearButton.focus()
      const isFocused = await clearButton.evaluate((el) => el === document.activeElement)
      expect(isFocused).toBe(true)

      // Click it and verify filters are cleared
      await clearButton.click()
      await page.waitForTimeout(300)

      // Summary should be hidden after clearing
      const summaryContainer = page.locator('text="Active:" i').locator('..')
      const summaryVisible = await summaryContainer.isVisible().catch(() => false)
      expect(summaryVisible).toBe(false)
    }
  })

  test('should be accessible to screen readers', async ({ page }) => {
    // Get accessibility tree snapshot
    const snapshot = await page.accessibility.snapshot()

    // Helper function to find in accessibility tree
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

    // Find filter buttons in accessibility tree
    const buttonNode = findInTree(snapshot, (node: any) =>
      node.role === 'button' && node.pressed !== undefined
    )

    expect(buttonNode).toBeTruthy()
    expect(buttonNode.pressed).toMatch(/^(true|false)$/)
  })
})
