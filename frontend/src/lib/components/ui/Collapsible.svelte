<script lang="ts">
	import { Collapsible } from 'bits-ui';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import type { Snippet } from 'svelte';

	/** Sbalitelná sekce (Bits Collapsible): šipka se otáčí, popisek se nemění. */
	let {
		label,
		open = $bindable(false),
		children
	}: { label: string; open?: boolean; children: Snippet } = $props();
</script>

<Collapsible.Root bind:open>
	<Collapsible.Trigger
		class="inline-flex h-8 items-center gap-1 rounded-md px-2 text-body font-semibold text-ink hover:bg-surface-sunken"
	>
		<ChevronDown
			size={16}
			strokeWidth={1.5}
			aria-hidden="true"
			class="transition-transform duration-(--duration-fast) ease-standard {open
				? 'rotate-180'
				: ''}"
		/>
		{label}
	</Collapsible.Trigger>
	<Collapsible.Content class="pt-2">
		{@render children()}
	</Collapsible.Content>
</Collapsible.Root>
