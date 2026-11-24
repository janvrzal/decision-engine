<script lang="ts">
	import Alert from './ui/Alert.svelte';
	import Button from './ui/Button.svelte';
	import ConfirmDialog from './ui/ConfirmDialog.svelte';

	/**
	 * Dialog Zahodit rozpracovanou zakázku (UC-15, UC-06 A1): před novou nebo načtenou
	 * zakázkou nabídne uložení. Fokus začíná na bezpečné akci „Zrušit“.
	 */
	let {
		open = $bindable(false),
		name,
		hasProject,
		hasProposal,
		discardLabel,
		busy,
		error,
		onsave,
		ondiscard
	}: {
		open?: boolean;
		name: string;
		/** Je potvrzená zakázka, kterou jde uložit; jinak jde jen o rozpracovaný návrh. */
		hasProject: boolean;
		/** Čeká rozpracovaný návrh změny, který se do souboru neuloží. */
		hasProposal: boolean;
		/** „Zahodit zakázku“, u načtení „Zahodit a načíst“. */
		discardLabel: string;
		busy: boolean;
		/** Proč se uložení nepovedlo; okno zůstává otevřené. */
		error: string | null;
		onsave: () => void;
		ondiscard: () => void;
	} = $props();

	let description = $derived(
		[
			`Zakázka „${name}“ má neuložené změny.`,
			!hasProject
				? 'Rozpracovaný návrh nejde uložit, dokud ho nepotvrdíte.'
				: hasProposal
					? 'Uloží se potvrzená verze; rozpracovaný návrh v souboru nebude.'
					: ''
		]
			.filter(Boolean)
			.join(' ')
	);
	let saveReason = $derived(
		busy
			? 'Ukládám…'
			: hasProject
				? undefined
				: 'Uložit půjde až potvrzenou zakázku. Nejdřív potvrďte údaje.'
	);
</script>

<ConfirmDialog
	bind:open
	title="Zahodit rozpracovanou zakázku?"
	{description}
	initialFocus="[data-cancel]"
>
	{#if error}
		<Alert variant="danger" title="Zakázka se neuložila">{error}</Alert>
	{/if}

	{#snippet footer()}
		<!-- Destruktivní akce vlevo, daleko od „Uložit a pokračovat“ (komponenty.md). -->
		<div class="mr-auto">
			<Button
				variant="danger"
				disabledReason={busy ? 'Počkejte na dokončení.' : undefined}
				onclick={ondiscard}
			>
				{discardLabel}
			</Button>
		</div>
		<Button variant="ghost" data-cancel onclick={() => (open = false)}>Zrušit</Button>
		<Button variant="primary" disabledReason={saveReason} onclick={onsave}>
			Uložit a pokračovat
		</Button>
	{/snippet}
</ConfirmDialog>
