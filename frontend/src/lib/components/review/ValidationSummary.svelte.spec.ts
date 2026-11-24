import { afterEach, describe, expect, it } from 'vitest';
import { page } from 'vitest/browser';
import { render } from 'vitest-browser-svelte';
import ValidationSummary from './ValidationSummary.svelte';

/** Formulář s poli, na která vedou odkazy (jako v kroku Kontrola údajů). */
function form(): HTMLElement {
	const root = document.createElement('section');
	root.innerHTML = `
		<div data-cell="parts">
			<input aria-label="Díl 1, Délka" data-cell="parts.0.length_mm" />
			<input aria-label="Díl 2, Délka" data-cell="parts.1.length_mm" />
		</div>
		<div data-cell="parameters.objective">
			<button role="radio" aria-checked="false">Nejnižší cena</button>
			<button role="radio" aria-checked="true">Nejméně tyčí</button>
		</div>`;
	document.body.append(root);
	return root;
}

afterEach(() => document.querySelector('section')?.remove());

describe('ValidationSummary', () => {
	it('odkaz přesune fokus na pole s chybou', async () => {
		const scope = form();
		await render(ValidationSummary, {
			title: 'Opravte 1 pole, než spustíte výpočet.',
			errors: [{ field: 'Díl 2, délka', message: 'Chybí hodnota.', target: 'parts.1.length_mm' }],
			scope
		});

		await page.getByRole('link', { name: 'Díl 2, délka: Chybí hodnota.' }).click();

		await expect.element(page.getByRole('textbox', { name: 'Díl 2, Délka' })).toHaveFocus();
	});

	it('chyba tabulky vede na první buňku a chyba cíle na vybranou volbu', async () => {
		const scope = form();
		await render(ValidationSummary, {
			title: 'Opravte 2 pole, než spustíte výpočet.',
			errors: [
				{ field: 'Díly', message: 'Přidejte aspoň jeden díl.', target: 'parts' },
				{ field: 'Cíl optimalizace', message: 'Chybí hodnota.', target: 'parameters.objective' }
			],
			scope
		});

		await page.getByRole('link', { name: /Díly/ }).click();
		await expect.element(page.getByRole('textbox', { name: 'Díl 1, Délka' })).toHaveFocus();

		await page.getByRole('link', { name: /Cíl optimalizace/ }).click();
		await expect.element(page.getByRole('radio', { name: 'Nejméně tyčí' })).toHaveFocus();
	});

	it('chyba bez pole ve formuláři zůstane textem', async () => {
		await render(ValidationSummary, {
			title: 'Opravte 1 pole, než spustíte výpočet.',
			errors: [{ field: 'Zakázka', message: 'Neplatná data.', target: null }]
		});

		await expect.element(page.getByText('Zakázka: Neplatná data.')).toBeVisible();
		expect(page.getByRole('link').elements()).toHaveLength(0);
	});
});
