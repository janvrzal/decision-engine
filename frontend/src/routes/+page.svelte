<script lang="ts">
	import { api } from '#lib/api/client.js';

	// Dočasná stránka kostry (#3): ověřuje spojení s API. Obrazovku zakázky přinese #4.
	type Connection = { state: 'loading' } | { state: 'ok'; version: string } | { state: 'error' };

	let connection = $state<Connection>({ state: 'loading' });

	async function checkConnection() {
		connection = { state: 'loading' };
		try {
			const { data } = await api.GET('/api/health');
			connection = data ? { state: 'ok', version: data.version } : { state: 'error' };
		} catch {
			connection = { state: 'error' };
		}
	}

	$effect(() => {
		void checkConnection();
	});
</script>

<main class="mx-auto max-w-xl p-8">
	<h1 class="text-2xl font-semibold">DecisionEngine</h1>
	<p class="mt-2">Ze zadání k nářezovému plánu a ceně zakázky.</p>

	<p class="mt-6" role="status" aria-live="polite">
		{#if connection.state === 'loading'}
			Ověřuji spojení se serverem…
		{:else if connection.state === 'ok'}
			Spojení se serverem funguje (verze {connection.version}).
		{:else}
			Server neodpovídá. Spusťte <code>uv run decision-engine</code> a
			<button type="button" class="underline" onclick={checkConnection}>zkuste to znovu</button>.
		{/if}
	</p>
</main>
