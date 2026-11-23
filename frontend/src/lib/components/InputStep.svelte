<script lang="ts">
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import Shuffle from '@lucide/svelte/icons/shuffle';
	import ToolCard from './ToolCard.svelte';
	import Button from './ui/Button.svelte';
	import TextArea from './ui/TextArea.svelte';
	import { NOT_CONNECTED_REASON, type ProjectView } from '#lib/fixtures/empty-project.js';

	/** Krok Zadání v prázdném stavu: velké pole s ukázkou zadání a karty nástrojů. */
	let { project }: { project: ProjectView } = $props();

	let draft = $state('');
	let exampleIndex = $state(0);
	let example = $derived(project.examplePrompts[exampleIndex % project.examplePrompts.length]);

	function nextExample() {
		exampleIndex += 1;
	}

	let continueReason = $derived(
		draft.trim() === '' ? 'Nejdřív popište, co potřebujete nařezat.' : NOT_CONNECTED_REASON
	);
</script>

<section class="flex flex-col gap-8" aria-labelledby="input-step-title">
	<div class="flex flex-col gap-4 rounded-lg border border-border bg-surface p-6 shadow-raised">
		<div class="flex flex-col gap-1">
			<h2 id="input-step-title" class="text-heading text-balance text-ink">
				Co potřebujete nařezat?
			</h2>
			<p class="text-body text-ink-muted">
				Napište zadání vlastními slovy, jako byste ho říkali kolegovi v dílně.
			</p>
		</div>
		<TextArea
			bind:value={draft}
			label="Zadání zakázky"
			hideLabel
			rows={6}
			placeholder={example?.text}
			hint="Uveďte díly s délkou a počtem, skladovou délku tyčí a případně prořez a ceny."
		/>
		<div class="flex flex-wrap items-center justify-between gap-2">
			<Button variant="ghost" onclick={nextExample}>
				<Shuffle size={16} strokeWidth={1.5} aria-hidden="true" />
				Další ukázka
			</Button>
			<Button variant="primary" disabledReason={continueReason}>
				Pokračovat
				<ArrowRight size={16} strokeWidth={1.5} aria-hidden="true" />
			</Button>
		</div>
	</div>

	<div class="flex flex-col gap-3">
		<div class="flex flex-wrap items-baseline justify-between gap-2">
			<h2 class="text-heading text-ink">Nebo začněte nástrojem</h2>
			<Button variant="ghost" disabledReason={NOT_CONNECTED_REASON}>Zadat ručně</Button>
		</div>
		<ul class="grid gap-4 md:grid-cols-2">
			{#each project.tools as tool (tool.id)}
				<li><ToolCard {tool} disabledReason={NOT_CONNECTED_REASON} /></li>
			{/each}
		</ul>
	</div>
</section>
