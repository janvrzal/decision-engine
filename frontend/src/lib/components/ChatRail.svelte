<script lang="ts">
	import PanelLeftOpen from '@lucide/svelte/icons/panel-left-open';
	import IconButton from './ui/IconButton.svelte';

	/** Sbalený Panel Dialog: pruh 44 px s ikonou pro rozbalení (komponenty.md). */
	let { onexpand }: { onexpand: () => void } = $props();
</script>

<div class="flex w-11 shrink-0 flex-col items-center border-r border-border bg-surface py-3">
	<IconButton label="Rozbalit dialog" onclick={onexpand} aria-expanded="false">
		<PanelLeftOpen size={16} strokeWidth={1.5} aria-hidden="true" />
	</IconButton>
</div>
