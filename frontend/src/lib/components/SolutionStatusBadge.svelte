<script lang="ts">
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import CircleX from '@lucide/svelte/icons/circle-x';
	import Info from '@lucide/svelte/icons/info';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import TriangleExclamation from '@lucide/svelte/icons/triangle-exclamation-point';
	import type { SolutionStatus } from '#lib/api/types.js';

	/** Stav plánu: vždy ikona + slovo, nikdy jen barva (komponenty.md). */
	let {
		status,
		label,
		stale = false
	}: { status: SolutionStatus; label: string; stale?: boolean } = $props();

	const variants = {
		optimal: { icon: CircleCheck, classes: 'bg-success-bg text-success' },
		best_found: { icon: Info, classes: 'bg-info-bg text-info' },
		partial: { icon: TriangleExclamation, classes: 'bg-warning-bg text-warning' },
		infeasible: { icon: CircleX, classes: 'bg-danger-bg text-danger' }
	} as const;
	let variant = $derived(
		stale ? { icon: RefreshCw, classes: 'bg-stale-bg text-stale' } : variants[status]
	);
	let Icon = $derived(variant.icon);
</script>

<span
	class="inline-flex h-5.5 items-center gap-1 rounded-sm px-2 text-label font-medium uppercase {variant.classes}"
	data-status={stale ? 'stale' : status}
>
	<Icon size={14} strokeWidth={2} aria-hidden="true" />
	{stale ? 'Neaktuální' : label}
</span>
