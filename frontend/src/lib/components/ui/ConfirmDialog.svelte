<script lang="ts">
	import { AlertDialog } from 'bits-ui';
	import type { Snippet } from 'svelte';

	/**
	 * Potvrzení před zahozením práce (komponenty.md `ConfirmDialog`, Bits AlertDialog).
	 * Klik mimo okno nezavře, Esc ano; fokus začíná na bezpečné akci (`initialFocus`).
	 */
	let {
		open = $bindable(false),
		title,
		description,
		initialFocus,
		children,
		footer
	}: {
		open?: boolean;
		title: string;
		/** Co se stane a co by se ztratilo; čtečky ho přečtou s nadpisem. */
		description: string;
		/** Selektor prvku, který dostane fokus po otevření (bezpečná akce „Zrušit“). */
		initialFocus?: string;
		children?: Snippet;
		footer: Snippet;
	} = $props();

	let content = $state<HTMLElement | null>(null);

	function focusInitial(event: Event) {
		const target = initialFocus ? content?.querySelector<HTMLElement>(initialFocus) : null;
		if (!target) return;
		event.preventDefault();
		target.focus();
	}
</script>

<AlertDialog.Root bind:open>
	<AlertDialog.Portal>
		<AlertDialog.Overlay class="fixed inset-0 z-40 bg-ink/30" />
		<AlertDialog.Content
			bind:ref={content}
			onOpenAutoFocus={focusInitial}
			class="fixed top-1/2 left-1/2 z-50 flex w-130 max-w-full -translate-x-1/2 -translate-y-1/2 flex-col rounded-lg border border-border bg-surface shadow-overlay"
		>
			<div class="border-b border-border px-6 py-4">
				<AlertDialog.Title class="text-heading text-ink">{title}</AlertDialog.Title>
			</div>
			<div class="flex flex-col gap-4 px-6 py-4">
				<AlertDialog.Description class="text-body text-ink">{description}</AlertDialog.Description>
				{@render children?.()}
			</div>
			<div class="flex flex-wrap justify-end gap-2 border-t border-border px-6 py-3">
				{@render footer()}
			</div>
		</AlertDialog.Content>
	</AlertDialog.Portal>
</AlertDialog.Root>
