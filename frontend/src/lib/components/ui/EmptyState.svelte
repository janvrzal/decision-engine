<script lang="ts">
	import type { Snippet } from 'svelte';

	/**
	 * Prázdný stav: co sem patří (nadpis a jedna věta) a jedna akce.
	 * Celostránková varianta má navíc ikonu (komponenty.md).
	 */
	let {
		title,
		variant = 'panel',
		icon,
		children,
		action
	}: {
		title: string;
		variant?: 'panel' | 'page';
		icon?: Snippet;
		children: Snippet;
		action?: Snippet;
	} = $props();
</script>

<div
	class="flex flex-col items-center text-center {variant === 'page'
		? 'gap-4 px-8 py-12'
		: 'gap-3 px-4 py-8'}"
>
	{#if icon && variant === 'page'}
		<div class="text-ink-muted" aria-hidden="true">{@render icon()}</div>
	{/if}
	<h2 class="text-balance {variant === 'page' ? 'text-title' : 'text-heading'} text-ink">
		{title}
	</h2>
	<div class="max-w-md text-body text-ink-muted">{@render children()}</div>
	{#if action}
		<div class="mt-2">{@render action()}</div>
	{/if}
</div>
