<script lang="ts">
	import ChatComposer from './ChatComposer.svelte';
	import SuggestionChips from './SuggestionChips.svelte';
	import type { ExamplePrompt } from '#lib/fixtures/empty-project.js';
	import type { Snippet } from 'svelte';

	/**
	 * Panel Dialog v prázdném stavu: uvítání podle kroku, ukázky zpráv a pole pro zprávu.
	 * Zprávy, průběh a chyby přibudou s view modelem v M1.
	 */
	let {
		suggestions,
		sendDisabledReason,
		header
	}: {
		suggestions: ExamplePrompt[];
		sendDisabledReason?: string;
		header?: Snippet;
	} = $props();

	let draft = $state('');
	let composer = $state<HTMLTextAreaElement | null>(null);

	function pick(text: string) {
		draft = text;
		composer?.focus();
	}
</script>

<section class="flex min-h-0 flex-1 flex-col" aria-label="Dialog">
	{#if header}
		{@render header()}
	{/if}
	<div class="flex min-h-0 flex-1 flex-col justify-end gap-4 overflow-y-auto p-4" role="log">
		<div class="flex flex-col gap-2">
			<p class="text-body text-ink">
				Popište, co potřebujete nařezat: díly, jejich délky a počty a z jakých tyčí. Údaje převedu
				do tabulky, kterou před výpočtem zkontrolujete.
			</p>
			<p class="text-small text-ink-muted">Čísla v plánu i ceně vždy spočítá program, ne AI.</p>
		</div>
		<SuggestionChips label="Vyzkoušejte ukázku:" {suggestions} onpick={pick} />
	</div>
	<div class="border-t border-border p-4">
		<ChatComposer bind:value={draft} bind:ref={composer} {sendDisabledReason} />
	</div>
</section>
