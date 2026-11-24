import { describe, expect, it } from 'vitest';
import { STEP_HEADING, stepAnnouncement } from './step-focus';

describe('step-focus', () => {
	it('každý krok má nadpis, na který jde fokus', () => {
		expect(Object.keys(STEP_HEADING)).toEqual(['input', 'review', 'result']);
	});

	it('oznámí spočítaný plán souhrnem od backendu', () => {
		expect(stepAnnouncement('result', '4 tyče, výtěžnost 70,0 %')).toBe(
			'Plán spočítán: 4 tyče, výtěžnost 70,0 %.'
		);
		expect(stepAnnouncement('review', null)).toContain('Kontrola údajů');
	});
});
