import { describe, expect, it, vi } from 'vitest';
import { page, userEvent } from 'vitest/browser';
import { render } from 'vitest-browser-svelte';
import ChatComposer from './ChatComposer.svelte';

describe('ChatComposer', () => {
	it('Enter odešle zprávu a vyprázdní pole', async () => {
		const onsend = vi.fn();
		await render(ChatComposer, { onsend });

		const field = page.getByRole('textbox', { name: 'Zpráva' });
		await field.click();
		await userEvent.keyboard('Dva sloupky 1 850 mm{Enter}');

		expect(onsend).toHaveBeenCalledWith('Dva sloupky 1 850 mm');
		await expect.element(field).toHaveValue('');
	});

	it('Shift+Enter vloží nový řádek a nic neodešle', async () => {
		const onsend = vi.fn();
		await render(ChatComposer, { onsend });

		const field = page.getByRole('textbox', { name: 'Zpráva' });
		await field.click();
		await userEvent.keyboard('první{Shift>}{Enter}{/Shift}druhý');

		expect(onsend).not.toHaveBeenCalled();
		await expect.element(field).toHaveValue('první\ndruhý');
	});

	it('prázdnou zprávu neodešle a řekne proč', async () => {
		const onsend = vi.fn();
		await render(ChatComposer, { onsend });

		const send = page.getByRole('button', { name: 'Odeslat' });
		await expect.element(send).toHaveAttribute('aria-disabled', 'true');
		await expect.element(send).toHaveAccessibleDescription('Nejdřív napište zprávu.');
		// aria-disabled tlačítko je záměrně klikatelné (kvůli tooltipu), klik nesmí nic odeslat.
		await send.click({ force: true });

		expect(onsend).not.toHaveBeenCalled();
	});

	it('vypnuté odesílání má důvod a zprávu nepošle ani Enterem', async () => {
		const onsend = vi.fn();
		await render(ChatComposer, { onsend, sendDisabledReason: 'Tato akce zatím není k dispozici.' });

		await page.getByRole('textbox', { name: 'Zpráva' }).click();
		await userEvent.keyboard('text{Enter}');

		expect(onsend).not.toHaveBeenCalled();
		await expect
			.element(page.getByRole('button', { name: 'Odeslat' }))
			.toHaveAccessibleDescription('Tato akce zatím není k dispozici.');
	});
});
