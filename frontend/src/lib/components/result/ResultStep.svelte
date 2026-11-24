<script lang="ts">
	import CostSummary from './CostSummary.svelte';
	import Pencil from '@lucide/svelte/icons/pencil';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import type { ResultView, UserEvent } from '#lib/api/types.js';
	import { formatLength, formatMillimeters, formatPercent } from '#lib/format.js';
	import MetricCard from '../MetricCard.svelte';
	import SolutionStatusBadge from '../SolutionStatusBadge.svelte';
	import Alert from '../ui/Alert.svelte';
	import Button from '../ui/Button.svelte';
	import Collapsible from '../ui/Collapsible.svelte';
	import EmptyState from '../ui/EmptyState.svelte';
	import Loader from '../ui/Loader.svelte';
	import BarBreakdown from './BarBreakdown.svelte';
	import CuttingPlan from './CuttingPlan.svelte';

	/**
	 * Krok Plán a cena (mapa obrazovek, Panel Plán): štítek, metriky, plán, rozpis.
	 * Všechna čísla dodává backend; tady se jen formátují (`cs-CZ`).
	 */
	let {
		result,
		solving,
		proposalPending,
		editReason,
		onsend,
		onreview
	}: {
		result: ResultView | null;
		solving: boolean;
		proposalPending: boolean;
		/** Proč teď nejde „Upravit údaje“; `undefined` = jde. */
		editReason: string | undefined;
		onsend: (event: UserEvent) => void;
		onreview: () => void;
	} = $props();

	let highlighted = $state<string | null>(null);
	let breakdownOpen = $state(false);

	function number(value: number | string): string {
		return formatMillimeters(value);
	}
</script>

<section class="flex flex-col gap-6" aria-labelledby="result-title" aria-busy={solving}>
	{#if result && !solving}
		<!-- Hlavička papíru k pile: na obrazovce je název v hlavičce zakázky. -->
		<p class="hidden text-heading text-ink print:block">
			{result.project_name}{#if result.material}&nbsp;· {result.material}{/if}
		</p>
	{/if}
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div class="flex items-center gap-3">
			<h2 id="result-title" tabindex="-1" class="text-title text-ink">Nářezový plán</h2>
			{#if result && !solving}
				<!-- Neaktuální plán: štítek kvality patří předchozí verzi, proto je ztlumený. -->
				<span class={result.stale ? 'opacity-60' : ''}>
					<SolutionStatusBadge status={result.status} label={result.status_label} />
				</span>
			{/if}
		</div>
		{#if result && !solving && result.status_note}
			<p class="w-full text-small text-ink-muted {result.stale ? 'opacity-60' : ''}">
				{result.status_note}
			</p>
		{/if}
		{#if result && !solving && !proposalPending}
			<div class="print:hidden">
				<Button
					variant="secondary"
					disabledReason={editReason}
					onclick={() => onsend({ type: 'EditRequested' })}
				>
					<Pencil size={16} strokeWidth={1.5} aria-hidden="true" />
					Upravit údaje
				</Button>
			</div>
		{/if}
	</div>

	{#if solving}
		<div class="rounded-lg border border-border bg-surface p-6">
			<Loader size="large" label="Počítám plán…" />
		</div>
	{:else if !result}
		<div class="rounded-lg border border-border bg-surface">
			<EmptyState title="Plán zatím není spočítaný">
				Potvrďte údaje v kroku Kontrola údajů a plán se spočítá.
			</EmptyState>
		</div>
	{:else}
		{#if result.stale}
			<div
				class="flex flex-wrap items-center gap-3 rounded-md border border-stale bg-stale-bg px-3 py-3 text-stale"
				role="status"
			>
				<RefreshCw size={16} strokeWidth={1.5} aria-hidden="true" />
				<p class="flex-1 text-body">
					<span class="font-semibold">Neaktuální:</span>
					{result.stale_reason}. Plán odpovídá předchozí verzi zakázky.
				</p>
				{#if proposalPending}
					<Button variant="primary" onclick={onreview}>Zkontrolovat změny</Button>
				{:else}
					<Button variant="primary" onclick={() => onsend({ type: 'SolveRequested' })}>
						Přepočítat
					</Button>
				{/if}
			</div>
		{/if}

		{#if result.unplaced.length > 0}
			<Alert variant="warning" title="Neumístěné kusy">
				<ul class="list-disc pl-4">
					{#each result.unplaced as item (item.part_id)}
						<li>
							{item.quantity}× {item.name}
							{formatLength(item.length_mm)}: {item.reason}
						</li>
					{/each}
				</ul>
			</Alert>
		{/if}

		<dl
			class="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5 {result.stale
				? 'opacity-60'
				: ''}"
		>
			<MetricCard
				label="Spotřebované tyče"
				value={number(result.metrics.bars_used)}
				unit="ks"
				note={result.metrics.bars_by_length
					.map((item) => `${item.count}× ${formatLength(item.length_mm)}`)
					.join(', ')}
			/>
			<MetricCard label="Délka dílů" value={number(result.metrics.parts_length_mm)} unit="mm" />
			<MetricCard
				label="Využitelné zbytky"
				value={number(result.metrics.remnant_length_mm)}
				unit="mm"
				note="{result.metrics.remnant_count} ks"
			/>
			<MetricCard label="Odpad" value={number(result.metrics.waste_length_mm)} unit="mm" />
			<MetricCard
				label="Výtěžnost"
				value={formatPercent(result.metrics.yield_ratio)}
				note="délka dílů / spotřeba"
			/>
		</dl>

		<CostSummary cost={result.cost} stale={result.stale} />

		<div class="rounded-lg border border-border bg-surface p-4">
			<CuttingPlan svg={result.svg} bind:highlighted dimmed={result.stale} />
		</div>

		<div class="print:hidden">
			<Collapsible label="Rozpis po tyčích" bind:open={breakdownOpen}>
				<BarBreakdown bars={result.bars} onhighlight={(id: string | null) => (highlighted = id)} />
			</Collapsible>
		</div>
		<!-- Na papíře k pile je rozpis vždy celý, i když je na obrazovce sbalený. -->
		<div class="hidden print:block">
			<h3 class="mb-2 text-heading text-ink">Rozpis po tyčích</h3>
			<BarBreakdown bars={result.bars} onhighlight={() => {}} />
		</div>
	{/if}
</section>
