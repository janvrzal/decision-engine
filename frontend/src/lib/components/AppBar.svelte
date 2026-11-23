<script lang="ts">
	import { resolve } from '$app/paths';

	/** Horní lišta: logo a hlavní navigace. Sklad a vývojářský panel jen až budou hotové. */
</script>

<header class="flex h-12 shrink-0 items-center gap-6 border-b border-border bg-surface px-4">
	<a href={resolve('/')} class="flex items-center gap-2 rounded-sm text-heading text-ink">
		<span class="flex h-4 w-6 items-stretch gap-px overflow-hidden rounded-sm" aria-hidden="true">
			<span class="flex-3 bg-plan-part-1"></span>
			<span class="flex-2 bg-plan-part-2"></span>
			<span class="w-px bg-plan-cut"></span>
			<span class="flex-1 bg-plan-part-3"></span>
		</span>
		DecisionEngine
	</a>
	<nav aria-label="Hlavní navigace">
		<ul class="flex items-center gap-1">
			<li>
				<a
					href={resolve('/project')}
					aria-current="page"
					class="inline-flex h-8 items-center rounded-md px-3 text-body font-semibold text-ink underline decoration-accent-text decoration-2 underline-offset-8"
				>
					Zakázka
				</a>
			</li>
		</ul>
	</nav>
</header>
