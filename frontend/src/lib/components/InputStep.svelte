<script lang="ts">
	import { MAX_MESSAGE_CHARS } from '#lib/limits.js';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import FolderOpen from '@lucide/svelte/icons/folder-open';
	import Shuffle from '@lucide/svelte/icons/shuffle';
	import ToolCard from './ToolCard.svelte';
	import Alert from './ui/Alert.svelte';
	import Button from './ui/Button.svelte';
	import TextArea from './ui/TextArea.svelte';
	import { EXAMPLE_PROMPTS, TOOL_DESCRIPTIONS, type Tool } from '#lib/examples.js';
	import type { MessageView } from '#lib/api/types.js';
	import ChatMessageItem from './ChatMessageItem.svelte';

	/** Krok Zadání: velké pole s ukázkou zadání; odeslání jde do dialogu jako `MessageSent`. */
	let {
		capabilities,
		extractionAvailable,
		busy,
		reply = null,
		onsubmit,
		onretry,
		onmanual,
		onload
	}: {
		capabilities: { id: string; label: string }[];
		extractionAvailable: boolean;
		busy: boolean;
		/** Poslední odpověď na zadání (chyba AI, doptání); ukáže se i u hlavního pole. */
		reply?: MessageView | null;
		onsubmit: (text: string) => void;
		onretry?: (text: string) => void;
		/** Ruční zadání bez AI zvoleným nástrojem (UC-13). */
		onmanual: (capability: string) => void;
		/** Otevře okno Načíst zakázku (UC-06). */
		onload: () => void;
	} = $props();

	let manualReason = $derived(busy ? 'Zpracovávám předchozí zadání.' : undefined);

	let tools = $derived<Tool[]>(
		capabilities.map((c) => ({ ...c, description: TOOL_DESCRIPTIONS[c.id] ?? '' }))
	);

	let draft = $state('');
	let exampleIndex = $state(0);
	let example = $derived(EXAMPLE_PROMPTS[exampleIndex % EXAMPLE_PROMPTS.length]);

	function nextExample() {
		exampleIndex += 1;
	}

	let continueReason = $derived(
		!extractionAvailable
			? 'AI není nastavená (LLM_API_KEY a LLM_MODEL v .env).'
			: busy
				? 'Zpracovávám předchozí zadání.'
				: draft.trim() === ''
					? 'Nejdřív popište, co potřebujete nařezat.'
					: undefined
	);

	function submit() {
		if (continueReason) return;
		onsubmit(draft.trim());
	}
</script>

<section class="flex flex-col gap-8" aria-labelledby="input-step-title">
	<div class="flex flex-col gap-4 rounded-lg border border-border bg-surface p-6 shadow-raised">
		<div class="flex flex-col gap-1">
			<h2 id="input-step-title" tabindex="-1" class="text-heading text-balance text-ink">
				Co potřebujete nařezat?
			</h2>
			<p class="text-body text-ink-muted">
				Napište zadání vlastními slovy, jako byste ho říkali kolegovi v dílně.
			</p>
		</div>
		{#if reply}
			<div aria-live="polite">
				<ChatMessageItem
					message={reply}
					onretry={reply.retry_text ? () => onretry?.(reply.retry_text ?? '') : undefined}
					onmanual={() => onmanual('cutting_1d')}
					retryDisabledReason={busy ? 'Probíhá zpracování.' : undefined}
				/>
			</div>
		{/if}
		{#if !extractionAvailable}
			<Alert variant="info" title="AI není nastavená">
				Zadání z textu teď nepůjde zpracovat. Zakázku vyplňte ručně tlačítkem „Zadat ručně“.
			</Alert>
		{/if}
		<TextArea
			bind:value={draft}
			label="Zadání zakázky"
			hideLabel
			rows={6}
			maxlength={MAX_MESSAGE_CHARS}
			placeholder={example?.text}
			hint="Uveďte díly s délkou a počtem, skladovou délku tyčí a případně prořez a ceny."
		/>
		<div class="flex flex-wrap items-center justify-between gap-2">
			<Button variant="ghost" onclick={nextExample}>
				<Shuffle size={16} strokeWidth={1.5} aria-hidden="true" />
				Další ukázka
			</Button>
			<Button variant="primary" disabledReason={continueReason} onclick={submit}>
				Pokračovat
				<ArrowRight size={16} strokeWidth={1.5} aria-hidden="true" />
			</Button>
		</div>
	</div>

	<div class="flex flex-col gap-3">
		<div class="flex flex-wrap items-baseline justify-between gap-2">
			<h2 class="text-heading text-ink">Nebo začněte nástrojem</h2>
			<div class="flex flex-wrap gap-2">
				<Button variant="ghost" onclick={onload}>
					<FolderOpen size={16} strokeWidth={1.5} aria-hidden="true" />
					Načíst zakázku
				</Button>
				<Button
					variant={extractionAvailable ? 'ghost' : 'primary'}
					disabledReason={manualReason}
					onclick={() => onmanual(tools[0]?.id ?? 'cutting_1d')}
				>
					Zadat ručně
				</Button>
			</div>
		</div>
		<ul class="grid gap-4 md:grid-cols-2">
			{#each tools as tool (tool.id)}
				<li>
					<ToolCard {tool} disabledReason={manualReason} onselect={() => onmanual(tool.id)} />
				</li>
			{/each}
		</ul>
	</div>
</section>
