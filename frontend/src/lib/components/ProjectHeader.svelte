<script lang="ts">
	import FilePlus from '@lucide/svelte/icons/file-plus';
	import FolderOpen from '@lucide/svelte/icons/folder-open';
	import MessageSquare from '@lucide/svelte/icons/message-square';
	import CircleDot from '@lucide/svelte/icons/circle-dot';
	import Save from '@lucide/svelte/icons/save';
	import StepIndicator from './StepIndicator.svelte';
	import Badge from './ui/Badge.svelte';
	import Button from './ui/Button.svelte';
	import Tooltip from './ui/Tooltip.svelte';
	import DropdownMenu, { type MenuItem } from './ui/DropdownMenu.svelte';
	import type { StepView } from '#lib/api/types.js';

	/** Hlavička zakázky: název, ukazatel kroků a akce se zakázkou (mapa obrazovek). */
	let {
		name,
		steps,
		onselectstep,
		onopenchat,
		saveDisabledReason,
		saveNote,
		unsaved,
		newDisabledReason,
		onsave,
		onload,
		onnew
	}: {
		name: string;
		steps: StepView[];
		onselectstep: (id: StepView['id']) => void;
		onopenchat: () => void;
		/** Proč teď nejde uložit; `undefined` = jde. */
		saveDisabledReason: string | undefined;
		/** Upozornění k uložení (rozpracovaný návrh nebude v souboru). */
		saveNote: string | null;
		/** Zakázka má neuložené změny (štítek „neuloženo“). */
		unsaved: boolean;
		/** Proč teď nejde začít novou zakázku; `undefined` = jde. */
		newDisabledReason: string | undefined;
		onsave: () => void;
		onload: () => void;
		onnew: () => void;
	} = $props();

	// Na střední šířce jsou méně časté akce v menu „⋯“ (komponenty.md).
	let moreActions = $derived<MenuItem[]>([
		{ label: 'Načíst zakázku', icon: FolderOpen, onselect: onload },
		{ label: 'Nová zakázka', icon: FilePlus, disabledReason: newDisabledReason, onselect: onnew }
	]);
</script>

<div class="flex shrink-0 items-center gap-x-6 gap-y-2 border-b border-border bg-surface px-4 py-3">
	<div class="xl:hidden">
		<Button variant="secondary" onclick={onopenchat} aria-haspopup="dialog">
			<MessageSquare size={16} strokeWidth={1.5} aria-hidden="true" />
			Dialog
		</Button>
	</div>
	<div class="flex min-w-0 items-center gap-2">
		<h1 class="min-w-0 truncate text-title text-ink">{name}</h1>
		{#if unsaved}
			<Badge variant="warning" icon={CircleDot}>neuloženo</Badge>
		{/if}
	</div>
	<div class="flex-1">
		<StepIndicator {steps} onselect={onselectstep} />
	</div>
	<div class="flex items-center gap-2">
		{#if saveNote && !saveDisabledReason}
			<!-- UC-06 A2: uloží se jen potvrzená verze, rozpracovaný návrh ne. -->
			<Tooltip content={saveNote}>
				{#snippet trigger({ props })}
					<Button {...props} variant="secondary" onclick={onsave}>
						<Save size={16} strokeWidth={1.5} aria-hidden="true" />
						Uložit
					</Button>
				{/snippet}
			</Tooltip>
		{:else}
			<Button variant="secondary" disabledReason={saveDisabledReason} onclick={onsave}>
				<Save size={16} strokeWidth={1.5} aria-hidden="true" />
				Uložit
			</Button>
		{/if}
		<div class="hidden items-center gap-2 xl:flex">
			<Button variant="ghost" onclick={onload}>
				<FolderOpen size={16} strokeWidth={1.5} aria-hidden="true" />
				Načíst
			</Button>
			<Button variant="ghost" disabledReason={newDisabledReason} onclick={onnew}>
				<FilePlus size={16} strokeWidth={1.5} aria-hidden="true" />
				Nová zakázka
			</Button>
		</div>
		<div class="xl:hidden">
			<DropdownMenu label="Další akce se zakázkou" items={moreActions} />
		</div>
	</div>
</div>
