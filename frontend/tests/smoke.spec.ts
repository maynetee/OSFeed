import { test, expect } from '@playwright/test'

test('login flow reaches dashboard', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('button', { name: 'Se connecter' }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
})
