import { describe, expect, it } from 'vitest';
import { integerText, moneyText, parseInteger, parseMoney } from './number-input';

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
});
