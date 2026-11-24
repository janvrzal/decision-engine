/**
 * Fokus a oznámení po změně kroku (WCAG 2.4.3, 4.1.3; Issue #59).
 *
 * Po přechodu na jiný krok se fokus přesune na nadpis kroku, aby další Tab nezačínal
 * od konce stránky, a živá oblast krátce řekne, co se stalo. Texty skládá jen
 * z hodnot, které dodal backend; nic nepočítá.
 */

export type StepId = 'input' | 'review' | 'result';

/** Id nadpisu kroku, na který se po změně kroku přesune fokus. */
export const STEP_HEADING: Record<StepId, string> = {
	input: 'input-step-title',
	review: 'review-title',
	result: 'result-title'
};

/** Krátké oznámení pro čtečku po přechodu na krok. */
export function stepAnnouncement(step: StepId, resultSummary: string | null): string {
	switch (step) {
		case 'input':
			return 'Zadání: popište, co potřebujete nařezat.';
		case 'review':
			return 'Kontrola údajů: zkontrolujte údaje a spusťte výpočet.';
		case 'result':
			return resultSummary ? `Plán spočítán: ${resultSummary}.` : 'Nářezový plán.';
	}
}

/**
 * Přesune fokus na prvek s daným id (nadpis má `tabindex="-1"`). Fokus, který krok
 * sám přesunul do svého obsahu (první buňka ručního zadání), nepřebije.
 */
export function focusById(id: string, root: Document = document): boolean {
	const target = root.getElementById(id);
	if (!target) return false;
	const active = root.activeElement;
	const step = target.closest('section');
	if (active && active !== target && step?.contains(active)) return false;
	target.focus({ preventScroll: false });
	return true;
}
