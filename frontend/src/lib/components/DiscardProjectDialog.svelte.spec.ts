import { describe, expect, it, vi } from 'vitest';
import { page, userEvent } from 'vitest/browser';
import { render } from 'vitest-browser-svelte';
import DiscardProjectDialog from './DiscardProjectDialog.svelte';

const base = {
	open: true,
	name: 'Plot zahrada',
	hasProject: true,
	hasProposal: false,
	discardLabel: 'Zahodit zakázku',
	busy: false,
	error: null
};

describe('DiscardProjectDialog', () => {
	it('začíná fokusem na Zrušit a Esc nic nezahodí', async () => {
		const ondiscard = vi.fn();
		await render(DiscardProjectDialog, { ...base, onsave: vi.fn(), ondiscard });

		await expect
			.element(page.getByRole('alertdialog', { name: 'Zahodit rozpracovanou zakázku?' }))
			.toBeVisible();
		await expect
			.element(page.getByText('Zakázka „Plot zahrada“ má neuložené změny.'))
			.toBeVisible();
		await expect.element(page.getByRole('button', { name: 'Zrušit' })).toHaveFocus();

		await userEvent.keyboard('{Escape}');
		await expect.element(page.getByRole('alertdialog')).not.toBeInTheDocument();
		expect(ondiscard).not.toHaveBeenCalled();
	});

	it('rozpracovaný návrh bez potvrzené zakázky uložit nejde, zahodit ano', async () => {
		const ondiscard = vi.fn();
		await render(DiscardProjectDialog, { ...base, hasProject: false, onsave: vi.fn(), ondiscard });

		const save = page.getByRole('button', { name: 'Uložit a pokračovat' });
		await expect.element(save).toHaveAttribute('aria-disabled', 'true');
		await expect
			.element(save)
			.toHaveAccessibleDescription('Uložit půjde až potvrzenou zakázku. Nejdřív potvrďte údaje.');

		await page.getByRole('button', { name: 'Zahodit zakázku' }).click();
		expect(ondiscard).toHaveBeenCalledOnce();
	});

	it('chyba uložení zůstane v okně', async () => {
		await render(DiscardProjectDialog, {
			...base,
			error: 'Server neodpovídá, zakázka se neuložila.',
			onsave: vi.fn(),
			ondiscard: vi.fn()
		});

		await expect.element(page.getByText('Zakázka se neuložila', { exact: true })).toBeVisible();
		await expect
			.element(page.getByText('Server neodpovídá, zakázka se neuložila.', { exact: true }))
			.toBeVisible();
	});
});
