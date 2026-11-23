<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	/** Čip: ukázky zadání, rychlé úpravy, volby doptání. Nikdy nenahrazuje hlavní akci. */
	let {
		selected = false,
		children,
		...rest
	}: Omit<HTMLButtonAttributes, 'type'> & { selected?: boolean; children: Snippet } = $props();
</script>

<button
	{...rest}
	type="button"
	aria-pressed={selected || undefined}
	class="inline-flex h-6 items-center gap-1 rounded-sm border px-2 text-small whitespace-nowrap transition-colors duration-(--duration-fast) ease-standard {selected
		? 'border-ink bg-surface-sunken text-ink'
		: 'border-border-strong bg-surface text-ink hover:bg-surface-sunken'}"
>
	{@render children()}
</button>
