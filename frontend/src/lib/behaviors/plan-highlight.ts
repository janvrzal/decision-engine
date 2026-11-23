/**
 * Zvýraznění dílu v plánu (plan-rezani.md): všechny výskyty typu se vyplní barvou typu
 * a dostanou obrys `plan-highlight`. SVG generuje backend; každý kus má `data-part-id`,
 * první obdélník je tělo dílu a druhý proužek v barvě typu.
 */

const HIGHLIGHT = 'data-highlight';

export function highlightPart(root: Element | null, partId: string | null): void {
	if (!root) return;
	for (const group of root.querySelectorAll<SVGGElement>('g[data-part-id]')) {
		const [body, stripe] = Array.from(group.querySelectorAll<SVGRectElement>('rect'));
		const active = partId !== null && group.dataset.partId === partId;
		if (active) group.setAttribute(HIGHLIGHT, '');
		else group.removeAttribute(HIGHLIGHT);
		if (body && stripe) {
			// Dynamická hodnota z SVG (barva typu dílu), ne pevná barva ve frontendu.
			body.style.fill = active ? (stripe.getAttribute('fill') ?? '') : '';
			body.style.stroke = active ? 'var(--color-plan-highlight)' : '';
			body.style.strokeWidth = active ? '2' : '';
		}
	}
}

/** Id dílu pod kurzorem (nebo `null`). */
export function partIdAt(target: EventTarget | null): string | null {
	if (!(target instanceof Element)) return null;
	return target.closest<SVGGElement>('g[data-part-id]')?.dataset.partId ?? null;
}
