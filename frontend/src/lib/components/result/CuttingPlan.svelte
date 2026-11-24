<script lang="ts">
	import { highlightPart, partIdAt } from '#lib/behaviors/plan-highlight.js';

	/**
	 * Měřítkový plán (komponenty.md, CuttingPlan1D). SVG generuje backend (`render_svg`,
	 * texty escapované); frontend ho vloží a přidá zvýraznění dílu. Pod 720 px se plán
	 * posouvá do strany ve vlastním kontejneru, aby se popisky nezmenšily pod čitelnost.
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

<!-- Posuvná oblast jde posunout i z klávesnice (WCAG 2.1.1, #59). -->
<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
	class="overflow-x-auto print:overflow-visible"
	role="region"
	aria-label="Nářezový plán, posuvný"
	tabindex="0"
>
	<div
		bind:this={container}
		class="min-w-180 transition-opacity duration-(--duration-base) ease-standard {dimmed
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
