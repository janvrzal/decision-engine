<script lang="ts">
	import { Dialog } from 'bits-ui';
	import X from '@lucide/svelte/icons/x';
	import type { Snippet } from 'svelte';

	/**
	 * Modální okno (Bits Dialog, komponenty.md `Modal`): nadpis, obsah a patička s akcemi
	 * vpravo (hlavní poslední). Past fokusu; ✕, Esc i klik mimo zavřou a fokus se vrátí
	 * na spouštěcí prvek.
	 */
	let {
		open = $bindable(false),
		title,
		description,
		children,
		footer
	}: {
		open?: boolean;
		title: string;
		description?: string;
		children: Snippet;
		footer?: Snippet;
	} = $props();
</script>

<Dialog.Root bind:open>
	<Dialog.Portal>
		<Dialog.Overlay class="fixed inset-0 z-40 bg-ink/30" />
		<Dialog.Content
			class="fixed top-1/2 left-1/2 z-50 flex w-130 max-w-full -translate-x-1/2 -translate-y-1/2 flex-col rounded-lg border border-border bg-surface shadow-overlay"
		>
			<div class="flex items-start justify-between gap-4 border-b border-border px-6 py-4">
				<div class="flex flex-col gap-1">
					<Dialog.Title class="text-heading text-ink">{title}</Dialog.Title>
					{#if description}
						<Dialog.Description class="text-small text-ink-muted">{description}</Dialog.Description>
					{/if}
				</div>
				<Dialog.Close
					class="inline-flex size-8 shrink-0 items-center justify-center rounded-md text-ink hover:bg-surface-sunken"
					aria-label="Zavřít"
				>
					<X size={16} strokeWidth={1.5} aria-hidden="true" />
				</Dialog.Close>
			</div>
			<div class="flex flex-col gap-4 px-6 py-4">
				{@render children()}
			</div>
			{#if footer}
				<div class="flex justify-end gap-2 border-t border-border px-6 py-3">
					{@render footer()}
				</div>
			{/if}
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
