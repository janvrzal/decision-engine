<script lang="ts">
	import type { MessageView } from '#lib/api/types.js';
	import Alert from './ui/Alert.svelte';
	import Button from './ui/Button.svelte';

	/** Zpráva v Panelu Dialog (komponenty.md, ChatMessage). */
	let {
		message,
		onretry,
		onmanual,
		retryDisabledReason
	}: {
		message: MessageView;
		onretry?: () => void;
		/** Ruční postup místo AI (UC-07): otevře kontrolní tabulku k vyplnění. */
		onmanual?: () => void;
		retryDisabledReason?: string;
	} = $props();
</script>

{#if message.kind === 'error'}
	<Alert variant="danger" title="Zpráva se nezpracovala">
		{message.text}
		{#snippet actions()}
			{#if onretry}
				<Button variant="secondary" onclick={onretry} disabledReason={retryDisabledReason}>
					Zkusit znovu
				</Button>
			{/if}
			{#if onmanual}
				<Button variant="ghost" onclick={onmanual} disabledReason={retryDisabledReason}>
					Zadat ručně
				</Button>
			{/if}
		{/snippet}
	</Alert>
{:else if message.role === 'user'}
	<div
		class="ml-8 self-end rounded-md bg-surface-sunken px-3 py-3 text-body whitespace-pre-line text-ink"
	>
		<span class="sr-only">Vy:</span>
		{message.text}
	</div>
{:else}
	<div class="mr-8 text-body text-ink">
		<span class="sr-only">Asistent:</span>
		{message.text}
	</div>
{/if}
