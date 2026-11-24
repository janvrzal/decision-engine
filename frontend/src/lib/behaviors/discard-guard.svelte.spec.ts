import { describe, expect, it } from 'vitest';
import { DiscardGuard } from './discard-guard.svelte';

function setup(unsaved: { value: boolean }, saveError: string | null = null) {
	const runs: boolean[] = [];
	let saves = 0;
	let releaseSave: () => void = () => {};
	const guard = new DiscardGuard(
		() => unsaved.value,
		() =>
			new Promise((resolve) => {
				saves += 1;
				releaseSave = () => resolve(saveError);
			})
	);
	const action = {
		label: 'Zahodit zakázku',
		run: (discard: boolean) => {
			runs.push(discard);
			return Promise.resolve(true);
		}
	};
	return { guard, action, runs, saves: () => saves, releaseSave: () => releaseSave() };
}

describe('DiscardGuard', () => {
	it('provedená akce dialog neotevře, i když po ní je práce neuložená', async () => {
		const unsaved = { value: false };
		const { guard } = setup(unsaved);

		await guard.request({
			label: 'Zahodit a načíst',
			run: () => {
				unsaved.value = true; // načtená zakázka ještě není uložená
				return Promise.resolve(true);
			}
		});

		expect(guard.open).toBe(false);
	});

	it('bez neuložené práce akci provede rovnou', async () => {
		const { guard, action, runs } = setup({ value: false });

		await guard.request(action);

		expect(runs).toEqual([false]);
		expect(guard.open).toBe(false);
	});

	it('s neuloženou prací se zeptá a po zahození pošle potvrzení', async () => {
		const { guard, action, runs } = setup({ value: true });

		await guard.request(action);
		expect(guard.open).toBe(true);
		expect(runs).toEqual([]);

		await guard.proceed(false);
		expect(runs).toEqual([true]);
		expect(guard.open).toBe(false);
	});

	it('když backend akci odmítne kvůli neuložené práci, dialog se otevře', async () => {
		const unsaved = { value: false };
		const { guard, runs } = setup(unsaved);

		await guard.request({
			label: 'Zahodit zakázku',
			run: (discard) => {
				runs.push(discard);
				unsaved.value = true; // čerstvý stav z backendu: práce neuložená
				return Promise.resolve(false); // backend akci odmítl
			}
		});

		expect(runs).toEqual([false]);
		expect(guard.open).toBe(true);
	});

	it('zrušení během ukládání akci neprovede', async () => {
		const { guard, action, runs, releaseSave } = setup({ value: true });
		await guard.request(action);

		const proceeding = guard.proceed(true);
		guard.open = false; // „Zrušit“ v dialogu
		releaseSave();
		await proceeding;

		expect(runs).toEqual([]);
	});

	it('chyba uložení nechá dialog otevřený s hláškou', async () => {
		const { guard, action, runs, releaseSave } = setup({ value: true }, 'Disk je plný.');
		await guard.request(action);

		const proceeding = guard.proceed(true);
		releaseSave();
		await proceeding;

		expect(guard.error).toBe('Disk je plný.');
		expect(guard.open).toBe(true);
		expect(runs).toEqual([]);
	});
});
