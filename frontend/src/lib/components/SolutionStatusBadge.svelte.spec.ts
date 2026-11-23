import { describe, expect, it } from 'vitest';
import { page } from 'vitest/browser';
import { render } from 'vitest-browser-svelte';
import SolutionStatusBadge from './SolutionStatusBadge.svelte';

describe('SolutionStatusBadge', () => {
	it('stav má text i ikonu, ne jen barvu', async () => {
		await render(SolutionStatusBadge, { status: 'partial', label: 'Částečný' });

		const badge = page.getByText('Částečný');
		await expect.element(badge).toBeVisible();
		expect(document.querySelector('[data-status="partial"] svg')).not.toBeNull();
	});

	it('neaktuální výsledek přebije štítek stavu', async () => {
		await render(SolutionStatusBadge, {
			status: 'best_found',
			label: 'Nejlepší nalezený',
			stale: true
		});

		await expect.element(page.getByText('Neaktuální')).toBeVisible();
		expect(document.querySelector('[data-status="stale"]')).not.toBeNull();
	});
});
