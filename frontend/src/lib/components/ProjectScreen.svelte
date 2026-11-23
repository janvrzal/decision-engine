<script lang="ts">
	import PanelLeftClose from '@lucide/svelte/icons/panel-left-close';
	import { MediaQuery } from 'svelte/reactivity';
	import type { StepView, UserEvent, ViewModel } from '#lib/api/types.js';
	import { EXAMPLE_PROMPTS } from '#lib/examples.js';
	import type { Session } from '#lib/session.svelte.js';
	import AppBar from './AppBar.svelte';
	import ChatPanel from './ChatPanel.svelte';
	import ChatRail from './ChatRail.svelte';
	import InputStep from './InputStep.svelte';
	import ProjectHeader from './ProjectHeader.svelte';
	import ResultStep from './result/ResultStep.svelte';
	import ResultSummaryBar from './result/ResultSummaryBar.svelte';
	import ReviewStep from './review/ReviewStep.svelte';
	import Alert from './ui/Alert.svelte';
	import Button from './ui/Button.svelte';
	import IconButton from './ui/IconButton.svelte';
	import Sheet from './ui/Sheet.svelte';

	/**
	 * Pracovní obrazovka zakázky (mapa obrazovek). Krok určuje backend (`project.step`);
	 * klik na hotový krok jen přepne zobrazení. Od 1280 px Dialog vlevo, 768–1279 px
	 * vysouvací panel.
	 */
	let { session, view }: { session: Session; view: ViewModel } = $props();

	const wide = new MediaQuery('min-width: 1280px');
	let chatCollapsed = $state(false);
	let chatSheetOpen = $state(false);
	let shownStep = $state<StepView['id'] | null>(null);

	$effect(() => {
		if (wide.current) chatSheetOpen = false;
	});
	// Když backend posune krok (nový návrh, výsledek), zobrazí se nový krok.
	$effect(() => {
		void view.project.step;
		shownStep = null;
	});

	let solving = $derived(session.pending?.kind === 'solving');
	let step = $derived(solving ? 'result' : (shownStep ?? view.project.step));
	let busy = $derived(session.pending !== null);
	let steps = $derived(
		view.project.steps.map((s) => ({
			...s,
			state: s.id === step && s.state !== 'stale' ? ('active' as const) : s.state
		}))
	);

	function send(event: UserEvent) {
		void session.send(event);
	}

	function sendMessage(text: string) {
		chatSheetOpen = false;
		send({ type: 'MessageSent', text });
	}

	function selectStep(id: StepView['id']) {
		const target = view.project.steps.find((s) => s.id === id);
		if (target && target.state !== 'unavailable' && target.state !== 'pending') shownStep = id;
	}
</script>

{#snippet chat(withHeader: boolean)}
	<ChatPanel
		messages={view.messages}
		pending={session.pending}
		suggestions={EXAMPLE_PROMPTS}
		extractionAvailable={view.session.ai.extraction_available}
		onsend={sendMessage}
		onretry={() => void session.retry()}
	>
		{#snippet header()}
			{#if withHeader}
				<div class="flex items-center justify-between border-b border-border px-4 py-2">
					<h2 class="text-heading text-ink">Dialog</h2>
					<IconButton
						label="Sbalit dialog"
						aria-expanded="true"
						onclick={() => (chatCollapsed = true)}
					>
						<PanelLeftClose size={16} strokeWidth={1.5} aria-hidden="true" />
					</IconButton>
				</div>
			{/if}
		{/snippet}
	</ChatPanel>
{/snippet}

<div class="flex h-dvh flex-col bg-page">
	<AppBar />
	<ProjectHeader
		name={view.project.name}
		{steps}
		onselectstep={selectStep}
		onopenchat={() => (chatSheetOpen = true)}
	/>

	<div class="flex min-h-0 flex-1">
		{#if wide.current}
			{#if chatCollapsed}
				<ChatRail onexpand={() => (chatCollapsed = false)} />
			{:else}
				<aside class="flex w-90 shrink-0 flex-col border-r border-border bg-surface">
					{@render chat(true)}
				</aside>
			{/if}
		{/if}

		<div class="flex min-w-0 flex-1 flex-col">
			<main class="min-h-0 flex-1 overflow-y-auto">
				<div class="mx-auto flex max-w-5xl flex-col gap-6 p-6">
					{#if session.problem === 'unreachable'}
						<Alert variant="danger" title="Server neodpovídá">
							Poslední akce se neprovedla. Zkontrolujte, že běží
							<code class="font-mono text-code">uv run decision-engine</code>.
							{#snippet actions()}
								<Button variant="secondary" onclick={() => void session.retry()}>
									Zkusit znovu
								</Button>
							{/snippet}
						</Alert>
					{/if}

					{#if step === 'input'}
						<InputStep
							capabilities={view.capabilities}
							extractionAvailable={view.session.ai.extraction_available}
							{busy}
							onsubmit={sendMessage}
						/>
					{:else if step === 'review' && view.proposal}
						<ReviewStep proposal={view.proposal} {busy} onsend={send} />
					{:else}
						<ResultStep
							result={view.result}
							{solving}
							proposalPending={view.proposal !== null}
							onsend={send}
							onreview={() => (shownStep = 'review')}
						/>
					{/if}
				</div>
			</main>
			{#if step === 'result' && view.result && !solving}
				<ResultSummaryBar
					result={view.result}
					proposalPending={view.proposal !== null}
					onsend={send}
					onreview={() => (shownStep = 'review')}
				/>
			{/if}
		</div>
	</div>
</div>

{#if !wide.current}
	<Sheet bind:open={chatSheetOpen} title="Dialog">
		{@render chat(false)}
	</Sheet>
{/if}
