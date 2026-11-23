import type { Objective, ProposalEdited, ProposalView } from './api/types.js';
import { integerText, moneyText, parseInteger, parseMoney } from './behaviors/number-input.js';

/**
 * Lokální koncept kontrolní tabulky: texty v buňkách během psaní (skill ui-frontend:
 * „lokální stav formulářů před odesláním“). Platnost dat posuzuje backend; tady se jen
 * převádí text na čísla a hlásí, když text číslem není.
 */

export interface PartDraftRow {
	id: string;
	name: string;
	length_mm: string;
	quantity: string;
}

export interface StockDraftRow {
	id: string;
	length_mm: string;
	price: string;
}

export interface ProposalDraft {
	name: string;
	material: string;
	parts: PartDraftRow[];
	stock: StockDraftRow[];
	kerf_mm: string;
	trim_mm: string;
	min_remnant_mm: string;
	time_limit_s: string;
	objective: Objective | null;
}

export type ParameterKey = 'kerf_mm' | 'trim_mm' | 'min_remnant_mm' | 'time_limit_s';

export function draftFromProposal(proposal: ProposalView): ProposalDraft {
	return {
		name: proposal.name.value ?? '',
		material: proposal.material.value ?? '',
		parts: proposal.parts.map((row) => ({
			id: row.id,
			name: row.name.value ?? '',
			length_mm: integerText(row.length_mm.value),
			quantity: integerText(row.quantity.value)
		})),
		stock: proposal.stock.map((row) => ({
			id: row.id,
			length_mm: integerText(row.length_mm.value),
			price: moneyText(row.price.value)
		})),
		kerf_mm: integerText(proposal.parameters.kerf_mm.value),
		trim_mm: integerText(proposal.parameters.trim_mm.value),
		min_remnant_mm: integerText(proposal.parameters.min_remnant_mm.value),
		time_limit_s: integerText(proposal.parameters.time_limit_s.value),
		objective: proposal.objective
	};
}

/** Řádek, do kterého uživatel zatím nic nenapsal (neposílá se backendu). */
export function isEmptyRow(row: PartDraftRow | StockDraftRow): boolean {
	return Object.entries(row).every(([key, value]) => key === 'id' || String(value).trim() === '');
}

/**
 * Nový koncept z návrhu od backendu; prázdné řádky, které uživatel právě přidal a ještě
 * nevyplnil, zůstanou na konci (backend o nich neví).
 */
export function mergeDraft(proposal: ProposalView, previous: ProposalDraft | null): ProposalDraft {
	const next = draftFromProposal(proposal);
	if (!previous) return next;
	const keep = <Row extends PartDraftRow | StockDraftRow>(rows: Row[], known: { id: string }[]) =>
		rows.filter((row) => isEmptyRow(row) && !known.some((k) => k.id === row.id));
	next.parts.push(...keep(previous.parts, next.parts));
	next.stock.push(...keep(previous.stock, next.stock));
	return next;
}

/** Nové `id` řádku, které v konceptu ještě není (`p3`, `s2` …). */
export function nextRowId(prefix: 'p' | 's', existing: { id: string }[]): string {
	const taken = new Set(existing.map((row) => row.id));
	let index = existing.length + 1;
	while (taken.has(`${prefix}${index}`)) index += 1;
	return `${prefix}${index}`;
}

/** Klíč buňky pro lokální chyby: `parts.0.length_mm`, `parameters.kerf_mm`. */
export type CellKey = string;

export type DraftResult =
	{ ok: true; event: ProposalEdited } | { ok: false; errors: Record<CellKey, string> };

/** Koncept → událost `ProposalEdited`, nebo chyby buněk, jejichž text není číslo. */
export function draftToEvent(draft: ProposalDraft): DraftResult {
	const errors: Record<CellKey, string> = {};
	const int = (key: CellKey, text: string): number | null => {
		const parsed = parseInteger(text);
		if (parsed.ok) return parsed.value;
		errors[key] = parsed.message;
		return null;
	};
	const money = (key: CellKey, text: string): string | null => {
		const parsed = parseMoney(text);
		if (parsed.ok) return parsed.value;
		errors[key] = parsed.message;
		return null;
	};
	const text = (value: string): string | null => (value.trim() === '' ? null : value.trim());

	const event: ProposalEdited = {
		type: 'ProposalEdited',
		name: text(draft.name),
		material: text(draft.material),
		parts: draft.parts.flatMap((row, i) =>
			isEmptyRow(row)
				? []
				: [
						{
							id: row.id,
							name: text(row.name),
							length_mm: int(`parts.${i}.length_mm`, row.length_mm),
							quantity: int(`parts.${i}.quantity`, row.quantity)
						}
					]
		),
		stock: draft.stock.flatMap((row, i) =>
			isEmptyRow(row)
				? []
				: [
						{
							id: row.id,
							length_mm: int(`stock.${i}.length_mm`, row.length_mm),
							price: money(`stock.${i}.price`, row.price)
						}
					]
		),
		parameters: {
			kerf_mm: int('parameters.kerf_mm', draft.kerf_mm),
			trim_mm: int('parameters.trim_mm', draft.trim_mm),
			min_remnant_mm: int('parameters.min_remnant_mm', draft.min_remnant_mm),
			time_limit_s: int('parameters.time_limit_s', draft.time_limit_s),
			objective: draft.objective
		}
	};
	return Object.keys(errors).length > 0 ? { ok: false, errors } : { ok: true, event };
}
