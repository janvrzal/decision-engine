import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

test('úvodní stránka se načte a hlásí spojení se serverem', async ({ page }) => {
	await page.goto('/');

	await expect(page.getByRole('heading', { level: 1, name: 'DecisionEngine' })).toBeVisible();
	await expect(page.getByRole('status')).toContainText('Spojení se serverem funguje');
});

test('obnovení na podstránce vrátí aplikaci (SPA)', async ({ page }) => {
	const response = await page.goto('/neexistujici/cesta');

	expect(response?.status()).toBe(200);
	await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
});

test('přístupnost: axe bez závažných nálezů', async ({ page }) => {
	await page.goto('/');
	await expect(page.getByRole('status')).toContainText('Spojení');

	const results = await new AxeBuilder({ page }).analyze();
	const serious = results.violations.filter(
		(v) => v.impact === 'serious' || v.impact === 'critical'
	);

	expect(serious).toEqual([]);
});
