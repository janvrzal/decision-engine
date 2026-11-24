<script lang="ts">
	import Calculator from '@lucide/svelte/icons/calculator';
	import { untrack } from 'svelte';
	import type {
		IntCell,
		MoneyCell,
		Objective,
		ProposalView,
		RemovedPartView,
		RemovedStockView,
		TextCell,
		UserEvent
	} from '#lib/api/types.js';
	import {
		draftToEvent,
		keepEditsSince,
		mergeDraft,
		nextRowId,
		normalizeDraft,
		type CellKey,
		type ParameterKey,
		type ProposalDraft
	} from '#lib/proposal-draft.js';
	import Button from '../ui/Button.svelte';
	import Collapsible from '../ui/Collapsible.svelte';
	import RadioCardGroup from '../ui/RadioCardGroup.svelte';
	import { integerText, moneyText } from '#lib/behaviors/number-input.js';
	import CellInput from './CellInput.svelte';
	import ChangeSummary from './ChangeSummary.svelte';
	import EditableGrid from './EditableGrid.svelte';
	import type { CellState } from './grid-types.js';
	import ValidationSummary from './ValidationSummary.svelte';

	/**
	 * Krok Kontrola údajů (mapa obrazovek): tabulky dílů a skladových délek, parametry
	 * a cíl. Každá potvrzená buňka pošle `ProposalEdited`; platnost posuzuje backend.
	 */
	let {
		proposal,
		busy,
		onsend
	}: { proposal: ProposalView; busy: boolean; onsend: (event: UserEvent) => void } = $props();

	let draft = $state<ProposalDraft>(untrack(() => mergeDraft(proposal, null)));
	let localErrors = $state<Record<CellKey, string>>({});
	let lastSent = '';
	/** Koncept v okamžiku posledního odeslání; co se od té doby změnilo, odpověď nepřepíše. */
	let sentDraft: ProposalDraft | null = null;
	let section = $state<HTMLElement | null>(null);
	let isNewManual = $derived(proposal.origin === 'manual' && !proposal.is_change);
	// Prázdný ruční formulář nekřičí chybami hned; souhrn se ukáže po první úpravě.
	let touched = $state(false);
	/** Oznámení převodu jednotek („1,5 m = 1 500 mm“), viditelné i pro čtečky. */
	let conversion = $state('');
	let showErrors = $derived(proposal.errors.length > 0 && (!isNewManual || touched));

	// Chybné pole v „Dalším nastavení“ nesmí zůstat schované (odkaz ze souhrnu chyb na něj vede).
	let moreOpen = $state(false);
	$effect(() => {
		if (showErrors && proposal.parameters.time_limit_s.error) moreOpen = true;
	});

	// Ruční zadání začíná fokusem v prvním řádku dílů (UC-13 krok 2).
	$effect(() => {
		if (!section || !untrack(() => isNewManual)) return;
		section.querySelector<HTMLInputElement>('table input')?.focus();
	});

	// Nový návrh od backendu (odpověď na úpravu nebo zprávu) přepíše koncept.
	$effect(() => {
		const incoming = proposal;
		untrack(() => {
			const current = $state.snapshot(draft);
			const next = mergeDraft(incoming, current);
			draft = sentDraft ? keepEditsSince(next, current, sentDraft) : next;
			localErrors = {};
		});
	});

	/** Buňky, do kterých uživatel od posledního odeslání psal: potvrdí je i beze změny (R6). */
	let typed: string[] = [];

	function markTyped(key: string) {
		if (!typed.includes(key)) typed.push(key);
	}

	function trackTyping(event: Event) {
		if (!(event.target instanceof Node) || !section?.contains(event.target)) return;
		const key = (event.target as HTMLElement | null)
			?.closest('[data-cell]')
			?.getAttribute('data-cell');
		if (key) markTyped(key);
	}

	function commit() {
		touched = true;
		// Potvrzená buňka se ukáže ve formátu cs-CZ (`12 500`); během psaní se text nemění.
		const raw = $state.snapshot(draft);
		const result = draftToEvent(raw);
		const snapshot = normalizeDraft(raw);
		draft = structuredClone(snapshot);
		if (!result.ok) {
			localErrors = result.errors;
			return;
		}
		localErrors = {};
		if (result.conversions.length > 0) conversion = `Převedeno: ${result.conversions.join(', ')}.`;
		// Stejný obsah se znovu neposílá, ledaže uživatel do buňky psal (potvrzení hodnoty).
		const content = JSON.stringify(result.event);
		if ((content === lastSent && typed.length === 0) || busy) return;
		const event = { ...result.event, confirmed: [...typed] };
		lastSent = content;
		sentDraft = snapshot;
		typed = [];
		onsend(event);
	}

	/** Vrátí řádek, který návrh odebral (ChangeSummary „Vrátit“). */
	function restorePart(row: RemovedPartView) {
		draft.parts.push({
			id: row.id,
			name: row.name,
			length_mm: integerText(row.length_mm),
			quantity: integerText(row.quantity)
		});
		commit();
	}

	function restoreStock(row: RemovedStockView) {
		draft.stock.push({
			id: row.id,
			length_mm: integerText(row.length_mm),
			price: moneyText(row.price)
		});
		commit();
	}

	function confirm() {
		onsend({ type: 'ProposalConfirmed' });
	}

	/** Ctrl/Cmd+Enter odešle rozepsanou buňku a spustí výpočet (zkušený uživatel). */
	function shortcut(event: KeyboardEvent) {
		if (event.key !== 'Enter' || !(event.ctrlKey || event.metaKey)) return;
		event.preventDefault();
		commit();
		if (!busy) confirm();
	}

	function cellState(cell: IntCell | MoneyCell | TextCell | undefined, key: CellKey): CellState {
		return {
			unconfirmed: cell?.unconfirmed ?? false,
			error: localErrors[key] ?? (isNewManual && !touched ? null : (cell?.error ?? null)),
			previous: cell?.previous ?? null
		};
	}

	const PARAMETERS: { key: ParameterKey; label: string; unit: string }[] = [
		{ key: 'kerf_mm', label: 'Prořez', unit: 'mm' },
		{ key: 'trim_mm', label: 'Zarovnávací ořez', unit: 'mm' },
		{ key: 'min_remnant_mm', label: 'Minimální využitelný zbytek', unit: 'mm' }
	];

	let confirmReason = $derived(
		busy ? 'Počkejte na dokončení.' : (proposal.confirm_disabled_reason ?? undefined)
	);
