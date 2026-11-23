<script lang="ts">
	/**
	 * Indikátor práce místo spinneru (komponenty.md): do malé tyče postupně padají díly
	 * v barvách plánu. Vždy s textem; při omezeném pohybu stojí se dvěma vloženými díly.
	 */
	let { label, size = 'small' }: { label: string; size?: 'small' | 'large' } = $props();
</script>

<div class="flex items-center gap-3" role="status" aria-live="polite">
	<span
		class="loader relative flex shrink-0 overflow-hidden rounded-sm bg-plan-bar {size === 'large'
			? 'h-4 w-24'
			: 'h-3 w-11'}"
		aria-hidden="true"
	>
		<span class="piece piece-1 bg-plan-part-1"></span>
		<span class="piece piece-2 bg-plan-part-2"></span>
		<span class="piece piece-3 bg-plan-part-3"></span>
	</span>
	<span class="text-body text-ink-muted">{label}</span>
</div>

<style>
	.piece {
		height: 100%;
		width: 30%;
		margin-right: 3%;
		animation: drop 1.8s var(--ease-standard) infinite;
	}
	.piece-2 {
		animation-delay: 0.3s;
	}
	.piece-3 {
		animation-delay: 0.6s;
	}
	@keyframes drop {
		0% {
			transform: translateY(-110%);
			opacity: 0;
		}
		25%,
		80% {
			transform: translateY(0);
			opacity: 1;
		}
		100% {
			transform: translateY(0);
			opacity: 0;
		}
	}
	@media (prefers-reduced-motion: reduce) {
		.piece {
			animation: none;
		}
		.piece-3 {
			visibility: hidden;
		}
	}
</style>
