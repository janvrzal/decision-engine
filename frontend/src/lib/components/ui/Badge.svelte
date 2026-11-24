<script lang="ts">
	import type { Component, Snippet } from 'svelte';

	/** Krátký štítek (komponenty.md `Badge`): vždy text, volitelně ikona; nikdy jen barva. */
	type Variant = 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'proposal';

	let {
		variant = 'neutral',
		icon: Icon,
		children
	}: {
		variant?: Variant;
		icon?: Component<{ size?: number; strokeWidth?: number }>;
		children: Snippet;
	} = $props();

	const classes: Record<Variant, string> = {
		neutral: 'bg-surface-sunken text-ink-muted',
		info: 'bg-info-bg text-info',
		success: 'bg-success-bg text-success',
		warning: 'bg-warning-bg text-warning',
		danger: 'bg-danger-bg text-danger',
		proposal: 'bg-proposal-bg text-proposal'
	};
</script>

<span
	class="inline-flex h-5.5 shrink-0 items-center gap-1 rounded-sm px-2 text-label font-medium uppercase {classes[
		variant
	]}"
>
	{#if Icon}
		<span aria-hidden="true" class="inline-flex"><Icon size={14} strokeWidth={2} /></span>
	{/if}
	{@render children()}
</span>
