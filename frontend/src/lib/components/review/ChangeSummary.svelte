<script lang="ts">
	import Undo from '@lucide/svelte/icons/undo-2';
	import type { ChangesView, RemovedPartView, RemovedStockView } from '#lib/api/types.js';
	import { formatInteger, formatLength, formatMoney } from '#lib/format.js';
	import Button from '../ui/Button.svelte';

	/**
	 * Souhrn změn navazující úpravy (komponenty.md, ChangeSummary): přerušovaný okraj
	 * `proposal` = ještě neplatí. Texty změn skládá backend; odebraný řádek jde vrátit.
	 */
	let {
		changes,
		busy,
		onrestorepart,
		onrestorestock
	}: {
		changes: ChangesView;
		busy: boolean;
		onrestorepart: (row: RemovedPartView) => void;
		onrestorestock: (row: RemovedStockView) => void;
	} = $props();

	let reason = $derived(busy ? 'Počkejte na dokončení.' : undefined);
</script>

<section
	class="flex flex-col gap-2 rounded-md border border-dashed border-proposal bg-proposal-bg px-4 py-3"
	aria-labelledby="change-summary-title"
>
	<h3 id="change-summary-title" class="text-heading text-ink">
		Úprava zakázky: změny oproti verzi {changes.base_revision + 1}
	</h3>
	{#if changes.summary.length === 0}
		<p class="text-body text-ink-muted">
			Zatím beze změn. Upravte údaje v tabulkách, nebo změnu napište do dialogu.
		</p>
	{:else}
		<ul class="flex list-disc flex-col gap-1 pl-5 text-body text-ink">
			{#each changes.summary as line, index (index)}
				<li>{line}</li>
			{/each}
		</ul>
	{/if}
	{#if changes.removed_parts.length > 0 || changes.removed_stock.length > 0}
		<ul class="flex flex-col gap-1" aria-label="Odebrané řádky">
			{#each changes.removed_parts as row (row.id)}
				<li class="flex flex-wrap items-center gap-2 text-body">
					<s class="text-ink-muted">
						{row.name}
						{formatLength(row.length_mm)} × {formatInteger(row.quantity)} ks
					</s>
					<Button variant="ghost" disabledReason={reason} onclick={() => onrestorepart(row)}>
						<Undo size={16} strokeWidth={1.5} aria-hidden="true" />
						Vrátit díl {row.name}
					</Button>
				</li>
			{/each}
			{#each changes.removed_stock as row (row.id)}
				<li class="flex flex-wrap items-center gap-2 text-body">
					<s class="text-ink-muted">{formatLength(row.length_mm)}, {formatMoney(row.price)}</s>
					<Button variant="ghost" disabledReason={reason} onclick={() => onrestorestock(row)}>
						<Undo size={16} strokeWidth={1.5} aria-hidden="true" />
						Vrátit skladovou délku {formatLength(row.length_mm)}
					</Button>
				</li>
			{/each}
		</ul>
	{/if}
	<p class="text-small text-ink-muted">
		Změny se projeví až po potvrzení. Do té doby platí původní plán.
	</p>
</section>
