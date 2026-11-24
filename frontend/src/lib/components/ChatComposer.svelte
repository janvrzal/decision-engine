<script lang="ts">
	import { MAX_MESSAGE_CHARS } from '#lib/limits.js';
	import Send from '@lucide/svelte/icons/send';
	import Button from './ui/Button.svelte';
	import TextArea from './ui/TextArea.svelte';

	/**
	 * Pole pro zprávu: Enter odešle, Shift+Enter vloží nový řádek (komponenty.md).
	 * Prázdnou zprávu odeslat nelze; `sendDisabledReason` vypne odesílání s důvodem.
	 */
	let {
		value = $bindable(''),
		ref = $bindable(null),
		sendDisabledReason,
		onsend
	}: {
		value?: string;
		ref?: HTMLTextAreaElement | null;
		sendDisabledReason?: string;
		onsend?: (text: string) => void;
	} = $props();

	let reason = $derived(
		sendDisabledReason ?? (value.trim() === '' ? 'Nejdřív napište zprávu.' : undefined)
	);

	function send() {
		if (reason !== undefined) return;
		onsend?.(value.trim());
		value = '';
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
			event.preventDefault();
			send();
		}
	}
</script>

<div class="flex flex-col gap-2">
	<TextArea
		bind:value
		bind:ref
		label="Zpráva"
		hideLabel
		rows={3}
		maxlength={MAX_MESSAGE_CHARS}
		placeholder="Napište, co potřebujete…"
		onkeydown={handleKeydown}
	/>
	<div class="flex items-center justify-between gap-2">
		<p class="text-small text-ink-subtle">Enter odešle, Shift+Enter nový řádek</p>
		<Button variant="primary" disabledReason={reason} onclick={send}>
			<Send size={16} strokeWidth={1.5} aria-hidden="true" />
			Odeslat
		</Button>
	</div>
</div>
