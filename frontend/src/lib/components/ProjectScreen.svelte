<script lang="ts">
	import PanelLeftClose from '@lucide/svelte/icons/panel-left-close';
	import { MediaQuery } from 'svelte/reactivity';
	import AppBar from './AppBar.svelte';
	import ChatPanel from './ChatPanel.svelte';
	import ChatRail from './ChatRail.svelte';
	import InputStep from './InputStep.svelte';
	import ProjectHeader from './ProjectHeader.svelte';
	import IconButton from './ui/IconButton.svelte';
	import Sheet from './ui/Sheet.svelte';
	import { NOT_CONNECTED_REASON, type ProjectView } from '#lib/fixtures/empty-project.js';

	/**
	 * Pracovní obrazovka zakázky. Od 1280 px Panel Dialog vlevo vedle Pracovní plochy
	 * (sbalitelný), 768–1279 px Dialog jako vysouvací panel zleva (mapa obrazovek).
	 */
	let { project }: { project: ProjectView } = $props();

	const wide = new MediaQuery('min-width: 1280px');
	let chatCollapsed = $state(false);
	let chatSheetOpen = $state(false);

	// Při rozšíření okna se vysouvací panel zavře, Dialog je pak vidět v rozvržení.
	$effect(() => {
		if (wide.current) chatSheetOpen = false;
	});
</script>

<div class="flex h-dvh flex-col bg-page">
	<AppBar />
	<ProjectHeader {project} canSave={false} onopenchat={() => (chatSheetOpen = true)} />

	<div class="flex min-h-0 flex-1">
		{#if wide.current}
			{#if chatCollapsed}
				<ChatRail onexpand={() => (chatCollapsed = false)} />
			{:else}
				<aside class="flex w-90 shrink-0 flex-col border-r border-border bg-surface">
					<ChatPanel suggestions={project.examplePrompts} sendDisabledReason={NOT_CONNECTED_REASON}>
						{#snippet header()}
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
						{/snippet}
					</ChatPanel>
				</aside>
			{/if}
		{/if}

		<main class="min-w-0 flex-1 overflow-y-auto">
			<div class="mx-auto flex max-w-4xl flex-col gap-6 p-6">
				<InputStep {project} />
			</div>
		</main>
	</div>
</div>

{#if !wide.current}
	<Sheet bind:open={chatSheetOpen} title="Dialog">
		<ChatPanel suggestions={project.examplePrompts} sendDisabledReason={NOT_CONNECTED_REASON} />
	</Sheet>
{/if}
