import type { Objective, ProposalEdited, ProposalView } from './api/types.js';
import {
	integerText,
	moneyText,
	parseInteger,
	parseLength,
	parseMoney
} from './behaviors/number-input.js';
import { formatLength } from './format.js';

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
	if (!previous) return withStarterRow(next);
	const keep = <Row extends PartDraftRow | StockDraftRow>(rows: Row[], known: { id: string }[]) =>
		rows.filter((row) => isEmptyRow(row) && !known.some((k) => k.id === row.id));
	next.parts.push(...keep(previous.parts, next.parts));
	next.stock.push(...keep(previous.stock, next.stock));
	return withStarterRow(next);
}

/**
 * Ponechá v novém konceptu `next` (z odpovědi backendu) všechno, co uživatel změnil od
 * posledního odeslání (`sent`): odpověď na starší úpravu nesmí přepsat rozepsanou buňku.
 */
export function keepEditsSince(
	next: ProposalDraft,
	current: ProposalDraft,
	sent: ProposalDraft
): ProposalDraft {
	const scalar = <K extends keyof ProposalDraft>(key: K) =>
		current[key] !== sent[key] ? current[key] : next[key];
	const rows = <Row extends PartDraftRow | StockDraftRow>(
		nextRows: Row[],
		currentRows: Row[],
		sentRows: Row[]
	): Row[] => {
		const byId = (list: Row[], id: string) => list.find((row) => row.id === id);
		const merged = nextRows.flatMap((row) => {
			const cur = byId(currentRows, row.id);
			const old = byId(sentRows, row.id);
			if (!cur) return old ? [] : [row]; // uživatel řádek mezitím odebral
			if (!old) return [cur];
			const result = { ...row };
			for (const key of Object.keys(row) as (keyof Row)[]) {
				if (cur[key] !== old[key]) result[key] = cur[key];
			}
			return [result];
		});
		const added = currentRows.filter((row) => !byId(nextRows, row.id) && !byId(sentRows, row.id));
		return [...merged, ...added];
	};
	return {
		name: scalar('name'),
		material: scalar('material'),
		parts: rows(next.parts, current.parts, sent.parts),
		stock: rows(next.stock, current.stock, sent.stock),
		kerf_mm: scalar('kerf_mm'),
		trim_mm: scalar('trim_mm'),
		min_remnant_mm: scalar('min_remnant_mm'),
		time_limit_s: scalar('time_limit_s'),
		objective: scalar('objective')
	};
}

/** Tabulka dílů nikdy není bez řádku: prázdná dostane jeden prázdný řádek k vyplnění (UC-13). */
function withStarterRow(draft: ProposalDraft): ProposalDraft {
	if (draft.parts.length === 0) {
		draft.parts.push({ id: nextRowId('p', draft.parts), name: '', length_mm: '', quantity: '' });
	}
	return draft;
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
	| { ok: true; event: ProposalEdited; conversions: string[] }
	| { ok: false; errors: Record<CellKey, string> };

/** Koncept → událost `ProposalEdited`, nebo chyby buněk, jejichž text není číslo. */
export function draftToEvent(draft: ProposalDraft): DraftResult {
	const errors: Record<CellKey, string> = {};
	const int = (key: CellKey, text: string): number | null => {
		const parsed = parseInteger(text);
		if (parsed.ok) return parsed.value;
		errors[key] = parsed.message;
		return null;
	};
	const conversions: string[] = [];
	const length = (key: CellKey, text: string): number | null => {
		const parsed = parseLength(text);
		if (!parsed.ok) {
			errors[key] = parsed.message;
			return null;
		}
		if (parsed.converted && parsed.value !== null) {
			conversions.push(`${text.trim()} = ${formatLength(parsed.value)}`);
		}
		return parsed.value;
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
							length_mm: length(`parts.${i}.length_mm`, row.length_mm),
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
							length_mm: length(`stock.${i}.length_mm`, row.length_mm),
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
	return Object.keys(errors).length > 0 ? { ok: false, errors } : { ok: true, event, conversions };
}

/**
 * Koncept s platnými čísly ve formátu `cs-CZ` (`12500` → `12 500`, `1,5 m` → `1 500`,
 * `1234,5` → `1 234,50`). Volá se při potvrzení buňky, ne během psaní; text, který číslem
 * není, zůstane, jak ho uživatel napsal, aby šel opravit.
 */
export function normalizeDraft(draft: ProposalDraft): ProposalDraft {
	const int = (text: string) => {
		const parsed = parseInteger(text);
		return parsed.ok ? integerText(parsed.value) : text;
	};
	const length = (text: string) => {
		const parsed = parseLength(text);
		return parsed.ok ? integerText(parsed.value) : text;
	};
	const money = (text: string) => {
		const parsed = parseMoney(text);
		return parsed.ok ? moneyText(parsed.value) : text;
	};
	return {
		...draft,
		parts: draft.parts.map((row) => ({
			...row,
			length_mm: length(row.length_mm),
			quantity: int(row.quantity)
		})),
		stock: draft.stock.map((row) => ({
			...row,
			length_mm: length(row.length_mm),
			price: money(row.price)
		})),
		kerf_mm: int(draft.kerf_mm),
		trim_mm: int(draft.trim_mm),
		min_remnant_mm: int(draft.min_remnant_mm),
		time_limit_s: int(draft.time_limit_s)
	};
}
