/**
 * Převod textu z buňky na číslo (komponenty.md, NumberUnitInput): přijímá čárku i tečku
 * a mezery jako oddělovač tisíců. Prázdné pole je `null` (chybějící hodnota).
 */

export type Parsed<T> = { ok: true; value: T | null } | { ok: false; message: string };

const SPACES = /[\s\u00a0\u202f]/g;

export function parseInteger(text: string): Parsed<number> {
	const clean = text.replace(SPACES, '');
	if (clean === '') return { ok: true, value: null };
	if (!/^-?\d+$/.test(clean)) return { ok: false, message: 'Zadejte celé číslo.' };
	return { ok: true, value: Number(clean) };
}

const UNIT_MM: Record<string, number> = { mm: 1, cm: 10, m: 1000 };

/** Délka v celých milimetrech; uživatel smí psát i cm nebo m („1,5 m“ → 1500, UC-13). */
export type ParsedLength =
	{ ok: true; value: number | null; converted: boolean } | { ok: false; message: string };

export function parseLength(text: string): ParsedLength {
	const clean = text.replace(SPACES, '').replace(',', '.').toLowerCase();
	if (clean === '') return { ok: true, value: null, converted: false };
	const match = /^(-?\d+(?:\.\d+)?)([a-z]*)$/.exec(clean);
	if (!match) return { ok: false, message: 'Zadejte délku číslem, např. 1200 nebo 1,2 m.' };
	const [, number, unit] = match;
	const factor = unit === '' ? 1 : UNIT_MM[unit];
	if (factor === undefined) return { ok: false, message: 'Zadejte délku v mm, cm nebo m.' };
	const mm = Number(number) * factor;
	const rounded = Math.round(mm);
	if (Math.abs(mm - rounded) > 1e-9) {
		return { ok: false, message: 'Délka musí vyjít na celé milimetry.' };
	}
	return { ok: true, value: rounded, converted: factor !== 1 };
}

/** Částka jako řetězec `Decimal` pro API (`1234.5`), aby se neztratila přesnost. */
export function parseMoney(text: string): Parsed<string> {
	const clean = text.replace(SPACES, '').replace(',', '.');
	if (clean === '') return { ok: true, value: null };
	if (!/^\d+(\.\d{1,2})?$/.test(clean)) {
		return { ok: false, message: 'Zadejte částku, nejvýš 2 desetinná místa.' };
	}
	return { ok: true, value: clean };
}

/** Hodnota pro zobrazení v buňce (bez jednotky; tu ukazuje pole). */
export function integerText(value: number | null): string {
	return value === null ? '' : String(value);
}

export function moneyText(value: string | null): string {
	return value === null ? '' : value.replace('.', ',');
}
