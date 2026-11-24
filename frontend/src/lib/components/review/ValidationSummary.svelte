<script lang="ts">
	import type { FieldErrorView } from '#lib/api/types.js';
	import { focusField } from '#lib/behaviors/field-focus.js';
	import Alert from '../ui/Alert.svelte';

	/**
	 * Souhrn chyb nad kontrolní tabulkou (komponenty.md, ValidationSummary): každá chyba
	 * je odkaz, který přesune fokus na pole. Chyba bez pole ve formuláři zůstane textem.
	 */
	let {
		title,
		errors,
		scope = null
	}: { title: string; errors: FieldErrorView[]; scope?: ParentNode | null } = $props();

	function jump(event: MouseEvent, target: string) {
		if (focusField(scope ?? document, target)) event.preventDefault();
	}
</script>

<Alert variant="danger" {title}>
	<ul class="list-disc pl-4">
		{#each errors as error (`${error.field}:${error.message}`)}
			<li>
				{#if error.target}
					<a
						href="#{error.target}"
						class="rounded-sm underline underline-offset-2 hover:text-danger"
						onclick={(event) => jump(event, error.target as string)}
					>
						{error.field}: {error.message}
					</a>
				{:else}
					{error.field}: {error.message}
				{/if}
			</li>
		{/each}
	</ul>
</Alert>
