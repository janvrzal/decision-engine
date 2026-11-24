import AxeBuilder from '@axe-core/playwright';
import { expect, test, type Page } from '@playwright/test';

/**
 * Hlavní tok UC-01 v prohlížeči (spec kap. 9 „UI – hlavní tok“): zadání v dialogu →
 * kontrola údajů → potvrzení → plán a metriky. Model AI se přehrává z
 * e2e/fixtures/uc01.json, solver i SVG jsou skutečné.
 */

const ZADANI = 'Regál: 4 nohy po 1 800 mm a 8 polic po 1 200 mm, tyče 6 m po 320 Kč, prořez 3 mm.';

async function seriousA11yIssues(page: Page) {
	const results = await new AxeBuilder({ page }).analyze();
	return results.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
}

async function sendMessage(page: Page, text: string) {
	const field = page.getByRole('textbox', { name: 'Zpráva' });
	await field.fill(text);
	await field.press('Enter');
}

async function toReview(page: Page) {
	await page.goto('/project');
	await sendMessage(page, ZADANI);
	await expect(page.getByRole('heading', { name: 'Kontrola údajů' })).toBeVisible();
}

test.beforeEach(async ({ context }) => {
	// Každý test začíná novou relací.
	await context.addInitScript(() => sessionStorage.clear());
});

