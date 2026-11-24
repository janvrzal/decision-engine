import { describe, expect, it, vi } from 'vitest';
import { page, userEvent } from 'vitest/browser';
import { render } from 'vitest-browser-svelte';
import ImportDialog from './ImportDialog.svelte';

describe('ImportDialog', () => {
	it('stará chyba z dřívějšího pokusu se při otevření neukáže', async () => {
		await render(ImportDialog, {
			open: true,
			busy: false,
			error: 'Soubor není zakázka DecisionEngine.',
			onimport: vi.fn()
		});

		await expect.element(page.getByRole('dialog', { name: 'Načíst zakázku' })).toBeVisible();
		expect(document.body.textContent).not.toContain('Soubor není zakázka');
	});

	it('vybraný soubor přečte a pošle', async () => {
		const onimport = vi.fn().mockResolvedValue(undefined);
		await render(ImportDialog, {
			open: true,
			busy: false,
			error: null,
			onimport
		});

		const file = new File(['{"format_version": 1}'], 'regal.decision.json', {
			type: 'application/json'
		});
		await userEvent.upload(page.getByLabelText('Soubor zakázky', { exact: true }).last(), file);

		await vi.waitFor(() => expect(onimport).toHaveBeenCalledWith('{"format_version": 1}'));
	});

	it('Esc okno zavře', async () => {
		await render(ImportDialog, {
			open: true,
			busy: false,
			error: null,
			onimport: vi.fn()
		});
		await expect.element(page.getByRole('dialog')).toBeVisible();

		await userEvent.keyboard('{Escape}');

		await expect.element(page.getByRole('dialog')).not.toBeInTheDocument();
	});
});
