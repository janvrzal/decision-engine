<script lang="ts">
	import CircleQuestionMark from '@lucide/svelte/icons/circle-question-mark';
	import type { HTMLInputAttributes } from 'svelte/elements';
	import Tooltip from '../ui/Tooltip.svelte';

	/**
	 * Vstup buňky kontrolní tabulky a parametrů (komponenty.md: NumberUnitInput, EditableGrid).
	 * Stavy: potvrzená, nepotvrzená (přerušovaný okraj `proposal` + „?“ + tooltip), chybná.
	 * Číslo je vpravo, jednotka uvnitř pole vpravo. Potvrzení hodnoty řeší rodič (`oncommit`).
	 */
	let {
		value = $bindable(''),
		label,
		unit,
		numeric = false,
		unconfirmed = false,
		unconfirmedNote = null,
		error,
		previous = null,
		ref = $bindable(null),
		oncommit,
		onvalue,
		...rest
	}: Omit<HTMLInputAttributes, 'value'> & {
		value?: string;
		label: string;
		unit?: string;
		numeric?: boolean;
		unconfirmed?: boolean;
		/** Původ nepotvrzené hodnoty od backendu (výchozí, odhad AI, ze souboru). */
		unconfirmedNote?: string | null;
		error?: string | null;
		/** Hodnota v potvrzené revizi, změnil-li ji návrh (ukáže se přeškrtnutá). */
		previous?: string | null;
		ref?: HTMLInputElement | null;
		oncommit?: () => void;
		onvalue?: (value: string) => void;
	} = $props();

	const id = $props.id();
	let border = $derived(
		error ? 'border-danger' : unconfirmed ? 'border-dashed border-proposal' : 'border-border-strong'
	);
	let background = $derived(previous ? 'bg-proposal-bg' : 'bg-surface');
</script>

<div class="flex min-w-0 flex-col gap-1">
	<div class="flex h-8 items-center rounded-sm border {background} {border}">
		<input
			{...rest}
			bind:this={ref}
			bind:value
			{id}
			aria-label={label}
			aria-invalid={error ? true : undefined}
			aria-describedby={error || unconfirmed || previous ? `${id}-note` : undefined}
			inputmode={numeric ? 'decimal' : undefined}
			autocomplete="off"
			oninput={() => onvalue?.(value)}
			onblur={() => oncommit?.()}
			class="h-full w-full min-w-0 rounded-sm bg-transparent px-2 text-body text-ink outline-none {numeric
				? 'text-right numeric'
				: ''}"
		/>
		{#if unit}
			<span class="pr-2 text-small text-ink-muted" aria-hidden="true">{unit}</span>
		{/if}
		{#if unconfirmed && !error}
			<Tooltip content={unconfirmedNote ?? 'Výchozí hodnota nebo odhad AI, ověřte.'}>
				{#snippet trigger({ props })}
					<!-- Mimo pořadí tabulátoru: z klávesnice stejnou informaci nese popis pole. -->
					<span
						{...props}
						tabindex="-1"
						role="img"
						aria-label="Nepotvrzená hodnota"
						class="flex pr-2 text-proposal"
					>
						<CircleQuestionMark size={14} strokeWidth={2} aria-hidden="true" />
					</span>
				{/snippet}
			</Tooltip>
		{/if}
	</div>
	{#if error}
		<p id="{id}-note" class="text-small text-danger">{error}</p>
	{:else if previous}
		<p id="{id}-note" class="text-small text-ink-muted">
			původně <s>{previous}</s>
		</p>
	{:else if unconfirmed}
		<span id="{id}-note" class="sr-only">
			Nepotvrzená hodnota: {unconfirmedNote ?? 'výchozí nebo odhad AI, ověřte.'}
		</span>
	{/if}
</div>
