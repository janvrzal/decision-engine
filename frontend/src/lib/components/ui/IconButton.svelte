<script lang="ts">
	import { mergeProps } from 'bits-ui';
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';
	import Tooltip from './Tooltip.svelte';

	/** Tlačítko s ikonou: vždy `aria-label` a tooltip s názvem akce (komponenty.md). */
	let {
		label,
		variant = 'ghost',
		size = 32,
		disabledReason,
		children,
		onclick,
		...rest
	}: Omit<HTMLButtonAttributes, 'disabled' | 'aria-label'> & {
		label: string;
		variant?: 'ghost' | 'secondary';
		size?: 32 | 24;
		disabledReason?: string;
		children: Snippet;
	} = $props();

	let isDisabled = $derived(disabledReason !== undefined);
	let tooltip = $derived(disabledReason ? `${label}: ${disabledReason}` : label);

	const sizes = { 32: 'size-8', 24: 'size-6' } as const;
	const variants = {
		ghost: 'text-ink hover:bg-surface-sunken',
		secondary: 'border border-border-strong bg-surface text-ink hover:bg-surface-sunken'
	} as const;

	function handleClick(event: MouseEvent & { currentTarget: EventTarget & HTMLButtonElement }) {
		if (isDisabled) {
			event.preventDefault();
			return;
		}
		onclick?.(event);
	}
</script>

<Tooltip content={tooltip}>
	{#snippet trigger({ props })}
		<button
			{...mergeProps(rest, props)}
			type="button"
			aria-label={tooltip}
			aria-disabled={isDisabled || undefined}
			class="inline-flex shrink-0 items-center justify-center rounded-md transition-colors duration-(--duration-fast) ease-standard {sizes[
				size
			]} {isDisabled ? 'cursor-not-allowed text-ink-subtle' : variants[variant]}"
			onclick={handleClick}
		>
			{@render children()}
		</button>
	{/snippet}
</Tooltip>
