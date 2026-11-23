<script lang="ts" module>
	import type { Component } from 'svelte';

	export interface MenuItem {
		label: string;
		icon?: Component<{ size?: number; strokeWidth?: number }>;
		/** Neaktivní položka ukazuje důvod přímo pod názvem (v menu nejsou tooltipy). */
		disabledReason?: string;
		onselect?: () => void;
	}
</script>

<script lang="ts">
	import { DropdownMenu } from 'bits-ui';
	import Ellipsis from '@lucide/svelte/icons/ellipsis';

	/** Menu akcí „⋯“ (Bits DropdownMenu), např. v hlavičce zakázky na střední šířce. */
	let { label, items }: { label: string; items: MenuItem[] } = $props();
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger
		aria-label={label}
		class="inline-flex size-8 items-center justify-center rounded-md text-ink transition-colors duration-(--duration-fast) ease-standard hover:bg-surface-sunken"
	>
		<Ellipsis size={16} strokeWidth={1.5} aria-hidden="true" />
	</DropdownMenu.Trigger>
	<DropdownMenu.Portal>
		<DropdownMenu.Content
			align="end"
			sideOffset={4}
			class="z-50 flex min-w-56 flex-col rounded-lg border border-border bg-surface p-1 shadow-overlay"
		>
			{#each items as item (item.label)}
				<DropdownMenu.Item
					disabled={item.disabledReason !== undefined}
					onSelect={item.onselect}
					class="flex cursor-default items-start gap-2 rounded-md px-2 py-2 text-body text-ink outline-none data-disabled:text-ink-subtle data-highlighted:bg-surface-sunken"
				>
					{#if item.icon}
						<item.icon size={16} strokeWidth={1.5} />
					{/if}
					<span class="flex flex-col">
						<span class="font-semibold">{item.label}</span>
						{#if item.disabledReason}
							<span class="text-small">{item.disabledReason}</span>
						{/if}
					</span>
				</DropdownMenu.Item>
			{/each}
		</DropdownMenu.Content>
	</DropdownMenu.Portal>
</DropdownMenu.Root>
