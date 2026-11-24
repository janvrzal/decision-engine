<script lang="ts">
	import Check from '@lucide/svelte/icons/check';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import type { StepView } from '#lib/api/types.js';

	type StepId = StepView['id'];

	/**
	 * Ukazatel kroků Zadání → Kontrola údajů → Plán a cena (komponenty.md).
	 * Stav nikdy jen barvou: aktivní krok má `aria-current`, hotový fajfku,
	 * neaktuální ikonu a slovo. Pod 1280 px je název vidět jen u aktivního kroku.
	 */
	let {
		steps,
		current,
		onselect
	}: {
		steps: StepView[];
		/** Právě zobrazený krok; má `aria-current` i ve stavu „neaktuální“. */
		current?: StepId;
		onselect?: (id: StepId) => void;
	} = $props();

	function isCurrent(step: StepView): boolean {
		return current === undefined ? step.state === 'active' : step.id === current;
	}

	const stateText = {
		pending: 'čeká',
		active: 'aktuální krok',
		done: 'hotovo',
		stale: 'neaktuální',
		unavailable: 'zatím nedostupné'
	} as const;
</script>

<nav aria-label="Kroky zakázky">
	<ol class="flex items-center gap-2">
		{#each steps as step, index (step.id)}
			{@const clickable = step.state === 'done' || step.state === 'stale'}
			<li class="flex items-center gap-2">
				{#if index > 0}
					<span class="h-px w-4 bg-border-strong xl:w-6" aria-hidden="true"></span>
				{/if}
				{#if clickable}
					<button
						type="button"
						class="flex items-center gap-2 rounded-md px-1 py-1 hover:bg-surface-sunken {isCurrent(
							step
						)
							? 'bg-surface-sunken'
							: ''}"
						onclick={() => onselect?.(step.id)}
						aria-current={isCurrent(step) ? 'step' : undefined}
						data-state={step.state}
					>
						{@render content(step, index)}
					</button>
				{:else}
					<span
						class="flex items-center gap-2 px-1 py-1"
						aria-current={isCurrent(step) ? 'step' : undefined}
						data-state={step.state}
					>
						{@render content(step, index)}
					</span>
				{/if}
			</li>
		{/each}
	</ol>
</nav>

{#snippet content(step: StepView, index: number)}
	<span
		class="flex size-6 shrink-0 items-center justify-center rounded-sm text-label font-semibold numeric {step.state ===
		'active'
			? 'bg-primary text-on-primary'
			: step.state === 'done'
				? 'bg-success-bg text-success'
				: step.state === 'stale'
					? 'bg-stale-bg text-stale'
					: step.state === 'pending'
						? 'border border-border-strong text-ink-muted'
						: 'border border-border text-ink-subtle'}"
		aria-hidden="true"
	>
		{#if step.state === 'done'}
			<Check size={14} strokeWidth={2} />
		{:else if step.state === 'stale'}
			<RefreshCw size={14} strokeWidth={2} />
		{:else}
			{index + 1}
		{/if}
	</span>
	<span
		class="text-body {step.state === 'active'
			? 'font-semibold text-ink'
			: step.state === 'unavailable'
				? 'text-ink-subtle'
				: 'text-ink-muted'} {step.state === 'active' || isCurrent(step)
			? ''
			: 'sr-only xl:not-sr-only'}"
	>
		{step.label}
		<span class="sr-only">({stateText[step.state]})</span>
	</span>
	{#if step.state === 'stale'}
		<span class="text-small text-stale">neaktuální</span>
	{/if}
{/snippet}
