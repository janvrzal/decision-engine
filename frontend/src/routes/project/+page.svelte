<script lang="ts">
	import ServerCrash from '@lucide/svelte/icons/server-crash';
	import ProjectScreen from '#lib/components/ProjectScreen.svelte';
	import Button from '#lib/components/ui/Button.svelte';
	import EmptyState from '#lib/components/ui/EmptyState.svelte';
	import Loader from '#lib/components/ui/Loader.svelte';
	import { Session } from '#lib/session.svelte.js';

	const session = new Session();

	$effect(() => {
		void session.start();
	});
</script>

<svelte:head>
	<title>{session.view?.project.name ?? 'Zakázka'} · DecisionEngine</title>
</svelte:head>

{#if session.problem === 'session_lost'}
	<main class="flex min-h-dvh items-center justify-center bg-page p-4">
		<div class="rounded-lg border border-border bg-surface shadow-raised">
			<EmptyState title="Rozpracovaná zakázka se ztratila" variant="page">
				{#snippet icon()}
					<ServerCrash size={32} strokeWidth={1.5} />
				{/snippet}
				Server byl restartován a rozpracovaná zakázka zůstala jen v jeho paměti. Ukládání zakázek přijde
				v další verzi.
				{#snippet action()}
					<Button variant="primary" onclick={() => void session.restart()}>Začít znovu</Button>
				{/snippet}
			</EmptyState>
		</div>
	</main>
{:else if session.view}
	<ProjectScreen {session} view={session.view} />
{:else}
	<main class="flex min-h-dvh items-center justify-center bg-page p-4">
		<Loader size="large" label="Připravuji zakázku…" />
	</main>
{/if}
