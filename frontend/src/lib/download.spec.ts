import { describe, expect, it } from 'vitest';
import { fileNameFromDisposition } from './download';

describe('fileNameFromDisposition', () => {
	it.each([
		["attachment; filename*=UTF-8''regal-do-dilny.decision.json", 'regal-do-dilny.decision.json'],
		["attachment; filename*=UTF-8''plot%20zahrada.decision.json", 'plot zahrada.decision.json'],
		['attachment; filename="ram.decision.json"', 'ram.decision.json'],
		[null, 'zakazka.decision.json'],
		["attachment; filename*=UTF-8''%E0%A4%A", 'zakazka.decision.json']
	])('%s → %s', (header, name) => {
		expect(fileNameFromDisposition(header)).toBe(name);
	});
});
