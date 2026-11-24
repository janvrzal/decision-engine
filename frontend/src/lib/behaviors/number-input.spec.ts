import { describe, expect, it } from 'vitest';
import { integerText, moneyText, parseInteger, parseLength, parseMoney } from './number-input';

describe('parseInteger', () => {
	it.each([
		['1850', 1850],
		['1 850', 1850],
		['1 850', 1850],
		['', null],
		['  ', null]
	])('%s → %s', (text, value) => {
		expect(parseInteger(text)).toEqual({ ok: true, value });
	});

	it.each(['1,5', '12a', '1.5'])('%s není celé číslo', (text) => {
		expect(parseInteger(text)).toEqual({ ok: false, message: 'Zadejte celé číslo.' });
	});
});

describe('parseMoney', () => {
	it.each([
		['320', '320'],
		['320,50', '320.50'],
		['1 234,5', '1234.5'],
		['', null]
	])('%s → %s', (text, value) => {
		expect(parseMoney(text)).toEqual({ ok: true, value });
	});

	it.each(['1,234', 'zdarma', '-5'])('%s není platná částka', (text) => {
		expect(parseMoney(text).ok).toBe(false);
	});
});

describe('zobrazení v buňce', () => {
	it('prázdná hodnota je prázdné pole, ne nula', () => {
		expect(integerText(null)).toBe('');
		expect(moneyText(null)).toBe('');
		expect(moneyText('320.50')).toBe('320,50');
	});

	it('čísla mají oddělovač tisíců cs-CZ a vrátí se parsováním beze změny', () => {
		expect(integerText(1800)).toBe('1\u00a0800');
		expect(integerText(12500)).toBe('12\u00a0500');
		expect(integerText(0)).toBe('0');
		expect(integerText(-1800)).toBe('-1\u00a0800');
		expect(moneyText('1234.5')).toBe('1\u00a0234,50');
		expect(moneyText('320')).toBe('320,00');
		expect(moneyText('123456789012.34')).toBe('123\u00a0456\u00a0789\u00a0012,34');
		expect(parseInteger(integerText(12500))).toEqual({ ok: true, value: 12500 });
		expect(parseMoney(moneyText('1234.5'))).toEqual({ ok: true, value: '1234.50' });
	});
});

describe('parseLength', () => {
	it.each([
		['1500', 1500, false],
		['1 500', 1500, false],
		['1500 mm', 1500, false],
		['150 cm', 1500, true],
		['1,5 m', 1500, true],
		['1.5M', 1500, true],
		['', null, false]
	])('„%s“ je %s mm', (text, value, converted) => {
		expect(parseLength(text)).toEqual({ ok: true, value, converted });
	});

	it.each([
		['metr a půl', 'Zadejte délku číslem, např. 1200 nebo 1,2 m.'],
		['1,5 palce', 'Zadejte délku v mm, cm nebo m.'],
		['15 dm', 'Zadejte délku v mm, cm nebo m.'],
		['1,2345 m', 'Délka musí vyjít na celé milimetry.'],
		['12,5', 'Délka musí vyjít na celé milimetry.']
	])('„%s“ se odmítne', (text, message) => {
		expect(parseLength(text)).toEqual({ ok: false, message });
	});
});
