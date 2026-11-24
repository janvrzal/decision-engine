<script lang="ts">
	import PanelLeftClose from '@lucide/svelte/icons/panel-left-close';
	import { MediaQuery } from 'svelte/reactivity';
	import type { StepView, UserEvent, ViewModel } from '#lib/api/types.js';
	import { EXAMPLE_PROMPTS } from '#lib/examples.js';
	import { api } from '#lib/api/client.js';
	import { saveProject } from '#lib/download.js';
	import type { Session } from '#lib/session.svelte.js';
	import AppBar from './AppBar.svelte';
	import ChatPanel from './ChatPanel.svelte';
	import ChatRail from './ChatRail.svelte';
	import DiscardProjectDialog from './DiscardProjectDialog.svelte';
	import { DiscardGuard } from '#lib/behaviors/discard-guard.svelte.js';
	import InputStep from './InputStep.svelte';
	import ImportDialog from './ImportDialog.svelte';
	import ProjectHeader from './ProjectHeader.svelte';
	import ResultStep from './result/ResultStep.svelte';
	import ResultSummaryBar from './result/ResultSummaryBar.svelte';
	import ReviewStep from './review/ReviewStep.svelte';
	import Alert from './ui/Alert.svelte';
	import Button from './ui/Button.svelte';
	import EmptyState from './ui/EmptyState.svelte';
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
	// Když backend posune krok (nový návrh, výsledek), zobrazí se nový krok. Nový view model
	// se stejným krokem (odpověď na úpravu buňky) volbu uživatele nepřepíše.
	let backendStep: StepView['id'] | null = null;
	$effect(() => {
		const current = view.project.step;
		if (current !== backendStep) {
			backendStep = current;
			shownStep = null;
		}
	});

	let solving = $derived(session.pending?.kind === 'solving');
	let step = $derived(solving ? 'result' : (shownStep ?? view.project.step));
	let busy = $derived(session.pending !== null);
	// Zobrazený krok je aktivní; neaktuální krok si svůj stav ponechá a aktivní je jen
	// přes `current` (aria-current), aby stav „neaktuální“ nezmizel.
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

	/** Ruční postup bez AI: nová zakázka tabulkou, úprava potvrzené, nebo otevřený návrh. */
	function manualEntry(capability: string = 'cutting_1d') {
		chatSheetOpen = false;
		if (view.proposal) shownStep = 'review';
		else if (view.project.can_edit) send({ type: 'EditRequested' });
		else if (view.project.revision === null && capability === 'cutting_1d')
			send({ type: 'ToolSelected', capability });
	}

	let importOpen = $state(false);
	let checkError = $state<string | null>(null);
	let saveError = $state<string | null>(null);
	let saveReason = $derived(view.project.can_save ? undefined : 'Uložit jde potvrzená zakázka.');
	let newReason = $derived(view.project.can_start_new ? undefined : 'Počkejte na dokončení.');

	/** Uloží zakázku a dá backendu vědět, kterou revizi si uživatel stáhl. */
	async function saveFile(): Promise<string | null> {
		const result = await saveProject(api, view.session.id);
		if (!result.ok) return result.message;
		if (result.revision !== null)
			await session.send({ type: 'ProjectSaved', revision: result.revision });
		return null;
	}

	async function save() {
		saveError = await saveFile();
	}

	// Dialog Zahodit rozpracovanou zakázku (UC-15): akce čeká, než uživatel rozhodne.
	const guard = new DiscardGuard(() => session.view?.project.unsaved_changes ?? false, saveFile);

	function newProject() {
		chatSheetOpen = false;
		void guard.request({
			label: 'Zahodit zakázku',
			run: async (discardUnsaved) => {
				saveError = null;
				await session.send({ type: 'NewProjectRequested', discard_unsaved: discardUnsaved });
				const fresh = session.view;
				return fresh !== null && fresh.project.revision === null && fresh.proposal === null;
			}
		});
	}

	function openImport() {
		chatSheetOpen = false;
		checkError = null;
		importErrorOnOpen = false;
		importOpen = true;
	}

	let importErrorOnOpen = $state(false);

	/** Platnost souboru se ověří dřív, než se nabídne zahození rozpracované zakázky (F4). */
	async function importFile(content: string) {
		checkError = null;
		if (view.project.unsaved_changes) {
			try {
				const { data } = await api.POST('/api/project-files/check', { body: { content } });
				if (!data) throw new Error('bez dat');
				if (!data.ok) {
					checkError = data.message ?? 'Soubor se nepodařilo načíst.';
					return;
				}
			} catch {
				checkError = 'Server neodpovídá, soubor se nenačetl.';
				return;
			}
			importOpen = false;
		}
		await guard.request({
			label: 'Zahodit a načíst',
			run: async (discardUnsaved) => {
				const before = session.view?.messages.length ?? 0;
				await session.send({ type: 'ProjectImported', content, discard_unsaved: discardUnsaved });
				if (session.view?.import_error) {
					// Soubor backend odmítl: chyba se ukáže v okně.
					importErrorOnOpen = true;
					importOpen = true;
					return true;
				}
				// Načtení přidá do dialogu zprávu „Zakázka načtena…“; jinak se neprovedlo.
				const applied = (session.view?.messages.length ?? 0) > before;
				if (applied) importOpen = false;
				return applied;
			}
		});
		// Načtení čeká na rozhodnutí v dialogu Zahodit: okno s výběrem souboru se zavře.
		if (guard.open) importOpen = false;
	}

	let editReason = $derived(view.project.can_edit ? undefined : 'Počkejte na dokončení výpočtu.');

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
		onmanual={() => manualEntry()}
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
		currentStep={step}
		onselectstep={selectStep}
		onopenchat={() => (chatSheetOpen = true)}
		saveDisabledReason={saveReason}
		saveNote={view.project.save_note}
		unsaved={view.project.unsaved_badge}
		newDisabledReason={newReason}
		onsave={() => void save()}
		onload={openImport}
		onnew={newProject}
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
					{#if saveError}
						<Alert variant="danger" title="Zakázka se neuložila">
							{saveError}
							{#snippet actions()}
								<Button variant="secondary" onclick={() => void save()}>Zkusit znovu</Button>
							{/snippet}
						</Alert>
					{/if}
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
					{#if session.problem === 'rejected'}
						<Alert variant="danger" title="Akce se neprovedla">
							Server poslední akci odmítl, údaje se nezměnily. Obnovte stránku a zkuste to znovu.
							{#snippet actions()}
								<Button variant="secondary" onclick={() => location.reload()}>
									Obnovit stránku
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
							onmanual={manualEntry}
							onload={openImport}
						/>
					{:else if step === 'review' && view.proposal}
						<ReviewStep proposal={view.proposal} {busy} onsend={send} />
					{:else if step === 'review'}
						<section class="rounded-lg border border-border bg-surface" aria-label="Kontrola údajů">
							<EmptyState title="Údaje jsou potvrzené">
								Plán je spočítaný z potvrzené verze zakázky. Údaje můžete upravit v tabulce, nebo
								změnu napsat do dialogu.
								{#snippet action()}
									<Button
										variant="primary"
										disabledReason={editReason}
										onclick={() => send({ type: 'EditRequested' })}
									>
										Upravit údaje
									</Button>
								{/snippet}
							</EmptyState>
						</section>
					{:else}
						<ResultStep
							result={view.result}
							{solving}
							{editReason}
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
					onsave={() => void save()}
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

<ImportDialog
	bind:open={importOpen}
	busy={session.pending !== null}
	error={checkError ?? view.import_error}
	errorOnOpen={importErrorOnOpen}
	onimport={importFile}
/>

<DiscardProjectDialog
	bind:open={guard.open}
	name={view.project.name}
	hasProject={view.project.can_save}
	hasProposal={view.proposal !== null}
	discardLabel={guard.action?.label ?? 'Zahodit zakázku'}
	busy={guard.busy}
	error={guard.error}
	onsave={() => void guard.proceed(true)}
	ondiscard={() => void guard.proceed(false)}
/>
