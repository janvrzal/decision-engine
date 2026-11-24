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
		currentStep,
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
		/** Právě zobrazený krok (může být i neaktuální). */
		currentStep?: StepView['id'];
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

<!-- Pod 640 px má hlavička tři řádky: název, akce a kroky (#58). -->
<div
	class="flex shrink-0 flex-wrap items-center gap-x-6 gap-y-2 border-b border-border bg-surface px-4 py-3 print:hidden"
>
	<div class="xl:hidden">
		<Button variant="secondary" onclick={onopenchat} aria-haspopup="dialog">
			<MessageSquare size={16} strokeWidth={1.5} aria-hidden="true" />
			Dialog
		</Button>
	</div>
	<div class="order-first flex w-full min-w-0 items-center gap-2 sm:order-none sm:w-auto">
		<h1 class="min-w-0 truncate text-title text-ink">{name}</h1>
		{#if unsaved}
			<!-- Pod 640 px jen ikona, slovo zůstane čtečkám, aby se vešel název zakázky. -->
			<Badge variant="warning" icon={CircleDot}>
				<span class="max-sm:sr-only">neuloženo</span>
			</Badge>
		{/if}
	</div>
	<div class="order-last w-full sm:order-none sm:w-auto sm:flex-1">
		<StepIndicator {steps} current={currentStep} onselect={onselectstep} />
	</div>
	<div class="ml-auto flex items-center gap-2 sm:ml-0">
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
