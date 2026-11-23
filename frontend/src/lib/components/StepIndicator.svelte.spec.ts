import { describe, expect, it, vi } from 'vitest';
import { page } from 'vitest/browser';
import { render } from 'vitest-browser-svelte';
import StepIndicator from './StepIndicator.svelte';
import type { StepView } from '#lib/api/types.js';

const steps: StepView[] = [
	{ id: 'input', label: 'Zadání', state: 'done' },
	{ id: 'review', label: 'Kontrola údajů', state: 'active' },
	{ id: 'result', label: 'Plán a cena', state: 'stale' }
];

describe('StepIndicator', () => {
	it('aktivní krok má aria-current a stav i textem', async () => {
		await render(StepIndicator, { steps });

		const current = () => document.querySelector('[aria-current="step"]')?.textContent ?? '';
		await expect.poll(current).toContain('Kontrola údajů');
		expect(current()).toContain('aktuální krok');
	});

	it('neaktuální krok má slovo „neaktuální“, ne jen barvu', async () => {
		await render(StepIndicator, { steps });

		await expect.element(page.getByText('neaktuální', { exact: true })).toBeInTheDocument();
	});

	it('hotový krok je tlačítko zpět', async () => {
		const onselect = vi.fn();
		await render(StepIndicator, { steps, onselect });

		await page.getByRole('button', { name: /Zadání/ }).click();

		expect(onselect).toHaveBeenCalledWith('input');
	});
});
