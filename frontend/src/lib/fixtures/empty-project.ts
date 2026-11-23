/**
 * Dočasná data prázdné zakázky ve tvaru podle „Kostry view modelu“ z mapy obrazovek
 * (docs/service-design/04-mapa-obrazovek.md). V M1 (#14, #15) je nahradí view model
 * generovaný z API; do té doby tu nejsou žádná vypočtená čísla.
 */

export type StepId = 'input' | 'review' | 'result';
export type StepState = 'pending' | 'active' | 'done' | 'stale' | 'unavailable';

export interface Step {
	id: StepId;
	label: string;
	state: StepState;
}

export interface ExamplePrompt {
	label: string;
	text: string;
}

export interface Tool {
	id: string;
	label: string;
	description: string;
}

export interface ProjectView {
	name: string;
	steps: Step[];
	examplePrompts: ExamplePrompt[];
	tools: Tool[];
}

/** Důvod u akcí, které ještě nejsou napojené na backend (rozhodnutí v #4). */
export const NOT_CONNECTED_REASON = 'Tato akce zatím není k dispozici.';

export const emptyProject: ProjectView = {
	name: 'Nová zakázka',
	steps: [
		{ id: 'input', label: 'Zadání', state: 'active' },
		{ id: 'review', label: 'Kontrola údajů', state: 'unavailable' },
		{ id: 'result', label: 'Plán a cena', state: 'unavailable' }
	],
	examplePrompts: [
		{
			label: 'Sloupky a příčky',
			text: 'Potřebuji nařezat 12 sloupků po 1 850 mm a 8 příček po 920 mm z tyčí 6 m, prořez 3 mm.'
		},
		{
			label: 'Jekl 40×40×2',
			text: 'Mám jekl 40×40×2 v délce 6 000 mm. Potřebuji 4 kusy po 2 200 mm a 6 kusů po 750 mm.'
		},
		{
			label: 'Regál s cenou',
			text: 'Regál: 4 nohy po 1 800 mm, 8 polic po 1 200 mm a 8 hloubek po 400 mm. Tyče 6 m stojí 320 Kč.'
		}
	],
	tools: [
		{
			id: 'cutting_1d',
			label: 'Řezání tyčí',
			description: 'Nářezový plán z tyčí, profilů a trubek s co nejmenším odpadem.'
		}
	]
};
