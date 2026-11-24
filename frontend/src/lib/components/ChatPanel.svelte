<script lang="ts">
	import { tick } from 'svelte';
	import type { Snippet } from 'svelte';
	import type { MessageView } from '#lib/api/types.js';
	import type { ExamplePrompt } from '#lib/examples.js';
	import type { Pending } from '#lib/session.svelte.js';
	import ChatComposer from './ChatComposer.svelte';
	import ChatMessageItem from './ChatMessageItem.svelte';
	import SuggestionChips from './SuggestionChips.svelte';
	import Loader from './ui/Loader.svelte';

	/**
	 * Panel Dialog (mapa obrazovek): zprávy, průběh zpracování, ukázky a pole pro zprávu.
	 * Zprávy a jejich texty dodává backend; panel jen zobrazuje a posílá `MessageSent`.
	 */
	let {
		messages,
		pending,
		suggestions,
		extractionAvailable,
		onsend,
		onretry,
		onmanual,
		header
	}: {
		messages: MessageView[];
		pending: Pending | null;
		suggestions: ExamplePrompt[];
		extractionAvailable: boolean;
		onsend: (text: string) => void;
		/** Pošle znovu zprávu, kterou AI nezpracovala (`retry_text` chybové zprávy). */
		onretry: (text: string) => void;
		onmanual: () => void;
		header?: Snippet;
	} = $props();

	let draft = $state('');
	let composer = $state<HTMLTextAreaElement | null>(null);
	let log = $state<HTMLElement | null>(null);
	let stickToBottom = $state(true);

	let sendDisabledReason = $derived(
		!extractionAvailable
			? 'AI není nastavená (LLM_API_KEY a LLM_MODEL v .env).'
			: pending
				? 'Počkejte, až se dokončí předchozí zpráva.'
				: undefined
	);
	let failedText = $derived.by(() => {
		const last = messages.at(-1);
		return last?.kind === 'error' ? (last.retry_text ?? null) : null;
	});

	/** Vrátí nezpracovanou zprávu do pole, aby ji šlo upravit a poslat znovu. */
	function editFailed() {
		if (failedText === null) return;
		draft = failedText;
		composer?.focus();
	}

	function pick(text: string) {
		draft = text;
		composer?.focus();
	}

	function send(text: string) {
		stickToBottom = true;
		onsend(text);
	}

	// Posun na novou zprávu, jen když uživatel nečte starší (komponenty.md, message-scroller).
	function onscroll() {
		if (!log) return;
		stickToBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 48;
	}
	$effect(() => {
		void messages.length;
		void pending;
		if (stickToBottom && log) {
			void tick().then(() => log?.scrollTo({ top: log.scrollHeight }));
		}
	});
</script>

<section class="flex min-h-0 flex-1 flex-col" aria-label="Dialog">
	{#if header}
		{@render header()}
	{/if}
	<div
		bind:this={log}
		{onscroll}
		class="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4"
		role="log"
		aria-live="polite"
	>
		<div class="mt-auto flex flex-col gap-2">
			<p class="text-body text-ink">
				Popište, co potřebujete nařezat: díly, jejich délky a počty a z jakých tyčí. Údaje převedu
				do tabulky, kterou před výpočtem zkontrolujete.
			</p>
			<p class="text-small text-ink-muted">Čísla v plánu vždy spočítá program, ne AI.</p>
		</div>
		{#each messages as message, index (message.id)}
			<ChatMessageItem
				{message}
				onretry={index === messages.length - 1 && message.retry_text
					? () => onretry(message.retry_text ?? '')
					: undefined}
				onmanual={index === messages.length - 1 ? onmanual : undefined}
				retryDisabledReason={pending ? 'Probíhá zpracování.' : undefined}
			/>
		{/each}
		{#if pending?.kind === 'extraction'}
			{#if pending.text}
				<ChatMessageItem
					message={{
						id: -1,
						role: 'user',
						kind: 'text',
						text: pending.text,
						proposal: false,
						offer_manual: false
					}}
				/>
			{/if}
			<Loader label="Připravuji údaje ke kontrole…" />
		{/if}
		{#if messages.length === 0 && !pending}
			<SuggestionChips label="Vyzkoušejte ukázku:" {suggestions} onpick={pick} />
		{/if}
	</div>
	<div class="border-t border-border p-4">
		{#if failedText !== null && draft === ''}
			<p class="mb-2 text-small text-ink-muted">
				Zprávu můžete také
				<button
					type="button"
					class="rounded-sm text-ink underline decoration-accent-text underline-offset-2 hover:no-underline"
					onclick={editFailed}
				>
					upravit a poslat znovu
				</button>.
			</p>
		{/if}
		<ChatComposer bind:value={draft} bind:ref={composer} {sendDisabledReason} onsend={send} />
	</div>
</section>
