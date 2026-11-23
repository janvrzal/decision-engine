<script lang="ts">
	import '@fontsource/ibm-plex-sans/400.css';
	import '@fontsource/ibm-plex-sans/500.css';
	import '@fontsource/ibm-plex-sans/600.css';
	import '@fontsource/ibm-plex-mono/400.css';
	import '../app.css';
	import ServerCrash from '@lucide/svelte/icons/server-crash';
	import favicon from '#lib/assets/favicon.svg';
	import { api } from '#lib/api/client.js';
	import Button from '#lib/components/ui/Button.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import type { LayoutProps } from './$types';

	let { children }: LayoutProps = $props();

	// Celostránkový stav „Backend nedostupný“ (mapa obrazovek); obsah se mezitím vykresluje.
	let backendDown = $state(false);
	let retrying = $state(false);

	async function checkBackend() {
		try {
			const { data } = await api.GET('/api/health');
			backendDown = data === undefined;
		} catch {
			backendDown = true;
		}
	}

	async function retry() {
		retrying = true;
		await checkBackend();
		retrying = false;
	}

	$effect(() => {
		void checkBackend();
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{#if backendDown}
	<main class="flex min-h-dvh items-center justify-center bg-page p-4">
		<div class="rounded-lg border border-border bg-surface shadow-raised">
			<EmptyState title="Aplikace se nemůže spojit se svým serverem" variant="page">
				{#snippet icon()}
					<ServerCrash size={32} strokeWidth={1.5} />
				{/snippet}
				Spusťte v terminálu
				<code class="font-mono text-code text-ink">uv run decision-engine</code>
				a zkuste to znovu.
				{#snippet action()}
					<Button
						variant="primary"
						onclick={retry}
						disabledReason={retrying ? 'Ověřuji spojení…' : undefined}
					>
						Zkusit znovu
					</Button>
				{/snippet}
			</EmptyState>
		</div>
	</main>
{:else}
	{@render children()}
{/if}
