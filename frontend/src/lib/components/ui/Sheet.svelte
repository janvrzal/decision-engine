<script lang="ts">
	import { Dialog } from 'bits-ui';
	import X from '@lucide/svelte/icons/x';
	import type { Snippet } from 'svelte';

	/**
	 * Vysouvací panel přes obsah (Bits Dialog): past fokusu, Esc a klik mimo zavřou,
	 * fokus se vrátí na spouštěcí prvek (komponenty.md, mapa obrazovek).
	 */
	let {
		open = $bindable(false),
		title,
		side = 'left',
		children
	}: {
		open?: boolean;
		title: string;
		side?: 'left' | 'right';
		children: Snippet;
	} = $props();

	const sides = {
		left: 'left-0 w-95 border-r',
		right: 'right-0 w-115 border-l'
	} as const;
</script>

<Dialog.Root bind:open>
	<Dialog.Portal>
		<Dialog.Overlay class="fixed inset-0 z-40 bg-ink/30" />
		<Dialog.Content
			class="fixed inset-y-0 z-50 flex max-w-full flex-col border-border bg-surface shadow-overlay {sides[
				side
			]}"
		>
			<div class="flex items-center justify-between border-b border-border px-4 py-3">
				<Dialog.Title class="text-heading text-ink">{title}</Dialog.Title>
				<Dialog.Close
					class="inline-flex size-8 items-center justify-center rounded-md text-ink hover:bg-surface-sunken"
					aria-label="Zavřít"
				>
					<X size={16} strokeWidth={1.5} aria-hidden="true" />
				</Dialog.Close>
			</div>
			<div class="flex min-h-0 flex-1 flex-col">
				{@render children()}
			</div>
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
