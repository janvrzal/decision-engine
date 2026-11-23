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

/** Délka v celých milimetrech: `1 250 mm`. */
export function formatLength(mm: number): string {
	return `${normalizeSpaces(integer.format(mm))}${NBSP}mm`;
}

/**
 * Částka v Kč ze stringu `Decimal` z API: `1 234,50 Kč`.
 * Chybějící cena je „chybí cena“, nikdy `0 Kč`.
 */
export function formatMoney(amount: string | null): string {
	if (amount === null) return 'chybí cena';
	return `${normalizeSpaces(money.format(amount as `${number}`))}${NBSP}Kč`;
}

/** Podíl 0–1 jako procento s jedním desetinným místem: `91,7 %`. */
export function formatPercent(ratio: number): string {
	return normalizeSpaces(percent.format(ratio));
}