</script>

<svelte:window oninput={trackTyping} onkeydown={shortcut} />

<section bind:this={section} class="flex flex-col gap-6" aria-labelledby="review-title">
	<div class="flex flex-col gap-1">
		<h2 id="review-title" class="text-title text-ink">Kontrola údajů</h2>
		<p class="text-body text-ink-muted">
			{#if proposal.origin === 'ai'}
				Zkontrolujte, co jsem ze zadání vyčetl. Hodnoty s otazníkem jsou výchozí nebo odhad AI —
				potvrdíte je spolu s celým návrhem.
			{:else if proposal.origin === 'file'}
				Zkontrolujte údaje načtené ze souboru a spusťte výpočet.
			{:else if proposal.is_change}
				Upravte údaje potvrzené zakázky v tabulkách nebo změnu napište do dialogu.
			{:else}
				Vyplňte díly, skladové délky a parametry. Délky můžete psát i v cm nebo m (1,5 m). Hodnoty s
				otazníkem jsou výchozí — potvrdíte je spolu s celou zakázkou.
			{/if}
		</p>
	</div>

	{#if proposal.changes}
		<ChangeSummary
			changes={proposal.changes}
			{busy}
			onrestorepart={restorePart}
			onrestorestock={restoreStock}
		/>
	{/if}

	{#if showErrors}
		<ValidationSummary
			title={proposal.confirm_disabled_reason ?? 'Opravte chyby'}
			errors={proposal.errors}
			scope={section}
		/>
	{/if}

	<p role="status" class="text-small text-ink-muted" class:sr-only={!conversion}>{conversion}</p>

	<div class="grid gap-4 md:grid-cols-2">
		<label class="flex flex-col gap-1">
			<span class="text-small font-medium text-ink">Název zakázky</span>
			<CellInput
				bind:value={draft.name}
				label="Název zakázky"
				data-cell="name"
				{...cellState(proposal.name, 'name')}
				oncommit={commit}
			/>
		</label>
		<label class="flex flex-col gap-1">
			<span class="text-small font-medium text-ink">Materiál (nepovinné)</span>
			<CellInput
				bind:value={draft.material}
				label="Materiál"
				data-cell="material"
				previous={proposal.material.previous ?? null}
				placeholder="např. jekl 40×40×2"
				oncommit={commit}
			/>
		</label>
	</div>

	<EditableGrid
		caption="Díly"
		name="parts"
		bind:rows={draft.parts}
		columns={[
			{ key: 'name', label: 'Název', placeholder: 'např. sloupek' },
			{ key: 'length_mm', label: 'Délka', unit: 'mm', numeric: true },
			{ key: 'quantity', label: 'Počet', unit: 'ks', numeric: true }
		]}
		cell={(r: number, key: string) =>
			cellState(proposal.parts[r]?.[key as 'name' | 'length_mm' | 'quantity'], `parts.${r}.${key}`)}
		added={(r: number) => proposal.parts[r]?.added ?? false}
		rowLabel={(r: number) => `Díl ${r + 1}`}
		addLabel="Přidat díl"
		disabled={busy}
		oncommit={commit}
		onadd={() =>
			draft.parts.push({ id: nextRowId('p', draft.parts), name: '', length_mm: '', quantity: '' })}
		onremove={(r: number) => {
			draft.parts.splice(r, 1);
			commit();
		}}
	/>

	<EditableGrid
		caption="Skladové délky"
		name="stock"
		bind:rows={draft.stock}
		columns={[
			{ key: 'length_mm', label: 'Délka tyče', unit: 'mm', numeric: true },
			{ key: 'price', label: 'Cena za kus', unit: 'Kč', numeric: true, placeholder: 'chybí cena' }
		]}
		cell={(r: number, key: string) =>
			cellState(proposal.stock[r]?.[key as 'length_mm' | 'price'], `stock.${r}.${key}`)}
		added={(r: number) => proposal.stock[r]?.added ?? false}
		rowLabel={(r: number) => `Skladová délka ${r + 1}`}
		addLabel="Přidat skladovou délku"
		disabled={busy}
		oncommit={commit}
		onadd={() => draft.stock.push({ id: nextRowId('s', draft.stock), length_mm: '', price: '' })}
		onremove={(r: number) => {
			draft.stock.splice(r, 1);
			commit();
		}}
	/>

	<div class="flex flex-col gap-3">
		<h3 class="text-heading text-ink">Parametry řezání</h3>
		<div class="grid gap-4 md:grid-cols-3">
			{#each PARAMETERS as parameter (parameter.key)}
				<label class="flex flex-col gap-1">
					<span class="text-small font-medium text-ink">{parameter.label}</span>
					<CellInput
						bind:value={draft[parameter.key]}
						label={parameter.label}
						data-cell="parameters.{parameter.key}"
						unit={parameter.unit}
						numeric
						{...cellState(proposal.parameters[parameter.key], `parameters.${parameter.key}`)}
						oncommit={commit}
					/>
				</label>
			{/each}
		</div>
		<Collapsible label="Další nastavení" bind:open={moreOpen}>
			<label class="flex max-w-60 flex-col gap-1">
				<span class="text-small font-medium text-ink">Časový limit výpočtu</span>
				<CellInput
					bind:value={draft.time_limit_s}
					label="Časový limit výpočtu"
					data-cell="parameters.time_limit_s"
					unit="s"
					numeric
					{...cellState(proposal.parameters.time_limit_s, 'parameters.time_limit_s')}
					oncommit={commit}
				/>
			</label>
		</Collapsible>
	</div>

	<div class="flex flex-col gap-3" data-cell="parameters.objective">
		<h3 class="text-heading text-ink">Cíl optimalizace</h3>
		<RadioCardGroup
			label="Cíl optimalizace"
			value={draft.objective}
			options={proposal.objective_options.map((option) => ({
				value: option.value,
				label: option.label,
				hint: option.hint,
				disabledReason: option.disabled_reason,
				note:
					proposal.objective_unconfirmed && option.value === proposal.objective
						? 'Výchozí volba, ověřte.'
						: null
			}))}
			onchange={(value: Objective) => {
				draft.objective = value;
				markTyped('objective');
				commit();
			}}
		/>
	</div>

	<div
		class="sticky bottom-0 flex flex-wrap items-center justify-end gap-2 border-t border-border bg-page py-4"
	>
		{#if proposal.is_change}
			<Button
				variant="ghost"
				onclick={() => onsend({ type: 'ProposalRejected' })}
				disabledReason={busy ? 'Počkejte na dokončení.' : undefined}
			>
				Zahodit změny
			</Button>
		{/if}
		<Button
			variant="primary"
			onclick={confirm}
			disabledReason={confirmReason}
			aria-keyshortcuts="Control+Enter Meta+Enter"
		>
			<Calculator size={16} strokeWidth={1.5} aria-hidden="true" />
			Potvrdit a vypočítat
		</Button>
	</div>
</section>