test.describe('široká obrazovka 1440 px', () => {
	test.use({ viewport: { width: 1440, height: 900 } });

	test('UC-01: od zadání k plánu', async ({ page }) => {
		await toReview(page);

		// Kontrola údajů: díly z AI a nepotvrzené hodnoty označené.
		const parts = page.getByRole('table', { name: 'Díly' });
		await expect(parts.getByRole('textbox', { name: 'Díl 1, Název' })).toHaveValue('noha');
		await expect(parts.getByRole('textbox', { name: 'Díl 2, Délka' })).toHaveValue('1\u00a0200');
		const stockLength = page.getByRole('textbox', { name: 'Skladová délka 1, Délka tyče' });
		await expect(stockLength).toHaveAccessibleDescription(/Nepotvrzená hodnota/);
		await expect(page.getByText('Rozpoznal jsem 2 druhy dílů')).toBeVisible();

		// Uživatel opraví buňku: hodnota přestane být nepotvrzená.
		const remnant = page.getByRole('textbox', { name: 'Minimální využitelný zbytek' });
		await expect(remnant).toHaveAccessibleDescription(/Nepotvrzená hodnota/);
		await remnant.fill('400');
		await remnant.press('Tab');
		await expect(remnant).not.toHaveAccessibleDescription(/Nepotvrzená hodnota/);

		await page.getByRole('button', { name: 'Potvrdit a vypočítat' }).click();

		// Plán a cena: štítek, metriky, SVG a rozpis.
		await expect(page.getByRole('heading', { name: 'Nářezový plán' })).toBeVisible();
		await expect(page.locator('[data-status="best_found"]').first()).toContainText(
			'Nejlepší nalezený'
		);
		const plan = page.getByRole('img', { name: /Nářezový plán: .* tyč/ });
		await expect(plan).toBeVisible();
		await expect(page.getByText('Spotřebované tyče')).toBeVisible();
		await expect(page.getByText('Výtěžnost', { exact: true })).toBeVisible();
		await expect(
			page.getByRole('navigation', { name: 'Kroky zakázky' }).locator('[aria-current="step"]')
		).toContainText('Plán a cena');

		// Zvýraznění dílu z rozpisu po tyčích.
		await page.getByRole('button', { name: 'Rozpis po tyčích' }).click();
		await page.getByRole('button', { name: /^noha/ }).first().focus();
		await expect(page.locator('g[data-part-id="p1"][data-highlight]').first()).toBeAttached();

		expect(await seriousA11yIssues(page)).toEqual([]);
	});

	test('chybějící hodnota blokuje potvrzení s důvodem', async ({ page }) => {
		await toReview(page);

		const length = page.getByRole('textbox', { name: 'Díl 1, Délka' });
		await length.fill('');
		await length.press('Tab');

		const confirm = page.getByRole('button', { name: 'Potvrdit a vypočítat' });
		await expect(confirm).toHaveAttribute('aria-disabled', 'true');
		await expect(confirm).toHaveAccessibleDescription('Opravte 1 pole, než spustíte výpočet.');
		await expect(page.getByRole('alert')).toContainText('Díl 1, délka: Chybí hodnota.');
	});

	test('text, který není číslo, se hlásí u buňky a neodešle', async ({ page }) => {
		await toReview(page);

		const quantity = page.getByRole('textbox', { name: 'Díl 1, Počet' });
		await quantity.fill('čtyři');
		await quantity.press('Tab');

		await expect(quantity).toHaveAccessibleDescription('Zadejte celé číslo.');
	});

	test('klávesnice v tabulce: šipky, Enter přidá řádek, Esc vrátí hodnotu', async ({ page }) => {
		await toReview(page);

		const first = page.getByRole('textbox', { name: 'Díl 1, Název' });
		await first.focus();
		await page.keyboard.press('ArrowDown');
		await expect(page.getByRole('textbox', { name: 'Díl 2, Název' })).toBeFocused();

		await page.keyboard.type(' navíc');
		await page.keyboard.press('Escape');
		await expect(page.getByRole('textbox', { name: 'Díl 2, Název' })).toHaveValue('polička');

		await page.keyboard.press('Enter');
		await expect(page.getByRole('textbox', { name: 'Díl 3, Název' })).toBeFocused();
	});

	test('nepotvrzený návrh označí plán jako neaktuální', async ({ page }) => {
		await toReview(page);
		await page.getByRole('button', { name: 'Potvrdit a vypočítat' }).click();
		// Počkat na hotový plán: během výpočtu je odeslání zprávy záměrně neaktivní.
		await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();

		await sendMessage(page, 'Přidej příčky ať jsou 850 mm, 4 kusy.');

		await expect(page.getByRole('heading', { name: 'Kontrola údajů' })).toBeVisible();
		await expect(page.getByText('Úprava zakázky')).toBeVisible();
		await page.getByRole('button', { name: /Plán a cena/ }).click();
		await expect(page.getByText(/Neaktuální:.*čekají nepotvrzené změny/)).toBeVisible();
	});

	test('úprava a přepočet: Zahodit změny vrátí aktuální plán, potvrzení spočítá nový', async ({
		page
	}) => {
		await toReview(page);
		await page.getByRole('button', { name: 'Potvrdit a vypočítat' }).click();
		await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();
		const stale = page.getByText(/Neaktuální/);
		await expect(stale).toHaveCount(0);

		// Rozpracovaná úprava: plán je neaktuální, zakázka se nemění.
		await page.getByRole('button', { name: 'Upravit údaje' }).click();
		const length = page.getByRole('textbox', { name: 'Díl 1, Délka' });
		await length.fill('1900');
		await length.press('Tab');
		await expect(length).toHaveValue('1\u00a0900');
		await page.getByRole('button', { name: /Plán a cena/ }).click();
		await expect(page.getByText(/Neaktuální:.*čekají nepotvrzené změny/)).toBeVisible();

		// Zahodit změny vrátí poslední potvrzenou revizi a plán je zase aktuální.
		await page.getByRole('button', { name: 'Zkontrolovat změny' }).first().click();
		await page.getByRole('button', { name: 'Zahodit změny' }).click();
		await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();
		await expect(stale).toHaveCount(0);
		await page.getByRole('button', { name: 'Upravit údaje' }).click();
		await expect(length).toHaveValue('1\u00a0800');

		// Potvrzená úprava spočítá nový plán z nové hodnoty.
		await length.fill('1900');
		await length.press('Tab');
		await page.getByRole('button', { name: 'Potvrdit a vypočítat' }).click();
		await expect(page.getByRole('img', { name: /Nářezový plán: .* tyč/ })).toBeVisible();
		await expect(stale).toHaveCount(0);
		await page.getByRole('button', { name: 'Upravit údaje' }).click();
		await expect(length).toHaveValue('1\u00a0900');
	});

	test('odkaz v souhrnu chyb přesune fokus na pole', async ({ page }) => {
		await toReview(page);

		const length = page.getByRole('textbox', { name: 'Díl 1, Délka' });
		await length.fill('');
		await length.press('Tab');
		await page.getByRole('link', { name: 'Díl 1, délka: Chybí hodnota.' }).click();

		await expect(length).toBeFocused();
		expect(await seriousA11yIssues(page)).toEqual([]);
	});

	test('čísla v buňkách se po potvrzení ukážou ve formátu cs-CZ', async ({ page }) => {
		await toReview(page);

		const length = page.getByRole('textbox', { name: 'Skladová délka 1, Délka tyče' });
		await expect(length).toHaveValue('6\u00a0000');
		await length.fill('12500');
		await expect(length).toHaveValue('12500'); // během psaní se text nemění
		await length.press('Tab');
		await expect(length).toHaveValue('12\u00a0500');

		const price = page.getByRole('textbox', { name: 'Skladová délka 1, Cena za kus' });
		await price.fill('1234,5');
		await price.press('Tab');
		await expect(price).toHaveValue('1\u00a0234,50');
	});

	test('výpadek AI ukáže chybu s nabídkou zkusit znovu', async ({ page }) => {
		await page.goto('/project');

		await sendMessage(page, 'simuluj výpadek AI');

		const alert = page.getByRole('alert');
		await expect(alert).toContainText('AI teď neodpovídá');
		await expect(alert.getByRole('button', { name: 'Zkusit znovu' })).toBeVisible();
	});
});

test.describe('střední šířka 768 px', () => {
	test.use({ viewport: { width: 768, height: 1024 } });

	test('kontrola údajů a plán jsou použitelné a přístupné', async ({ page }) => {
		await page.goto('/project');
		await page.getByRole('button', { name: 'Dialog', exact: true }).click();
		await sendMessage(page, ZADANI);
		await expect(page.getByRole('heading', { name: 'Kontrola údajů' })).toBeVisible();
		expect(await seriousA11yIssues(page)).toEqual([]);

		// Souhrn chyb s odkazem je přístupný i na střední šířce.
		const length = page.getByRole('textbox', { name: 'Díl 1, Délka' });
		await length.fill('');
		await length.press('Tab');
		await page.getByRole('link', { name: 'Díl 1, délka: Chybí hodnota.' }).click();
		await expect(length).toBeFocused();
		expect(await seriousA11yIssues(page)).toEqual([]);
		await length.fill('1800');
		await length.press('Tab');

		await page.getByRole('button', { name: 'Potvrdit a vypočítat' }).click();
		await expect(page.getByRole('heading', { name: 'Nářezový plán' })).toBeVisible();
		expect(await seriousA11yIssues(page)).toEqual([]);
	});
});
