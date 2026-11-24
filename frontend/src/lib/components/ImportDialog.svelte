<script lang="ts">
	import FileUp from '@lucide/svelte/icons/file-up';
	import Alert from './ui/Alert.svelte';
	import Button from './ui/Button.svelte';
	import Modal from './ui/Modal.svelte';

	/**
	 * Okno Načíst zakázku (UC-06): výběr souboru nebo přetažení. Soubor se jen přečte
	 * a pošle backendu; zda je platný, rozhodne jádro a chybu vrátí ve view modelu.
	 */
	let {
		open = $bindable(false),
		hasContent,
		busy,
		error,
		onimport
	}: {
		open?: boolean;
		/** Rozpracovaná zakázka bude nahrazena; okno na to upozorní. */
		hasContent: boolean;
		busy: boolean;
		/** Chyba načtení z backendu (`import_error`). */
		error: string | null;
		onimport: (content: string) => Promise<void>;
	} = $props();

	const MAX_BYTES = 1_000_000;

	let input = $state<HTMLInputElement | null>(null);
	let dragging = $state(false);
	let localError = $state<string | null>(null);
	let attempted = $state(false);
	let fileName = $state('');

	// Každé otevření začíná bez staré chyby.
	$effect(() => {
		if (open) {
			attempted = false;
			localError = null;
			fileName = '';
		}
	});

	let shownError = $derived(localError ?? (attempted ? error : null));

	async function load(file: File | undefined) {
		if (!file || busy) return;
		fileName = file.name;
		localError = null;
		if (file.size > MAX_BYTES) {
			localError = 'Soubor je příliš velký (nejvýš 1 MB). Zakázka to nebude.';
			return;
		}
		let content: string;
		try {
			content = await file.text();
		} catch {
			localError = 'Soubor se nepodařilo přečíst.';
			return;
		}
		attempted = true;
		await onimport(content);
	}

	function drop(event: DragEvent) {
		event.preventDefault();
		dragging = false;
		void load(event.dataTransfer?.files[0]);
	}
</script>

<Modal
	bind:open
	title="Načíst zakázku"
	description="Soubor .decision.json uložený z DecisionEngine."
>
	{#if hasContent}
		<Alert variant="warning" title="Aktuální zakázka bude nahrazena">
			Pokud ji chcete zachovat, nejdřív ji uložte.
		</Alert>
	{/if}

	<div
		role="group"
		aria-label="Soubor zakázky"
		class="flex flex-col items-center gap-3 rounded-md border border-dashed px-4 py-8 text-center transition-colors duration-(--duration-fast) ease-standard {dragging
			? 'border-ink bg-surface-sunken'
			: 'border-border-strong'}"
		ondragover={(event) => {
			event.preventDefault();
			dragging = true;
		}}
		ondragleave={() => (dragging = false)}
		ondrop={drop}
	>
		<FileUp size={24} strokeWidth={1.5} class="text-ink-muted" aria-hidden="true" />
		<p class="text-body text-ink">Přetáhněte soubor sem, nebo</p>
		<Button
			variant="secondary"
			disabledReason={busy ? 'Načítám…' : undefined}
			onclick={() => input?.click()}
		>
			Vybrat soubor
		</Button>
		<input
			bind:this={input}
			type="file"
			accept=".json,application/json"
			class="sr-only"
			tabindex="-1"
			aria-label="Soubor zakázky"
			onchange={(event) => {
				const file = event.currentTarget.files?.[0];
				// Stejný soubor jde vybrat znovu (např. po opravě).
				event.currentTarget.value = '';
				void load(file);
			}}
		/>
		{#if fileName}
			<p class="text-small text-ink-muted">{fileName}</p>
		{/if}
	</div>

	{#if shownError}
		<Alert variant="danger" title="Soubor se nenačetl">
			{shownError} Aktuální zakázka zůstala beze změny.
		</Alert>
	{/if}
</Modal>
