import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

/**
 * Uložení a načtení zakázky (UC-06, kritérium „Import/export“ z kap. 9): soubor z běžící
 * aplikace se načte v nové relaci se stejnými vstupy včetně cíle; neplatný soubor
 * ukáže chybu a zakázku nezmění. Bez AI.
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

/** Ručně zadaná zakázka s cenou a cílem „nejméně tyčí“, spočítaná. */
async function plannedProject(page: Page) {
	await page.goto('/project');
	await page.getByRole('button', { name: 'Zadat ručně' }).click();
	await fillCell(page, 'Název zakázky', 'Regál do dílny');
	await fillCell(page, 'Díl 1, Název', 'noha');
	await fillCell(page, 'Díl 1, Délka', '1800');
	await fillCell(page, 'Díl 1, Počet', '4');
	await fillCell(page, 'Skladová délka 1, Cena za kus', '320,50');
	await fillCell(page, 'Prořez', '3');
	await page.getByRole('radio', { name: /Nejméně tyčí/ }).click();
	await page.getByRole('button', { name: 'Potvrdit a vypočítat' }).click();
	await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();
}

function loadDialog(page: Page) {
	return page.getByRole('dialog', { name: 'Načíst zakázku' });
}

test.beforeEach(async ({ context }) => {
	// Každé načtení stránky začíná novou relací.
	await context.addInitScript(() => sessionStorage.clear());
});

test.describe('široká obrazovka 1440 px', () => {
	test.use({ viewport: { width: 1440, height: 900 } });

	test('UC-06: uložená zakázka se načte se stejnými vstupy a spočítá', async ({ page }) => {
		await plannedProject(page);

		const downloading = page.waitForEvent('download');
		await page.getByRole('button', { name: 'Uložit zakázku' }).click();
		const download = await downloading;
		expect(download.suggestedFilename()).toBe('regal-do-dilny.decision.json');
		const file = await download.path();

		// Nová relace: prázdná zakázka, načtení ze souboru z kroku Zadání.
		await page.reload();
		await page.getByRole('button', { name: 'Načíst zakázku' }).click();
		await loadDialog(page).getByLabel('Soubor zakázky', { exact: true }).last().setInputFiles(file);

		await expect(loadDialog(page)).toBeHidden();
		await expect(page.getByRole('heading', { name: 'Kontrola údajů' })).toBeVisible();
		await expect(page.getByText('Zakázka načtena. Zkontrolujte údaje')).toBeVisible();
		await expect(page.getByRole('textbox', { name: 'Název zakázky' })).toHaveValue(
			'Regál do dílny'
		);
		await expect(page.getByRole('textbox', { name: 'Díl 1, Délka' })).toHaveValue('1800');
		await expect(page.getByRole('textbox', { name: 'Skladová délka 1, Cena za kus' })).toHaveValue(
			'320,50'
		);
		await expect(page.getByRole('radio', { name: /Nejméně tyčí/ })).toBeChecked();

		await page.getByRole('button', { name: 'Potvrdit a vypočítat' }).click();
		await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();
	});

	test('neplatný soubor ukáže chybu a zakázka zůstane', async ({ page }) => {
		await plannedProject(page);

		await page.getByRole('button', { name: 'Načíst', exact: true }).click();
		await expect(loadDialog(page).getByText('Aktuální zakázka bude nahrazena')).toBeVisible();
		await loadDialog(page)
			.getByLabel('Soubor zakázky', { exact: true })
			.last()
			.setInputFiles({
				name: 'nakup.json',
				mimeType: 'application/json',
				buffer: Buffer.from('{"polozky": ["šrouby"]}')
			});

		await expect(loadDialog(page).getByRole('alert')).toContainText(
			'Soubor není zakázka DecisionEngine.'
		);
		expect(await seriousA11yIssues(page)).toEqual([]);
		await page.keyboard.press('Escape');
		await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();
	});

	test('částečně neplatná data se načtou a chyby ukáže tabulka', async ({ page }) => {
		const data = {
			id: 'x',
			name: 'Rám',
			format_version: 1,
			task_type: 'cutting_1d',
			revision: 2,
			problem: {
				material: null,
				parts: [{ id: 'p1', name: 'příčka', length_mm: -5, quantity: 2 }],
				stock: [{ id: 's1', length_mm: 6000, price: null }]
			},
			parameters: { kerf_mm: 3, trim_mm: 0, min_remnant_mm: 300, objective: 'least_material' }
		};
		await page.goto('/project');
		await page.getByRole('button', { name: 'Načíst zakázku' }).click();
		await loadDialog(page)
			.getByLabel('Soubor zakázky', { exact: true })
			.last()
			.setInputFiles({
				name: 'ram.decision.json',
				mimeType: 'application/json',
				buffer: Buffer.from(JSON.stringify(data))
			});

		await expect(page.getByRole('heading', { name: 'Kontrola údajů' })).toBeVisible();
		await expect(page.getByRole('textbox', { name: 'Díl 1, Délka' })).toHaveAttribute(
			'aria-invalid',
			'true'
		);
		await expect(page.getByRole('button', { name: 'Potvrdit a vypočítat' })).toHaveAttribute(
			'aria-disabled',
			'true'
		);
	});

	test('bez potvrzené zakázky nejde uložit a důvod je u tlačítka', async ({ page }) => {
		await page.goto('/project');
		const save = page.getByRole('button', { name: 'Uložit', exact: true });
		await expect(save).toHaveAttribute('aria-disabled', 'true');
		await expect(save).toHaveAccessibleDescription('Uložit jde potvrzená zakázka.');
	});
});

test.describe('střední šířka 768 px', () => {
	test.use({ viewport: { width: 768, height: 1024 } });

	test('Načíst zakázku z menu „⋯“ a okno je přístupné', async ({ page }) => {
		await page.goto('/project');
		await page.getByRole('button', { name: 'Další akce se zakázkou' }).click();
		await page.getByRole('menuitem', { name: /Načíst zakázku/ }).click();
		await expect(loadDialog(page)).toBeVisible();
		expect(await seriousA11yIssues(page)).toEqual([]);
	});
});
