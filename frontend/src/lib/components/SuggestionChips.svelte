<script lang="ts">
	import Chip from './ui/Chip.svelte';
	import type { ExamplePrompt } from '#lib/examples.js';

	/** Řada čipů s ukázkami zpráv nad polem pro zprávu. */
	let {
		label,
		suggestions,
		onpick
	}: {
		label: string;
		suggestions: ExamplePrompt[];
		onpick: (text: string) => void;
	} = $props();
</script>

<div class="flex flex-col gap-2">
	<p class="text-small text-ink-muted">{label}</p>
	<ul class="flex flex-wrap gap-2">
		{#each suggestions as suggestion (suggestion.label)}
			<li>
				<Chip onclick={() => onpick(suggestion.text)}>{suggestion.label}</Chip>
			</li>
		{/each}
	</ul>
</div>
