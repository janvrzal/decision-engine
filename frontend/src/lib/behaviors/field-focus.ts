/**
 * Přesun fokusu na pole formuláře podle klíče (`parts.1.length_mm`, `parameters.objective`)
 * z odkazu v souhrnu chyb (komponenty.md, ValidationSummary). Pole nese `data-cell`;
 * u skupiny (tabulka, volba cíle) dostane fokus vybraná volba nebo první vstup uvnitř.
 */

const FOCUSABLE = 'input:not([disabled]), [role="radio"]:not([disabled])';

export function findField(root: ParentNode, target: string): HTMLElement | null {
	const field = root.querySelector<HTMLElement>(`[data-cell="${CSS.escape(target)}"]`);
	if (!field || field.matches(FOCUSABLE)) return field;
	return (
		field.querySelector<HTMLElement>('[role="radio"][aria-checked="true"]') ??
		field.querySelector<HTMLElement>(FOCUSABLE)
	);
}

/** Zaostří pole a posune ho do zobrazení; vrátí, zda pole existuje. */
export function focusField(root: ParentNode, target: string): boolean {
	const field = findField(root, target);
	if (!field) return false;
	field.focus({ preventScroll: true });
	field.scrollIntoView({ block: 'center', behavior: 'smooth' });
	return true;
}
