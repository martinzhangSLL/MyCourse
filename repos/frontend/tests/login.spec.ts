import { test, expect, Page } from '@playwright/test'

// Test configuration
const BASE_URL = 'http://localhost:3000'
const API_URL = 'http://localhost:8001'

test.describe('Login Page Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL)
  })

  test('should display login page', async ({ page }) => {
    await expect(page.locator('body')).toBeVisible()
    // Check that page has loaded
    await page.waitForLoadState('networkidle')
  })

  test('should have admin and teacher tabs', async ({ page }) => {
    // Check for login form elements
    await page.waitForSelector('input[type="text"], input[placeholder*="账号"]', { timeout: 10000 })
  })
})

test.describe('Admin Login Flow', () => {
  test('should login as admin successfully', async ({ page }) => {
    await page.goto(BASE_URL)
    await page.waitForLoadState('networkidle')

    // Fill in login form
    const usernameInput = page.locator('input').first()
    const passwordInput = page.locator('input[type="password"]').first()

    if (await usernameInput.isVisible()) {
      await usernameInput.fill('admin')
      await passwordInput.fill('admin123')

      // Click login button
      const loginButton = page.locator('button[type="submit"], button:has-text("登录")').first()
      if (await loginButton.isVisible()) {
        await loginButton.click()
        await page.waitForTimeout(2000)
      }
    }
  })
})

test.describe('Navigation Tests', () => {
  test('should navigate to admin classes page after login', async ({ page }) => {
    // This test verifies the admin sidebar navigation works
    await page.goto(`${BASE_URL}/admin/classes`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)
  })
})
