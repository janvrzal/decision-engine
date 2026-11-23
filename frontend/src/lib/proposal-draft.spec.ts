import { describe, expect, it } from 'vitest';
import type { ProposalView } from './api/types';
import { formatLength } from './format';
import {
	draftFromProposal,
	draftToEvent,
	keepEditsSince,
	mergeDraft,
	nextRowId
} from './proposal-draft';

const cell = <T>(value: T, unconfirmed = false) => ({ value, unconfirmed, error: null });

const PROPOSAL: ProposalView = {
	is_change: false,
	origin: 'ai',
	name: cell('Regál'),
	material: cell(null),
	parts: [{ id: 'p1', name: cell('noha'), length_mm: cell(1800), quantity: cell(4) }],
	stock: [{ id: 's1', length_mm: cell(6000, true), price: cell('320.50') }],
	parameters: {
		kerf_mm: cell(3),
		trim_mm: cell(0, true),
		min_remnant_mm: cell(300, true),
		time_limit_s: cell(10)
	},
	objective: 'cheapest',
	objective_unconfirmed: true,
	objective_options: [],
	errors: [],
	can_confirm: true,
	confirm_disabled_reason: null
};

describe('koncept kontrolní tabulky', () => {
	it('návrh → koncept → událost beze změny hodnot', () => {
		const draft = draftFromProposal(PROPOSAL);
		expect(draft.stock[0].price).toBe('320,50');

		const result = draftToEvent(draft);

		expect(result).toEqual({
			ok: true,
			conversions: [],
			event: {
				type: 'ProposalEdited',
				name: 'Regál',
				material: null,
				parts: [{ id: 'p1', name: 'noha', length_mm: 1800, quantity: 4 }],
				stock: [{ id: 's1', length_mm: 6000, price: '320.50' }],
				parameters: {
					kerf_mm: 3,
					trim_mm: 0,
					min_remnant_mm: 300,
					time_limit_s: 10,
					objective: 'cheapest'
				}
			}
		});
	});

	it('prázdná buňka je chybějící hodnota, ne nula', () => {
		const draft = draftFromProposal(PROPOSAL);
		draft.parts[0].length_mm = '';

		const result = draftToEvent(draft);

		expect(result.ok && result.event.parts[0].length_mm).toBeNull();
	});

	it('text, který není číslo, se neodešle a hlásí chybu u buňky', () => {
		const draft = draftFromProposal(PROPOSAL);
		draft.parts[0].quantity = 'čtyři';
		draft.stock[0].price = 'hodně';

		const result = draftToEvent(draft);

		expect(result).toEqual({
			ok: false,
			errors: {
				'parts.0.quantity': 'Zadejte celé číslo.',
				'stock.0.price': 'Zadejte částku, nejvýš 2 desetinná místa.'
			}
		});
	});

	it('nové id řádku nekoliduje', () => {
		expect(nextRowId('p', [{ id: 'p1' }, { id: 'p3' }])).toBe('p4');
		expect(nextRowId('s', [])).toBe('s1');
	});

	it('prázdný nový řádek se neodešle a po odpovědi backendu zůstane', () => {
		const draft = draftFromProposal(PROPOSAL);
		draft.parts.push({ id: 'p2', name: '', length_mm: '', quantity: '' });

		const result = draftToEvent(draft);
		expect(result.ok && result.event.parts.map((p) => p.id)).toEqual(['p1']);

		const merged = mergeDraft(PROPOSAL, draft);
		expect(merged.parts.map((p) => p.id)).toEqual(['p1', 'p2']);
	});
});

describe('ruční zadání', () => {
	it('prázdná tabulka dílů dostane jeden prázdný řádek', () => {
		const draft = mergeDraft({ ...PROPOSAL, origin: 'manual', parts: [] }, null);
		expect(draft.parts).toEqual([{ id: 'p1', name: '', length_mm: '', quantity: '' }]);
	});

	it('délka v metrech se převede na mm a převod se oznámí', () => {
		const draft = draftFromProposal(PROPOSAL);
		draft.parts[0].length_mm = '1,5 m';
		const result = draftToEvent(draft);
		expect(result.ok && result.event.parts[0].length_mm).toBe(1500);
		expect(result.ok && result.conversions).toEqual([`1,5 m = ${formatLength(1500)}`]);
	});
});

describe('keepEditsSince', () => {
	it('odpověď na starší úpravu nepřepíše buňku rozepsanou mezitím', () => {
		const sent = draftFromProposal(PROPOSAL);
		const current = structuredClone(sent);
		current.parts[0].length_mm = '1,8 m';
		current.kerf_mm = '4';
		const next = structuredClone(sent);
		next.name = 'Regál (ze serveru)';

		const merged = keepEditsSince(next, current, sent);

		expect(merged.parts[0].length_mm).toBe('1,8 m');
		expect(merged.kerf_mm).toBe('4');
		expect(merged.name).toBe('Regál (ze serveru)');
	});

	it('nově přidaný řádek zůstane, mezitím odebraný se nevrátí', () => {
		const sent = draftFromProposal(PROPOSAL);
		const current = structuredClone(sent);
		current.parts = [{ id: 'p2', name: 'příčka', length_mm: '850', quantity: '2' }];

		const merged = keepEditsSince(structuredClone(sent), current, sent);

		expect(merged.parts.map((row) => row.id)).toEqual(['p2']);
	});
});
