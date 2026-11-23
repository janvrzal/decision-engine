<script lang="ts">
	import { Tooltip } from 'bits-ui';
	import type { Snippet } from 'svelte';

	// Tooltip se otevře najetím i fokusem z klávesnice; nenese jedinou kopii důležité informace.
	let {
		content,
		trigger
	}: {
		content: string;
		trigger: Snippet<[{ props: Record<string, unknown> }]>;
	} = $props();
</script>

<!-- Provider je v komponentě, aby tooltip fungoval v každém kontextu (i v testech). -->
<Tooltip.Provider delayDuration={300}>
	<Tooltip.Root>
		<Tooltip.Trigger>
			{#snippet child({ props })}
				{@render trigger({ props })}
			{/snippet}
		</Tooltip.Trigger>
		<Tooltip.Portal>
			<Tooltip.Content
				sideOffset={6}
				class="z-50 max-w-64 rounded-md bg-ink px-2 py-1 text-small text-surface shadow-overlay"
			>
				{content}
			</Tooltip.Content>
		</Tooltip.Portal>
	</Tooltip.Root>
</Tooltip.Provider>
