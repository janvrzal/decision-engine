<script lang="ts">
	import FileDown from '@lucide/svelte/icons/file-down';
	import Save from '@lucide/svelte/icons/save';
	import type { ResultView, UserEvent } from '#lib/api/types.js';
	import { NOT_AVAILABLE_REASON } from '#lib/examples.js';
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
	class="sticky bottom-0 flex flex-wrap items-center gap-3 border-t border-border bg-surface px-6 py-3 shadow-raised"
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
	<Button variant="secondary" onclick={onsave}>
		<Save size={16} strokeWidth={1.5} aria-hidden="true" />
		Uložit zakázku
	</Button>
	<Button variant="primary" disabledReason={NOT_AVAILABLE_REASON}>
		<FileDown size={16} strokeWidth={1.5} aria-hidden="true" />
		Stáhnout PDF
	</Button>
</div>
