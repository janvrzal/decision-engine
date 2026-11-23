<script lang="ts" module>
	export interface RadioCard<V> {
		value: V;
		label: string;
		hint: string;
		disabledReason?: string | null;
		note?: string | null;
	}
</script>

<script lang="ts" generics="T extends string">
	import { RadioGroup } from 'bits-ui';

	/**
	 * Výběr jedné možnosti jako karty s názvem a větou nápovědy (komponenty.md).
	 * Neaktivní volba má důvod přímo v kartě.
	 */

	let {
		label,
		value,
		options,
		onchange
	}: {
		label: string;
		value: T | null;
		options: RadioCard<T>[];
		onchange: (value: T) => void;
	} = $props();
</script>

<RadioGroup.Root
	value={value ?? ''}
	onValueChange={(next) => {
		const option = options.find((o) => o.value === next);
		if (option) onchange(option.value);
	}}
	aria-label={label}
	class="grid gap-2 md:grid-cols-3"
>
	{#each options as option (option.value)}
		<RadioGroup.Item
			value={option.value}
			disabled={Boolean(option.disabledReason)}
			class="flex flex-col items-start gap-1 rounded-md border p-3 text-left transition-colors duration-(--duration-fast) ease-standard aria-checked:border-ink aria-checked:bg-surface-sunken data-disabled:cursor-not-allowed data-disabled:border-border {option.disabledReason
				? 'text-ink-subtle'
				: 'border-border-strong bg-surface text-ink hover:bg-surface-sunken'}"
		>
			{#snippet children({ checked })}
				<span class="flex w-full items-center justify-between gap-2">
					<span class="text-body font-semibold">{option.label}</span>
					<span
						class="flex size-4 items-center justify-center rounded-full border border-border-strong"
						aria-hidden="true"
					>
						{#if checked}<span class="size-2 rounded-full bg-ink"></span>{/if}
					</span>
				</span>
				<span class="text-small text-ink-muted">{option.disabledReason ?? option.hint}</span>
				{#if checked && option.note}
					<span class="text-small text-proposal">{option.note}</span>
				{/if}
			{/snippet}
		</RadioGroup.Item>
	{/each}
</RadioGroup.Root>
