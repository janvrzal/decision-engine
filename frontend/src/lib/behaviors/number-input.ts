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
