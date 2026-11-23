/**
 * Klávesnice v editovatelné tabulce (komponenty.md, EditableGrid): šipky nahoru a dolů
 * mezi řádky, Enter potvrdí buňku a přejde dolů (na posledním řádku přidá řádek),
 * Esc vrátí původní hodnotu. Tab a Shift+Tab nechává prohlížeči.
 */

export type GridPosition = { row: number; col: number };

export type GridAction =
	| { type: 'move'; to: GridPosition }
	| { type: 'commit-and-move'; to: GridPosition }
	| { type: 'commit-and-add-row'; col: number }
	| { type: 'revert' }
	| { type: 'none' };

export function gridAction(
	key: string,
	position: GridPosition,
	rowCount: number,
	modifiers: { shift?: boolean; alt?: boolean; ctrl?: boolean } = {}
): GridAction {
	if (modifiers.alt || modifiers.ctrl) return { type: 'none' };
	const { row, col } = position;
	switch (key) {
		case 'ArrowUp':
			return row > 0 ? { type: 'move', to: { row: row - 1, col } } : { type: 'none' };
		case 'ArrowDown':
			return row < rowCount - 1 ? { type: 'move', to: { row: row + 1, col } } : { type: 'none' };
		case 'Enter':
			if (modifiers.shift) {
				return row > 0 ? { type: 'commit-and-move', to: { row: row - 1, col } } : { type: 'none' };
			}
			return row < rowCount - 1
				? { type: 'commit-and-move', to: { row: row + 1, col } }
				: { type: 'commit-and-add-row', col };
		case 'Escape':
			return { type: 'revert' };
		default:
			return { type: 'none' };
	}
}
