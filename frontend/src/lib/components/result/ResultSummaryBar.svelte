<script lang="ts">
	import Printer from '@lucide/svelte/icons/printer';
	import Save from '@lucide/svelte/icons/save';
	import type { ResultView, UserEvent } from '#lib/api/types.js';
	import { formatPercent } from '#lib/format.js';
	import SolutionStatusBadge from '../SolutionStatusBadge.svelte';
	import Button from '../ui/Button.svelte';

	/** Souhrnná lišta připnutá dole v kroku Plán a cena (komponenty.md, ResultSummaryBar). */
	let {
		result,
		proposalPending,
		onsend,
		onreview,
		onsave
	}: {
		result: ResultView;
		proposalPending: boolean;
		onsend: (event: UserEvent) => void;
		onreview: () => void;
		onsave: () => void;
	} = $props();

	let summary = $derived(
		`${result.metrics.bars_used} ${result.metrics.bars_used === 1 ? 'tyč' : result.metrics.bars_used < 5 ? 'tyče' : 'tyčí'} · výtěžnost ${formatPercent(result.metrics.yield_ratio)}`
	);
</script>

<div
	class="sticky bottom-0 flex flex-wrap items-center gap-3 border-t border-border bg-surface px-6 py-3 shadow-raised print:hidden"
>
	<SolutionStatusBadge status={result.status} label={result.status_label} stale={result.stale} />
	<p class="flex-1 text-body text-ink numeric {result.stale ? 'text-ink-muted line-through' : ''}">
		{summary}
	</p>
	{#if result.stale}
		{#if proposalPending}
			<Button variant="secondary" onclick={onreview}>Zkontrolovat změny</Button>
		{:else}
			<Button variant="secondary" onclick={() => onsend({ type: 'SolveRequested' })}>
				Přepočítat
			</Button>
		{/if}
	{/if}
	<!-- PDF přibude s kalkulací (M5); do té doby se nenabízí (AGENTS.md pravidlo 9). -->
	<Button
		variant="secondary"
		onclick={() => window.print()}
		disabledReason={result.stale ? 'Plán je neaktuální, nejdřív ho přepočítejte.' : undefined}
	>
		<Printer size={16} strokeWidth={1.5} aria-hidden="true" />
		Vytisknout plán
	</Button>
	<Button variant="primary" onclick={onsave}>
		<Save size={16} strokeWidth={1.5} aria-hidden="true" />
		Uložit zakázku
	</Button>
</div>
