import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

/**
 * Ruční zadání bez AI (UC-13, UC-07): tabulka vyplněná klávesnicí → plán, úprava
 * potvrzené zakázky („Upravit údaje“) a ruční cesta z chyby AI. Solver je skutečný.
 */

async function seriousA11yIssues(page: Page) {
	const results = await new AxeBuilder({ page }).analyze();
	return results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
}

async function fillCell(page: Page, name: string, value: string) {
	const cell = page.getByRole('textbox', { name, exact: true });
	await cell.fill(value);
	await cell.press('Tab');
}

/** Ruční zadání regálu od karty nástroje až k plánu. */
async function manualPlan(page: Page) {
	await page.goto('/project');
	await page.getByRole('button', { name: /^Řezání tyčí/ }).click();
	await expect(page.getByRole('heading', { name: 'Kontrola údajů' })).toBeVisible();

	// Prázdný formulář začíná fokusem v prvním řádku dílů a nehlásí chyby předem.
	const firstName = page.getByRole('textbox', { name: 'Díl 1, Název' });
	await expect(firstName).toBeFocused();
	await expect(page.getByRole('alert')).toHaveCount(0);

	await fillCell(page, 'Díl 1, Název', 'noha');
	await fillCell(page, 'Díl 1, Délka', '1,8 m');
	await expect(page.getByRole('status').filter({ hasText: 'Převedeno' })).toContainText(
		'1,8 m = 1 800 mm'
	);
	await expect(page.getByRole('textbox', { name: 'Díl 1, Délka' })).toHaveValue('1\u00a0800');
	await fillCell(page, 'Díl 1, Počet', '4');
	await fillCell(page, 'Prořez', '3');

	const confirm = page.getByRole('button', { name: 'Potvrdit a vypočítat' });
	await expect(confirm).not.toHaveAttribute('aria-disabled', 'true');
	await confirm.click();
	await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();
}

test.beforeEach(async ({ context }) => {
	await context.addInitScript(() => sessionStorage.clear());
});

test.describe('široká obrazovka 1440 px', () => {
	test.use({ viewport: { width: 1440, height: 900 } });

	test('UC-13: ruční zadání od karty nástroje k plánu', async ({ page }) => {
		await manualPlan(page);
		await expect(page.getByText('Spotřebované tyče')).toBeVisible();
		expect(await seriousA11yIssues(page)).toEqual([]);
	});

	test('prořez 2,5 mm a Ctrl+Enter spočítá plán s desetinnými polohami řezů', async ({ page }) => {
		await page.goto('/project');
		await page.getByRole('button', { name: 'Zadat ručně' }).click();
		await fillCell(page, 'Díl 1, Název', 'příčka');
		await fillCell(page, 'Díl 1, Délka', '1000');
		await fillCell(page, 'Díl 1, Počet', '3');
		await fillCell(page, 'Prořez', '2,5');
		await expect(page.getByRole('textbox', { name: 'Prořez' })).toHaveValue('2,5');

		await page.getByRole('textbox', { name: 'Prořez' }).press('Control+Enter');

		await expect(page.getByRole('img', { name: /Nářezový plán: .*prořez 2,5/ })).toBeVisible();
		await page.getByRole('button', { name: 'Rozpis po tyčích' }).click();
		await expect(page.getByText('1\u00a0000\u00a0mm, 2\u00a0002,5\u00a0mm').first()).toBeVisible();
	});

	test('rychlé vyplňování buněk za sebou žádnou hodnotu neztratí', async ({ page }) => {
		await page.goto('/project');
		await page.getByRole('button', { name: 'Zadat ručně' }).click();

		// Bez čekání: další buňka se potvrdí, zatímco backend ještě odpovídá na předchozí.
		for (const [name, value] of [
			['Díl 1, Název', 'noha'],
			['Díl 1, Délka', '1800'],
			['Díl 1, Počet', '4'],
			['Prořez', '3']
		]) {
			const cell = page.getByRole('textbox', { name, exact: true });
			await cell.fill(value);
			await cell.press('Tab');
		}

		await expect(page.getByRole('textbox', { name: 'Díl 1, Délka' })).toHaveValue('1\u00a0800');
		await expect(page.getByRole('textbox', { name: 'Díl 1, Počet' })).toHaveValue('4');
		await expect(page.getByRole('button', { name: 'Potvrdit a vypočítat' })).not.toHaveAttribute(
			'aria-disabled',
			'true'
		);
	});

	test('Upravit údaje: změna potvrzené zakázky a nový plán', async ({ page }) => {
		await manualPlan(page);

		await page.getByRole('button', { name: 'Upravit údaje' }).click();
		await expect(page.getByRole('heading', { name: 'Kontrola údajů' })).toBeVisible();
		await expect(page.getByText('Úprava zakázky')).toBeVisible();
		await expect(page.getByRole('textbox', { name: 'Díl 1, Délka' })).toHaveValue('1\u00a0800');

		await fillCell(page, 'Díl 1, Počet', '6');
		await page.getByRole('button', { name: 'Potvrdit a vypočítat' }).click();
		await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();
		await expect(page.getByText(/Neaktuální/)).toHaveCount(0);
	});

	test('krok Kontrola údajů nad potvrzenou zakázkou nabídne úpravu', async ({ page }) => {
		await manualPlan(page);

		await page.getByRole('button', { name: /Kontrola údajů/ }).click();
		await expect(page.getByRole('heading', { name: 'Údaje jsou potvrzené' })).toBeVisible();
		await page.getByRole('button', { name: 'Upravit údaje' }).click();
		await expect(page.getByRole('textbox', { name: 'Díl 1, Název' })).toHaveValue('noha');
	});

	test('UC-07: z chyby AI vede ruční cesta do tabulky', async ({ page }) => {
		await page.goto('/project');
		await page.getByRole('textbox', { name: 'Zadání zakázky' }).fill('simuluj výpadek AI');
		await page.getByRole('button', { name: 'Zpracovat zadání' }).click();

		// Chyba je v dialogu i u hlavního pole kroku Zadání, kam uživatel psal.
		const alert = page.getByRole('main').getByRole('alert');
		await expect(alert).toContainText('AI teď neodpovídá');
		await expect(page.getByRole('log').getByRole('alert')).toBeVisible();
		await alert.getByRole('button', { name: 'Zadat ručně' }).click();

		await expect(page.getByRole('heading', { name: 'Kontrola údajů' })).toBeVisible();
		await expect(page.getByRole('textbox', { name: 'Díl 1, Název' })).toBeFocused();
	});
});

test.describe('střední šířka 768 px', () => {
	test.use({ viewport: { width: 768, height: 1024 } });

	test('ruční zadání je použitelné a přístupné', async ({ page }) => {
		await page.goto('/project');
		await page.getByRole('button', { name: 'Zadat ručně' }).click();
		await expect(page.getByRole('heading', { name: 'Kontrola údajů' })).toBeVisible();
		expect(await seriousA11yIssues(page)).toEqual([]);
	});
});
