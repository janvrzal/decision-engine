import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

/**
 * Nová zakázka s ochranou neuložené práce (UC-15) a načtení souboru přes rozpracovanou
 * zakázku (UC-06 A1). Bez AI, solver je skutečný.
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

async function plannedProject(page: Page) {
	await page.goto('/project');
	await page.getByRole('button', { name: 'Zadat ručně' }).click();
	await fillCell(page, 'Název zakázky', 'Plot zahrada');
	await fillCell(page, 'Díl 1, Název', 'plaňka');
	await fillCell(page, 'Díl 1, Délka', '1200');
	await fillCell(page, 'Díl 1, Počet', '10');
	await fillCell(page, 'Prořez', '3');
	await page.getByRole('button', { name: 'Potvrdit a vypočítat' }).click();
	await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();
}

async function saveToFile(page: Page): Promise<string> {
	const downloading = page.waitForEvent('download');
	await page.getByRole('button', { name: 'Uložit zakázku' }).click();
	const file = await (await downloading).path();
	await expect(page.getByText('neuloženo', { exact: true })).toBeHidden();
	return file;
}

function discardDialog(page: Page) {
	return page.getByRole('alertdialog', { name: 'Zahodit rozpracovanou zakázku?' });
}

async function expectEmptyProject(page: Page) {
	await expect(page.getByRole('heading', { level: 1, name: 'Nová zakázka' })).toBeVisible();
	await expect(page.getByRole('heading', { name: 'Co potřebujete nařezat?' })).toBeVisible();
	await expect(page.getByText('neuloženo', { exact: true })).toBeHidden();
}

test.beforeEach(async ({ context }) => {
	await context.addInitScript(() => sessionStorage.clear());
});

test.describe('široká obrazovka 1440 px', () => {
	test.use({ viewport: { width: 1440, height: 900 } });

	test('uložená zakázka: Nová zakázka bez ptaní začne prázdnou', async ({ page }) => {
		await plannedProject(page);
		await expect(page.getByText('neuloženo', { exact: true })).toBeVisible();
		await saveToFile(page);

		await page.getByRole('button', { name: 'Nová zakázka', exact: true }).click();

		await expect(discardDialog(page)).toBeHidden();
		await expectEmptyProject(page);
	});

	test('neuložená zakázka: Zrušit nic nezmění, Zahodit začne znovu', async ({ page }) => {
		await plannedProject(page);

		await page.getByRole('button', { name: 'Nová zakázka', exact: true }).click();
		await expect(discardDialog(page)).toContainText('Zakázka „Plot zahrada“ má neuložené změny.');
		await expect(discardDialog(page).getByRole('button', { name: 'Zrušit' })).toBeFocused();
		expect(await seriousA11yIssues(page)).toEqual([]);

		await discardDialog(page).getByRole('button', { name: 'Zrušit' }).click();
		await expect(discardDialog(page)).toBeHidden();
		await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();

		await page.getByRole('button', { name: 'Nová zakázka', exact: true }).click();
		await discardDialog(page).getByRole('button', { name: 'Zahodit zakázku' }).click();
		await expectEmptyProject(page);
	});

	test('Uložit a pokračovat stáhne soubor a začne novou zakázku', async ({ page }) => {
		await plannedProject(page);

		await page.getByRole('button', { name: 'Nová zakázka', exact: true }).click();
		const downloading = page.waitForEvent('download');
		await discardDialog(page).getByRole('button', { name: 'Uložit a pokračovat' }).click();
		expect((await downloading).suggestedFilename()).toBe('plot-zahrada.decision.json');

		await expectEmptyProject(page);
	});

	test('načtení platného souboru přes rozpracovanou zakázku se nejdřív zeptá', async ({ page }) => {
		await plannedProject(page);
		const file = await saveToFile(page);
		await page.getByRole('button', { name: 'Upravit údaje' }).click();
		await fillCell(page, 'Díl 1, Počet', '12');
		await expect(page.getByText('neuloženo', { exact: true })).toBeVisible();

		await page.getByRole('button', { name: 'Načíst zakázku', exact: true }).click();
		const load = page.getByRole('dialog', { name: 'Načíst zakázku' });
		await load.getByLabel('Soubor zakázky', { exact: true }).last().setInputFiles(file);

		await expect(load).toBeHidden();
		await discardDialog(page).getByRole('button', { name: 'Zahodit a načíst' }).click();
		await expect(page.getByText('Zakázka načtena. Zkontrolujte údaje')).toBeVisible();
		await expect(page.getByRole('textbox', { name: 'Díl 1, Počet' })).toHaveValue('10');
	});

	test('neplatný soubor ukáže chybu a na zahození se neptá', async ({ page }) => {
		await plannedProject(page);

		await page.getByRole('button', { name: 'Načíst zakázku', exact: true }).click();
		const load = page.getByRole('dialog', { name: 'Načíst zakázku' });
		await load
			.getByLabel('Soubor zakázky', { exact: true })
			.last()
			.setInputFiles({
				name: 'nakup.json',
				mimeType: 'application/json',
				buffer: Buffer.from('{"polozky": []}')
			});

		await expect(load.getByRole('alert')).toContainText('Soubor není zakázka DecisionEngine.');
		await expect(discardDialog(page)).toBeHidden();
	});

	test('netknutý ruční formulář se zahodí bez ptaní', async ({ page }) => {
		await page.goto('/project');
		await page.getByRole('button', { name: 'Zadat ručně' }).click();
		await expect(page.getByRole('heading', { name: 'Kontrola údajů' })).toBeVisible();

		await page.getByRole('button', { name: 'Nová zakázka', exact: true }).click();

		await expect(discardDialog(page)).toBeHidden();
		await expectEmptyProject(page);
	});
});

test.describe('střední šířka 768 px', () => {
	test.use({ viewport: { width: 768, height: 1024 } });

	test('Nová zakázka z menu „⋯“ a přístupné potvrzení', async ({ page }) => {
		await plannedProject(page);

		await page.getByRole('button', { name: 'Další akce se zakázkou' }).click();
		await page.getByRole('menuitem', { name: /Nová zakázka/ }).click();

		await expect(discardDialog(page)).toBeVisible();
		expect(await seriousA11yIssues(page)).toEqual([]);
		await discardDialog(page).getByRole('button', { name: 'Zahodit zakázku' }).click();
		await expectEmptyProject(page);
	});
});
