import { test, expect, type Page } from '@playwright/test'

const login = async (page: Page) => {
  await page.addInitScript(() => {
    localStorage.setItem('osfeed_language', 'fr')
  })
  await page.goto('/login')
  await page.getByRole('button', { name: 'Se connecter' }).click()
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible()
}

test('login flow reaches dashboard', async ({ page }) => {
  await login(page)
})

test('navigation to feed opens export dialog', async ({ page }) => {
  await login(page)
  await page.getByRole('link', { name: 'Fil' }).click()
  await expect(page.getByRole('heading', { name: 'Signaux prioritaires' })).toBeVisible()
  await page.getByRole('button', { name: 'Exporter' }).click()
  await expect(page.getByRole('heading', { name: 'Exporter les signaux' })).toBeVisible()
})

test('search page shows tabs', async ({ page }) => {
  await login(page)
  await page.getByRole('link', { name: 'Recherche' }).click()
  await expect(page.getByRole('heading', { name: 'Recherche', level: 2 })).toBeVisible()
  await expect(page.getByRole('tab', { name: 'Semantique' })).toBeVisible()
  await expect(page.getByRole('tab', { name: 'Mot-cle' })).toBeVisible()
  await expect(page.getByRole('tab', { name: 'Entites' })).toBeVisible()
})
