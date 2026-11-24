<script lang="ts">
	/**
	 * Metrika výsledku (komponenty.md): popisek, hodnota stylem `metric` s jednotkou
	 * v `ink-muted`, volitelný podtext. Hodnotu dodává backend, karta ji jen ukáže.
	 */
	let { label, value, unit, note }: { label: string; value: string; unit?: string; note?: string } =
		$props();
</script>

<!-- Položka seznamu `<dl>`: čtečka spojí název metriky s hodnotou (#59). -->
<div class="flex flex-col gap-1 rounded-md border border-border bg-surface p-4">
	<dt class="text-small text-ink-muted">{label}</dt>
	<dd class="text-metric text-ink numeric">
		{value}{#if unit}<span class="ml-1 text-body text-ink-muted">{unit}</span>{/if}
	</dd>
	{#if note}<dd class="text-small text-ink-muted">{note}</dd>{/if}
</div>
