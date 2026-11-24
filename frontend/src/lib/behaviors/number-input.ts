import { formatAmount, formatInteger, formatMillimeters } from '../format.js';

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

/**
 * Jemná délka v mm s nejvýš jedním desetinným místem (prořez, ořez; ADR-0011) jako
 * řetězec `Decimal` pro API: „2,5“ → `2.5`, „0,25 cm“ → `2.5`.
 */
export function parseFineLength(text: string): Parsed<string> {
	const clean = text.replace(SPACES, '').replace(',', '.').toLowerCase();
	if (clean === '') return { ok: true, value: null };
	const match = /^(\d+(?:\.\d+)?)([a-z]*)$/.exec(clean);
	if (!match) return { ok: false, message: 'Zadejte délku číslem, např. 3 nebo 2,5.' };
	const [, number, unit] = match;
	const factor = unit === '' ? 1 : UNIT_MM[unit];
	if (factor === undefined) return { ok: false, message: 'Zadejte délku v mm nebo cm.' };
	const tenths = Number(number) * factor * 10;
	const rounded = Math.round(tenths);
	if (Math.abs(tenths - rounded) > 1e-6) {
		return { ok: false, message: 'Délka smí mít nejvýš 1 desetinné místo (mm).' };
	}
	const whole = Math.trunc(rounded / 10);
	const fraction = rounded % 10;
	return { ok: true, value: fraction === 0 ? String(whole) : `${whole}.${fraction}` };
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

/**
 * Hodnota pro zobrazení v buňce ve formátu `cs-CZ` (`1 800`, `1 234,50`), bez jednotky;
 * tu ukazuje pole. Parsování výše oddělovač tisíců i čárku přijímá zpět.
 */
export function integerText(value: number | null): string {
	return value === null ? '' : formatInteger(value);
}

/** Jemná délka pro buňku: `2,5`, `3`, `1 000`. */
export function fineText(value: string | null): string {
	return value === null ? '' : formatMillimeters(value);
}

export function moneyText(value: string | null): string {
	return value === null ? '' : formatAmount(value);
}
