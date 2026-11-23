import { describe, expect, it } from 'vitest';
import { formatLength, formatMoney, formatPercent } from './format';

// V očekávaných hodnotách je nezlomitelná mezera zapsaná jako „~“ kvůli čitelnosti.
const nbsp = (text: string) => text.replaceAll('~', ' ');

describe('formatLength', () => {
	it.each([
		[0, '0~mm'],
		[750, '750~mm'],
		[1250, '1~250~mm'],
		[12500, '12~500~mm']
	])('%d mm → %s', (mm, expected) => {
		expect(formatLength(mm)).toBe(nbsp(expected));
	});
});

describe('formatMoney', () => {
	it.each([
		['0', '0,00~Kč'],
		['1234.5', '1~234,50~Kč'],
		['1234567.891', '1~234~567,89~Kč'],
		['0.005', '0,01~Kč']
	])('%s → %s', (amount, expected) => {
		expect(formatMoney(amount)).toBe(nbsp(expected));
	});

	it('chybějící cenu nepíše jako nulu', () => {
		expect(formatMoney(null)).toBe('chybí cena');
	});

	it('neztrácí přesnost u velkých částek', () => {
		expect(formatMoney('12345678901234.57')).toBe(nbsp('12~345~678~901~234,57~Kč'));
	});
});

describe('formatPercent', () => {
	it.each([
		[0.917, '91,7~%'],
		[1, '100,0~%'],
		[0.0004, '0,0~%']
	])('%d → %s', (ratio, expected) => {
		expect(formatPercent(ratio)).toBe(nbsp(expected));
	});
});
