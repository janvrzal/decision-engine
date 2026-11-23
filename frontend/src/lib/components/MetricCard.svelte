<script lang="ts">
	/**
	 * Metrika výsledku (komponenty.md): popisek, hodnota stylem `metric` s jednotkou
	 * v `ink-muted`, volitelný podtext. Hodnotu dodává backend, karta ji jen ukáže.
	 */
	let { label, value, unit, note }: { label: string; value: string; unit?: string; note?: string } =
		$props();
</script>

<div class="flex flex-col gap-1 rounded-md border border-border bg-surface p-4">
	<span class="text-small text-ink-muted">{label}</span>
	<span class="text-metric text-ink numeric">
		{value}{#if unit}<span class="ml-1 text-body text-ink-muted">{unit}</span>{/if}
	</span>
	{#if note}<span class="text-small text-ink-muted">{note}</span>{/if}
</div>
