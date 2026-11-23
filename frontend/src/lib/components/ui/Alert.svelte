<script lang="ts">
	import CircleExclamation from '@lucide/svelte/icons/circle-exclamation-point';
	import Info from '@lucide/svelte/icons/info';
	import TriangleExclamation from '@lucide/svelte/icons/triangle-exclamation-point';
	import type { Snippet } from 'svelte';

	/** Upozornění: ikona, krátký nadpis, jedna věta, nejvýš dvě akce (komponenty.md). */
	let {
		variant,
		title,
		children,
		actions
	}: {
		variant: 'info' | 'warning' | 'danger';
		title: string;
		children?: Snippet;
		actions?: Snippet;
	} = $props();

	const styles = {
		info: 'border-info bg-info-bg text-info',
		warning: 'border-warning bg-warning-bg text-warning',
		danger: 'border-danger bg-danger-bg text-danger'
	} as const;
	const icons = { info: Info, warning: TriangleExclamation, danger: CircleExclamation } as const;
	let Icon = $derived(icons[variant]);
</script>

<div
	class="flex gap-3 rounded-md border px-3 py-3 {styles[variant]}"
	role={variant === 'danger' ? 'alert' : 'status'}
>
	<Icon size={16} strokeWidth={1.5} class="mt-0.5 shrink-0" aria-hidden="true" />
	<div class="flex min-w-0 flex-1 flex-col gap-1">
		<p class="text-body font-semibold">{title}</p>
		{#if children}
			<div class="text-body text-ink">{@render children()}</div>
		{/if}
		{#if actions}
			<div class="mt-1 flex flex-wrap gap-2">{@render actions()}</div>
		{/if}
	</div>
</div>
