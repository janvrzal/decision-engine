<script lang="ts">
	import type { CostView } from '#lib/api/types.js';
	import { formatAmount, formatInteger, formatLength, formatMoney } from '#lib/format.js';

	/**
	 * Orientační cena materiálu (UC-04, první etapa): součet a rozpis po skladových délkách.
	 * Částky počítá backend; chybějící cena je „chybí cena“, nikdy 0 Kč.
	 */
	let { cost, stale = false }: { cost: CostView; stale?: boolean } = $props();
</script>

<section
	class="flex flex-col gap-3 rounded-md border border-border bg-surface p-4 {stale
		? 'opacity-60'
		: ''}"
	aria-labelledby="cost-title"
>
	<div class="flex flex-wrap items-baseline justify-between gap-2">
		<h3 id="cost-title" class="text-heading text-ink">Cena materiálu (orientačně)</h3>
		<span class="text-metric text-ink numeric">
			{#if cost.total !== null}
				{formatAmount(cost.total)}<span class="ml-1 text-body text-ink-muted">Kč</span>
			{:else}
				—
			{/if}
		</span>
	</div>
	{#if cost.lines.length > 0}
		<table class="w-full text-body">
			<caption class="sr-only">Rozpis ceny podle skladových délek</caption>
			<thead class="text-small text-ink-muted">
				<tr>
					<th scope="col" class="py-1 text-left font-medium">Skladová délka</th>
					<th scope="col" class="py-1 text-right font-medium">Kusů</th>
					<th scope="col" class="py-1 text-right font-medium">Cena za kus</th>
					<th scope="col" class="py-1 text-right font-medium">Celkem</th>
				</tr>
			</thead>
			<tbody>
				{#each cost.lines as line (line.stock_id)}
					<tr class="border-t border-border">
						<th scope="row" class="py-1 text-left font-normal numeric">
							{formatLength(line.length_mm)}
						</th>
						<td class="py-1 text-right numeric">{formatInteger(line.count)}</td>
						<td class="py-1 text-right numeric">{formatMoney(line.unit_price)}</td>
						<td class="py-1 text-right numeric">{formatMoney(line.total)}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	{/if}
	{#if cost.note}
		<p class="text-small text-ink-muted">{cost.note}</p>
	{:else}
		<p class="text-small text-ink-muted">
			Jen materiál podle zadaných cen tyčí; bez práce, přirážky a DPH.
		</p>
	{/if}
</section>
