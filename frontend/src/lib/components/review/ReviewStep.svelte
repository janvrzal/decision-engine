<script lang="ts">
	import Calculator from '@lucide/svelte/icons/calculator';
	import { untrack } from 'svelte';
	import type {
		IntCell,
		MoneyCell,
		Objective,
		ProposalView,
		TextCell,
		UserEvent
	} from '#lib/api/types.js';
	import {
		draftToEvent,
		mergeDraft,
		nextRowId,
		type CellKey,
		type ParameterKey,
		type ProposalDraft
	} from '#lib/proposal-draft.js';
	import Alert from '../ui/Alert.svelte';
	import Button from '../ui/Button.svelte';
	import Collapsible from '../ui/Collapsible.svelte';
	import RadioCardGroup from '../ui/RadioCardGroup.svelte';
	import CellInput from './CellInput.svelte';
	import EditableGrid from './EditableGrid.svelte';
	import type { CellState } from './grid-types.js';

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

	// Nový návrh od backendu (odpověď na úpravu nebo zprávu) přepíše koncept.
	$effect(() => {
		const incoming = proposal;
		untrack(() => {
			draft = mergeDraft(incoming, $state.snapshot(draft));
			localErrors = {};
		});
	});

	function commit() {
		const result = draftToEvent($state.snapshot(draft));
		if (!result.ok) {
			localErrors = result.errors;
			return;
		}
		localErrors = {};
		const serialized = JSON.stringify(result.event);
		if (serialized === lastSent || busy) return;
		lastSent = serialized;
		onsend(result.event);
	}

	function cellState(cell: IntCell | MoneyCell | TextCell | undefined, key: CellKey): CellState {
		return {
			unconfirmed: cell?.unconfirmed ?? false,
			error: localErrors[key] ?? cell?.error ?? null
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

<section class="flex flex-col gap-6" aria-labelledby="review-title">
	<div class="flex flex-col gap-1">
		<h2 id="review-title" class="text-title text-ink">Kontrola údajů</h2>
		<p class="text-body text-ink-muted">
			Zkontrolujte, co jsem ze zadání vyčetl. Hodnoty s otazníkem jsou výchozí nebo odhad AI —
			potvrdíte je spolu s celým návrhem.
		</p>
	</div>

	{#if proposal.is_change}
		<Alert variant="info" title="Úprava zakázky">
			Změny se projeví až po potvrzení. Do té doby platí původní plán.
		</Alert>
	{/if}

	{#if proposal.errors.length > 0}
		<Alert variant="danger" title={proposal.confirm_disabled_reason ?? 'Opravte chyby'}>
			<ul class="list-disc pl-4">
				{#each proposal.errors as error (`${error.field}:${error.message}`)}
					<li>{error.field}: {error.message}</li>
				{/each}
			</ul>
		</Alert>
	{/if}

	<div class="grid gap-4 md:grid-cols-2">
		<label class="flex flex-col gap-1">
			<span class="text-small font-medium text-ink">Název zakázky</span>
			<CellInput
				bind:value={draft.name}
				label="Název zakázky"
				{...cellState(proposal.name, 'name')}
				oncommit={commit}
			/>
		</label>
		<label class="flex flex-col gap-1">
			<span class="text-small font-medium text-ink">Materiál (nepovinné)</span>
			<CellInput
				bind:value={draft.material}
				label="Materiál"
				placeholder="např. jekl 40×40×2"
				oncommit={commit}
			/>
		</label>
	</div>

	<EditableGrid
		caption="Díly"
		bind:rows={draft.parts}
		columns={[
			{ key: 'name', label: 'Název', placeholder: 'např. sloupek' },
			{ key: 'length_mm', label: 'Délka', unit: 'mm', numeric: true },
			{ key: 'quantity', label: 'Počet', unit: 'ks', numeric: true }
		]}
		cell={(r: number, key: string) =>
			cellState(proposal.parts[r]?.[key as 'name' | 'length_mm' | 'quantity'], `parts.${r}.${key}`)}
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
		bind:rows={draft.stock}
		columns={[
			{ key: 'length_mm', label: 'Délka tyče', unit: 'mm', numeric: true },
			{ key: 'price', label: 'Cena za kus', unit: 'Kč', numeric: true, placeholder: 'chybí cena' }
		]}
		cell={(r: number, key: string) =>
			cellState(proposal.stock[r]?.[key as 'length_mm' | 'price'], `stock.${r}.${key}`)}
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
						unit={parameter.unit}
						numeric
						{...cellState(proposal.parameters[parameter.key], `parameters.${parameter.key}`)}
						oncommit={commit}
					/>
				</label>
			{/each}
		</div>
		<Collapsible label="Další nastavení">
			<label class="flex max-w-60 flex-col gap-1">
				<span class="text-small font-medium text-ink">Časový limit výpočtu</span>
				<CellInput
					bind:value={draft.time_limit_s}
					label="Časový limit výpočtu"
					unit="s"
					numeric
					{...cellState(proposal.parameters.time_limit_s, 'parameters.time_limit_s')}
					oncommit={commit}
				/>
			</label>
		</Collapsible>
	</div>

	<div class="flex flex-col gap-3">
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
			onclick={() => onsend({ type: 'ProposalConfirmed' })}
			disabledReason={confirmReason}
		>
			<Calculator size={16} strokeWidth={1.5} aria-hidden="true" />
			Potvrdit a vypočítat
		</Button>
	</div>
</section>
