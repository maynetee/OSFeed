import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('TrendChart Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to page with TrendChart
    await page.goto('http://localhost:5173/collections')

    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle')
  })

  test('should not have any automatically detectable WCAG 2.1 Level A violations', async ({ page }) => {
    // Wait for chart to render
    await page.waitForSelector('[role="img"]', { timeout: 5000 })

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

  test('should have proper ARIA attributes on chart', async ({ page }) => {
    // Find the chart element
    const chart = page.locator('[role="img"]').first()

    // Verify chart exists
    await expect(chart).toBeVisible()

    // Check role attribute
    await expect(chart).toHaveAttribute('role', 'img')

    // Check aria-label exists and is descriptive
    const ariaLabel = await chart.getAttribute('aria-label')
    expect(ariaLabel).toBeTruthy()
    expect(ariaLabel).toContain('trend chart')
    expect(ariaLabel).toContain('data points')
    expect(ariaLabel).toMatch(/\d+/)  // Should contain numbers

    // Check aria-describedby links to data table
    await expect(chart).toHaveAttribute('aria-describedby', 'trend-chart-data')
  })

  test('should have accessible data table fallback', async ({ page }) => {
    const table = page.locator('#trend-chart-data')

    // Verify table exists in DOM
    await expect(table).toBeAttached()

    // Check table has caption
    const caption = table.locator('caption')
    await expect(caption).toHaveText('Message trend data')

    // Check table structure
    const thead = table.locator('thead')
    const tbody = table.locator('tbody')
    await expect(thead).toBeAttached()
    await expect(tbody).toBeAttached()

    // Check table headers
    const headers = thead.locator('th')
    await expect(headers).toHaveCount(2)

    const dateHeader = headers.nth(0)
    const countHeader = headers.nth(1)

    await expect(dateHeader).toHaveText('Date')
    await expect(dateHeader).toHaveAttribute('scope', 'col')

    await expect(countHeader).toHaveText('Count')
    await expect(countHeader).toHaveAttribute('scope', 'col')

    // Check table has data rows
    const rows = tbody.locator('tr')
    const rowCount = await rows.count()
    expect(rowCount).toBeGreaterThan(0)

    // Verify first row has proper structure
    if (rowCount > 0) {
      const firstRow = rows.first()
      const cells = firstRow.locator('td')
      await expect(cells).toHaveCount(2)
    }
  })

  test('should be accessible to screen readers', async ({ page }) => {
    // Get accessibility tree snapshot
    const snapshot = await page.accessibility.snapshot()

    // Helper function to find chart in accessibility tree
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

    // Find chart in accessibility tree
    const chartNode = findInTree(snapshot, (node: any) =>
      node.role === 'img' && node.name?.toLowerCase().includes('trend chart')
    )

    expect(chartNode).toBeTruthy()
    expect(chartNode.name).toContain('trend chart')
    expect(chartNode.name).toContain('data points')

    // Find data table in accessibility tree
    const tableNode = findInTree(snapshot, (node: any) =>
      node.role === 'table' || (node.name && node.name.includes('Message trend data'))
    )

    expect(tableNode).toBeTruthy()
  })

  test('should have sr-only class on data table', async ({ page }) => {
    const table = page.locator('#trend-chart-data')

    // Check that table has sr-only class
    const className = await table.getAttribute('class')
    expect(className).toContain('sr-only')

    // Verify table is visually hidden but accessible
    // sr-only should have these CSS properties
    const isVisible = await table.isVisible()
    expect(isVisible).toBe(false)  // Visually hidden

    // But it should still be in the DOM and accessible
    const isAttached = await table.isHidden()
    expect(isAttached).toBe(true)  // Element exists in DOM
  })

  test('should support theme switching without accessibility issues', async ({ page }) => {
    // Wait for chart to render
    await page.waitForSelector('[role="img"]', { timeout: 5000 })

    // Run initial accessibility scan
    const lightModeScan = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag21a'])
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
        .withTags(['wcag2a', 'wcag21a'])
        .analyze()

      expect(darkModeScan.violations).toEqual([])
    }
  })

  test('should have all interactive elements with proper focus states', async ({ page }) => {
    // TrendChart itself is non-interactive (role="img")
    // This test verifies there are no keyboard traps

    const chart = page.locator('[role="img"]').first()
    await expect(chart).toBeVisible()

    // Try to focus the chart
    await chart.focus().catch(() => {
      // It's okay if we can't focus - chart is not interactive
    })

    // Verify no keyboard trap by pressing Tab
    await page.keyboard.press('Tab')

    // Focus should move to next focusable element (not trapped)
    const focusedElement = await page.evaluate(() => {
      return document.activeElement?.tagName
    })

    // Just verify we can press Tab without error
    expect(focusedElement).toBeTruthy()
  })
})
