<script lang="ts">
	import type { HTMLTextareaAttributes } from 'svelte/elements';

	/** Víceřádkové pole s popiskem nad a nápovědou pod polem (komponenty.md). */
	let {
		label,
		hideLabel = false,
		hint,
		value = $bindable(''),
		ref = $bindable(null),
		class: className = '',
		...rest
	}: Omit<HTMLTextareaAttributes, 'value'> & {
		label: string;
		hideLabel?: boolean;
		hint?: string;
		value?: string;
		ref?: HTMLTextAreaElement | null;
	} = $props();

	const id = $props.id();
</script>

<div class="flex flex-col gap-1">
	<label for={id} class={hideLabel ? 'sr-only' : 'text-small font-medium text-ink'}>{label}</label>
	<textarea
		{...rest}
		{id}
		bind:value
		bind:this={ref}
		aria-describedby={hint ? `${id}-hint` : undefined}
		class="w-full resize-none rounded-sm border border-border-strong bg-surface px-3 py-2 text-body text-ink placeholder:text-ink-subtle {className}"
	></textarea>
	{#if hint}
		<p id="{id}-hint" class="text-small text-ink-muted">{hint}</p>
	{/if}
</div>
