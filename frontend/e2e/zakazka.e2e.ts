import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

async function expectNoSeriousA11yIssues(page: Page) {
	const results = await new AxeBuilder({ page }).analyze();
	const serious = results.violations.filter(
		(v) => v.impact === 'serious' || v.impact === 'critical'
	);
	expect(serious).toEqual([]);
}

test('úvod přesměruje na obrazovku zakázky', async ({ page }) => {
	await page.goto('/');

	await expect(page).toHaveURL(/\/project$/);
	await expect(page.getByRole('heading', { level: 1, name: 'Nová zakázka' })).toBeVisible();
});

test('obnovení na podstránce vrátí aplikaci (SPA)', async ({ page }) => {
	const response = await page.goto('/project');

	expect(response?.status()).toBe(200);
	await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
});

test.describe('široká obrazovka 1440 px', () => {
	test.use({ viewport: { width: 1440, height: 900 } });

	test('na prázdné obrazovce je jedno vstupní pole a asistent je sbalený', async ({ page }) => {
		await page.goto('/project');

		// Jediné pole pro zadání; asistent je sbalený a jde rozbalit (#61).
		await expect(page.getByRole('textbox', { name: 'Zadání zakázky' })).toBeVisible();
		await expect(page.getByRole('textbox', { name: 'Zpráva' })).toBeHidden();
		await page.getByRole('button', { name: 'Rozbalit asistenta' }).click();
		await expect(page.getByRole('region', { name: 'Asistent' })).toBeVisible();
		await expect(page.getByRole('heading', { name: 'Co potřebujete nařezat?' })).toBeVisible();
		await expect(page.locator('[aria-current="step"]')).toContainText('Zadání');
		await expect(page.getByRole('button', { name: 'Asistent', exact: true })).toBeHidden();
	});

	test('dialog jde sbalit a znovu rozbalit', async ({ page }) => {
		await page.goto('/project');

		await page.getByRole('button', { name: 'Rozbalit asistenta' }).click();
		await page.getByRole('button', { name: 'Sbalit asistenta' }).click();
		await expect(page.getByRole('region', { name: 'Asistent' })).toBeHidden();
		await page.getByRole('button', { name: 'Rozbalit asistenta' }).click();
		await expect(page.getByRole('region', { name: 'Asistent' })).toBeVisible();
	});

	test('ukázka z čipu se vloží do pole pro zprávu', async ({ page }) => {
		await page.goto('/project');
		await page.getByRole('button', { name: 'Rozbalit asistenta' }).click();

		await page.getByRole('button', { name: 'Sloupky a příčky' }).click();

		const field = page.getByRole('textbox', { name: 'Zpráva' });
		await expect(field).toBeFocused();
		await expect(field).toHaveValue(/12 sloupků/);
	});

	test('neaktivní akce mají důvod', async ({ page }) => {
		await page.goto('/project');

		await expect(
			page.getByRole('button', { name: 'Uložit zakázku', exact: true }).first()
		).toHaveAccessibleDescription('Uložit půjde až potvrzenou zakázku. Nejdřív potvrďte údaje.');
	});

	test('přístupnost: axe bez závažných nálezů', async ({ page }) => {
		await page.goto('/project');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

		await expectNoSeriousA11yIssues(page);
	});
});

test.describe('střední šířka 768 px', () => {
	test.use({ viewport: { width: 768, height: 1024 } });

	test('dialog se otevře jako vysouvací panel a Esc ho zavře', async ({ page }) => {
		await page.goto('/project');
		await expect(page.getByRole('region', { name: 'Asistent' })).toBeHidden();

		const open = page.getByRole('button', { name: 'Asistent', exact: true });
		await open.click();

		const sheet = page.getByRole('dialog', { name: 'Asistent' });
		await expect(sheet).toBeVisible();
		await expect(sheet.getByRole('textbox', { name: 'Zpráva' })).toBeVisible();

		await page.keyboard.press('Escape');
		await expect(sheet).toBeHidden();
		await expect(open).toBeFocused();
	});

	test('méně časté akce jsou v menu „⋯“', async ({ page }) => {
		await page.goto('/project');

		await page.getByRole('button', { name: 'Další akce se zakázkou' }).click();

		await expect(page.getByRole('menuitem', { name: /Načíst zakázku/ })).toBeVisible();
	});

	test('přístupnost: axe bez závažných nálezů', async ({ page }) => {
		await page.goto('/project');
		await expect(page.getByRole('heading', { level: 1 })).toBeVisible();

		await expectNoSeriousA11yIssues(page);
	});
});

test('nedostupný server ukáže celostránkovou chybu s nápravou', async ({ page }) => {
	await page.route('**/api/health', (route) => route.abort());
	await page.goto('/project');

	await expect(
		page.getByRole('heading', { name: 'Aplikace se nemůže spojit se svým serverem' })
	).toBeVisible();
	await expect(page.getByText('uv run decision-engine')).toBeVisible();

	await page.unroute('**/api/health');
	await page.getByRole('button', { name: 'Zkusit znovu' }).click();
	await expect(page.getByRole('heading', { level: 1, name: 'Nová zakázka' })).toBeVisible();
});
