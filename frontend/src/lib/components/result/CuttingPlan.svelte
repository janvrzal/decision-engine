<script lang="ts">
	import { highlightPart, partIdAt } from '#lib/behaviors/plan-highlight.js';

	/**
	 * Měřítkový plán (komponenty.md, CuttingPlan1D). SVG generuje backend (`render_svg`,
	 * texty escapované); frontend ho vloží a přidá zvýraznění dílu. Pod 560 px se plán
	 * posouvá do strany ve vlastním kontejneru.
	 */
	let {
		svg,
		highlighted = $bindable(null),
		dimmed = false
	}: { svg: string; highlighted?: string | null; dimmed?: boolean } = $props();

	let container = $state<HTMLElement | null>(null);

	$effect(() => {
		void svg;
		highlightPart(container, dimmed ? null : highlighted);
	});
</script>

<div class="overflow-x-auto" role="presentation">
	<div
		bind:this={container}
		class="min-w-140 transition-opacity duration-(--duration-base) ease-standard {dimmed
			? 'opacity-50'
			: ''}"
		onpointerover={(event) => {
			if (!dimmed) highlighted = partIdAt(event.target);
		}}
		onpointerleave={() => (highlighted = null)}
		role="presentation"
	>
		<!-- SVG pochází z vlastního backendu, který escapuje všechny texty. -->
		<!-- eslint-disable-next-line svelte/no-at-html-tags -->
		{@html svg}
	</div>
</div>
