<script lang="ts">
	import type { BarView } from '#lib/api/types.js';
	import { formatLength } from '#lib/format.js';

	/**
	 * Rozpis po tyčích (plan-rezani.md): textová alternativa plánu s polohami řezů.
	 * Najetí nebo fokus na díl zvýrazní všechny jeho výskyty v plánu.
	 */
	let { bars, onhighlight }: { bars: BarView[]; onhighlight: (partId: string | null) => void } =
		$props();

	function numbers(bar: BarView): string {
		const first = bar.numbers[0];
		const last = bar.numbers[bar.numbers.length - 1];
		return first === last ? `Tyč ${first}` : `Tyč ${first}–${last}`;
	}

	const TAIL = { remnant: 'zbytek', waste: 'odpad', none: '' } as const;
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
	class="overflow-x-auto print:overflow-visible"
	role="region"
	aria-label="Rozpis po tyčích, posuvný"
	tabindex="0"
>
	<!-- Pod 640 px je každá tyč karta s popisky místo sloupců (#58). -->
	<table class="w-full border-collapse text-body max-sm:block">
		<caption class="sr-only">Rozpis po tyčích</caption>
		<thead class="max-sm:sr-only">
			<tr class="bg-surface-sunken text-label font-medium text-ink-muted uppercase">
				<th scope="col" class="px-2 py-2 text-left">Tyč</th>
				<th scope="col" class="px-2 py-2 text-right">Počet</th>
				<th scope="col" class="px-2 py-2 text-left">Díly v pořadí řezání</th>
				<th scope="col" class="px-2 py-2 text-left">Polohy řezů od začátku tyče</th>
				<th scope="col" class="px-2 py-2 text-left">Konec tyče</th>
			</tr>
		</thead>
		<tbody class="max-sm:flex max-sm:flex-col max-sm:gap-2">
			{#each bars as bar (bar.numbers[0])}
				<tr class="border-b border-border align-top max-sm:block max-sm:rounded-md max-sm:border">
					<th
						scope="row"
						class="px-2 py-2 text-left font-semibold whitespace-nowrap text-ink max-sm:block"
					>
						{numbers(bar)}
						<span class="block text-small font-normal text-ink-muted">
							{formatLength(bar.length_mm)}
						</span>
					</th>
					<td class="px-2 py-2 text-right numeric max-sm:block max-sm:text-left">
						<span class="text-small text-ink-muted sm:hidden">Počet:</span>
						{bar.numbers.length}×
					</td>
					<td class="px-2 py-2 max-sm:block">
						<span class="text-small text-ink-muted sm:hidden">Díly v pořadí řezání:</span>
						<ul class="flex flex-wrap gap-1">
							{#each bar.pieces as piece, index (`${piece.part_id}-${index}`)}
								<li>
									<button
										type="button"
										class="rounded-sm px-1 hover:bg-surface-sunken"
										onmouseenter={() => onhighlight(piece.part_id)}
										onmouseleave={() => onhighlight(null)}
										onfocus={() => onhighlight(piece.part_id)}
										onblur={() => onhighlight(null)}
									>
										{piece.name} <span class="numeric">{formatLength(piece.length_mm)}</span>
									</button>
								</li>
							{/each}
						</ul>
					</td>
					<td class="px-2 py-2 numeric max-sm:block">
						<span class="text-small text-ink-muted sm:hidden">Polohy řezů:</span>
						{bar.cuts_mm.length ? bar.cuts_mm.map((cut) => formatLength(cut)).join(', ') : '—'}
					</td>
					<td class="px-2 py-2 whitespace-nowrap max-sm:block">
						<span class="text-small text-ink-muted sm:hidden">Konec tyče:</span>
						{#if bar.tail === 'none'}
							—
						{:else}
							{TAIL[bar.tail]} <span class="numeric">{formatLength(bar.tail_length_mm)}</span>
						{/if}
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
	<p class="mt-2 text-small text-ink-muted">
		Polohy jsou značky měřené od začátku tyče; řežte za značkou, prořez jde do odpadu. Je-li
		nastavený zarovnávací ořez, první řez zarovná čelo tyče.
	</p>
</div>
