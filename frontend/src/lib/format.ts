/**
 * Formátování čísel a jednotek podle docs/design-system/obsah.md.
 *
 * Hodnoty počítá backend; frontend je jen zobrazuje v `cs-CZ`. Mezi číslem a jednotkou
 * i jako oddělovač tisíců je nezlomitelná mezera.
 */

const NBSP = ' ';

const integer = new Intl.NumberFormat('cs-CZ', { maximumFractionDigits: 0 });
const money = new Intl.NumberFormat('cs-CZ', {
	minimumFractionDigits: 2,
	maximumFractionDigits: 2
});
const percent = new Intl.NumberFormat('cs-CZ', {
	style: 'percent',
	minimumFractionDigits: 1,
	maximumFractionDigits: 1
});

// Intl používá pro tisíce úzkou nebo běžnou nezlomitelnou mezeru; sjednotíme na NBSP.
const normalizeSpaces = (text: string): string => text.replace(/[\u202f\u00a0 ]/g, NBSP);

/** Celé číslo bez jednotky: `1 250`. */
export function formatInteger(value: number): string {
	return normalizeSpaces(integer.format(value));
}

/** Částka bez měny ze stringu `Decimal` (bez ztráty přesnosti): `1 234,50`. */
export function formatAmount(amount: string): string {
	return normalizeSpaces(money.format(amount as `${number}`));
}

const fine = new Intl.NumberFormat('cs-CZ', { maximumFractionDigits: 1 });

/**
 * Délka v milimetrech: `1 250 mm`, `2 005,5 mm`. Polohy a zbytky přicházejí z API
 * jako string `Decimal` (prořez smí mít desetiny mm, ADR-0011).
 */
export function formatLength(mm: number | string): string {
	return `${formatMillimeters(mm)}${NBSP}mm`;
}

/** Číslo milimetrů bez jednotky, nejvýš s jedním desetinným místem: `2 005,5`. */
export function formatMillimeters(mm: number | string): string {
	return normalizeSpaces(fine.format(Number(mm)));
}

/**
 * Částka v Kč ze stringu `Decimal` z API: `1 234,50 Kč`.
 * Chybějící cena je „chybí cena“, nikdy `0 Kč`.
 */
export function formatMoney(amount: string | null): string {
	if (amount === null) return 'chybí cena';
	return `${formatAmount(amount)}${NBSP}Kč`;
}

/** Podíl 0–1 jako procento s jedním desetinným místem: `91,7 %`. */
export function formatPercent(ratio: number): string {
	return normalizeSpaces(percent.format(ratio));
}

/** Česky skloňované „tyč“: 1 tyč, 2–4 tyče, 5 a víc tyčí. */
export function barsWord(count: number): string {
	if (count === 1) return 'tyč';
	return count >= 2 && count <= 4 ? 'tyče' : 'tyčí';
}
