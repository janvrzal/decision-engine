/** Ukázky zadání pro čipy a pole zadání (obsah UI, ne data zakázky). */

export interface ExamplePrompt {
	label: string;
	text: string;
}

export const EXAMPLE_PROMPTS: ExamplePrompt[] = [
	{
		label: 'Regál s cenou',
		text: 'Regál: 4 nohy po 1 800 mm a 8 polic po 1 200 mm. Tyče 6 m stojí 320 Kč, prořez 3 mm.'
	},
	{
		label: 'Sloupky a příčky',
		text: 'Potřebuji nařezat 12 sloupků po 1 850 mm a 8 příček po 920 mm z tyčí 6 m, prořez 3 mm.'
	},
	{
		label: 'Jekl 40×40×2',
		text: 'Mám jekl 40×40×2 v délce 6 000 mm. Potřebuji 4 kusy po 2 200 mm a 6 kusů po 750 mm.'
	}
];

export const NOT_AVAILABLE_REASON = 'Tato akce zatím není k dispozici.';

export interface Tool {
	id: string;
	label: string;
	description: string;
}

/** Jedna věta k nástroji pro kartu (názvy nástrojů dodává backend z registru). */
export const TOOL_DESCRIPTIONS: Record<string, string> = {
	cutting_1d: 'Nářezový plán z tyčí, profilů a trubek s co nejmenším odpadem.'
};
