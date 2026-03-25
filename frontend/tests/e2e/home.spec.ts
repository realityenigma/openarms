import { test, expect } from '@playwright/test'

test('homepage loads and tab switch works', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Armswideopen Hub' })).toBeVisible()

  await page.getByRole('button', { name: 'Datasets' }).click()
  await expect(page.getByText('Showing')).toContainText('datasets')

  await page.getByRole('button', { name: 'Models' }).click()
  await expect(page.getByText('Showing')).toContainText('models')
})
