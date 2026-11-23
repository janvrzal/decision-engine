<script lang="ts" module>
	export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

	const base =
		'inline-flex h-8 shrink-0 items-center justify-center gap-1 rounded-md px-3 text-body font-semibold whitespace-nowrap transition-colors duration-(--duration-fast) ease-standard';

	const enabled: Record<ButtonVariant, string> = {
		primary: 'bg-primary text-on-primary hover:bg-primary-hover',
		secondary: 'border border-border-strong bg-surface text-ink hover:bg-surface-sunken',
		ghost: 'text-ink hover:bg-surface-sunken',
		danger: 'bg-danger text-surface hover:bg-ink'
	};

	const disabled: Record<ButtonVariant, string> = {
		primary: 'cursor-not-allowed bg-surface-sunken text-ink-subtle',
		secondary: 'cursor-not-allowed border border-border bg-surface text-ink-subtle',
		ghost: 'cursor-not-allowed text-ink-subtle',
		danger: 'cursor-not-allowed bg-surface-sunken text-ink-subtle'
	};

	export function buttonClass(variant: ButtonVariant, isDisabled: boolean): string {
		return `${base} ${isDisabled ? disabled[variant] : enabled[variant]}`;
	}
</script>

<script lang="ts">
	import { mergeProps } from 'bits-ui';
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';
	import Tooltip from './Tooltip.svelte';

	/**
	 * Tlačítko. Neaktivní tlačítko má vždy důvod (`disabledReason`): zůstává v pořadí
	 * tabulátoru s `aria-disabled`, důvod je v tooltipu i pro čtečky (komponenty.md).
	 */
	let {
		variant = 'secondary',
		disabledReason,
		children,
		onclick,
		class: className = '',
		...rest
	}: Omit<HTMLButtonAttributes, 'disabled'> & {
		variant?: ButtonVariant;
		disabledReason?: string;
		children: Snippet;
	} = $props();

	const reasonId = $props.id();
	let isDisabled = $derived(disabledReason !== undefined);

	function handleClick(event: MouseEvent & { currentTarget: EventTarget & HTMLButtonElement }) {
		if (isDisabled) {
			event.preventDefault();
			return;
		}
		onclick?.(event);
	}
</script>

{#snippet button(extra: Record<string, unknown>)}
	<button
		{...mergeProps(rest, extra)}
		type="button"
		class="{buttonClass(variant, isDisabled)} {className}"
		aria-disabled={isDisabled || undefined}
		aria-describedby={isDisabled ? reasonId : undefined}
		onclick={handleClick}
	>
		{@render children()}
	</button>
	{#if isDisabled}
		<span id={reasonId} class="sr-only">{disabledReason}</span>
	{/if}
{/snippet}

{#if disabledReason}
	<Tooltip content={disabledReason}>
		{#snippet trigger({ props })}
			{@render button(props as Record<string, unknown>)}
		{/snippet}
	</Tooltip>
{:else}
	{@render button({})}
{/if}
