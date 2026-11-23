<script lang="ts">
	import FilePlus from '@lucide/svelte/icons/file-plus';
	import FolderOpen from '@lucide/svelte/icons/folder-open';
	import MessageSquare from '@lucide/svelte/icons/message-square';
	import Save from '@lucide/svelte/icons/save';
	import StepIndicator from './StepIndicator.svelte';
	import Button from './ui/Button.svelte';
	import DropdownMenu, { type MenuItem } from './ui/DropdownMenu.svelte';
	import { NOT_CONNECTED_REASON, type ProjectView } from '#lib/fixtures/empty-project.js';

	/** Hlavička zakázky: název, ukazatel kroků a akce se zakázkou (mapa obrazovek). */
	let {
		project,
		canSave,
		onopenchat
	}: { project: ProjectView; canSave: boolean; onopenchat: () => void } = $props();

	// Na střední šířce jsou méně časté akce v menu „⋯“ (komponenty.md).
	const moreActions: MenuItem[] = [
		{ label: 'Načíst zakázku', icon: FolderOpen, disabledReason: NOT_CONNECTED_REASON },
		{ label: 'Nová zakázka', icon: FilePlus, disabledReason: NOT_CONNECTED_REASON }
	];
</script>

<div class="flex shrink-0 items-center gap-x-6 gap-y-2 border-b border-border bg-surface px-4 py-3">
	<div class="xl:hidden">
		<Button variant="secondary" onclick={onopenchat} aria-haspopup="dialog">
			<MessageSquare size={16} strokeWidth={1.5} aria-hidden="true" />
			Dialog
		</Button>
	</div>
	<h1 class="min-w-0 truncate text-title text-ink">{project.name}</h1>
	<div class="flex-1">
		<StepIndicator steps={project.steps} />
	</div>
	<div class="flex items-center gap-2">
		<Button variant="secondary" disabledReason={canSave ? undefined : 'Zatím není co uložit.'}>
			<Save size={16} strokeWidth={1.5} aria-hidden="true" />
			Uložit
		</Button>
		<div class="hidden items-center gap-2 xl:flex">
			<Button variant="ghost" disabledReason={NOT_CONNECTED_REASON}>
				<FolderOpen size={16} strokeWidth={1.5} aria-hidden="true" />
				Načíst
			</Button>
			<Button variant="ghost" disabledReason={NOT_CONNECTED_REASON}>
				<FilePlus size={16} strokeWidth={1.5} aria-hidden="true" />
				Nová zakázka
			</Button>
		</div>
		<div class="xl:hidden">
			<DropdownMenu label="Další akce se zakázkou" items={moreActions} />
		</div>
	</div>
</div>
