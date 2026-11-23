<script lang="ts">
	import Ruler from '@lucide/svelte/icons/ruler';
	import { mergeProps } from 'bits-ui';
	import Tooltip from './ui/Tooltip.svelte';
	import type { Tool } from '#lib/fixtures/empty-project.js';

	/** Karta nástroje jako tlačítko: název a jedna věta (komponenty.md). */
	let {
		tool,
		disabledReason,
		onselect
	}: { tool: Tool; disabledReason?: string; onselect?: () => void } = $props();

	const reasonId = $props.id();
	let isDisabled = $derived(disabledReason !== undefined);
</script>

{#snippet card(extra: Record<string, unknown>)}
	<button
		{...mergeProps(extra, {})}
		type="button"
		aria-disabled={isDisabled || undefined}
		aria-describedby={isDisabled ? reasonId : undefined}
		onclick={() => {
			if (!isDisabled) onselect?.();
		}}
		class="flex w-full items-start gap-3 rounded-lg border bg-surface p-4 text-left transition-colors duration-(--duration-fast) ease-standard {isDisabled
			? 'cursor-not-allowed border-border'
			: 'border-border-strong hover:bg-surface-sunken'}"
	>
		<span
			class="flex size-8 shrink-0 items-center justify-center rounded-md bg-surface-sunken text-ink"
			aria-hidden="true"
		>
			<Ruler size={16} strokeWidth={1.5} />
		</span>
		<span class="flex flex-col gap-1">
			<span class="text-body font-semibold text-ink">{tool.label}</span>
			<span class="text-small text-ink-muted">{tool.description}</span>
		</span>
	</button>
	{#if isDisabled}
		<span id={reasonId} class="sr-only">{disabledReason}</span>
	{/if}
{/snippet}

{#if disabledReason}
	<Tooltip content={disabledReason}>
		{#snippet trigger({ props })}
			{@render card(props as Record<string, unknown>)}
		{/snippet}
	</Tooltip>
{:else}
	{@render card({})}
{/if}
