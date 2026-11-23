import { describe, expect, it } from 'vitest';
import { gridAction } from './grid-navigation';

describe('gridAction', () => {
	it('šipky přecházejí mezi řádky ve stejném sloupci', () => {
		expect(gridAction('ArrowDown', { row: 0, col: 2 }, 3)).toEqual({
			type: 'move',
			to: { row: 1, col: 2 }
		});
		expect(gridAction('ArrowUp', { row: 0, col: 2 }, 3)).toEqual({ type: 'none' });
		expect(gridAction('ArrowDown', { row: 2, col: 0 }, 3)).toEqual({ type: 'none' });
	});

	it('Enter potvrdí a přejde dolů, na posledním řádku přidá řádek', () => {
		expect(gridAction('Enter', { row: 0, col: 1 }, 2)).toEqual({
			type: 'commit-and-move',
			to: { row: 1, col: 1 }
		});
		expect(gridAction('Enter', { row: 1, col: 1 }, 2)).toEqual({
			type: 'commit-and-add-row',
			col: 1
		});
	});

	it('Shift+Enter přejde nahoru', () => {
		expect(gridAction('Enter', { row: 1, col: 0 }, 2, { shift: true })).toEqual({
			type: 'commit-and-move',
			to: { row: 0, col: 0 }
		});
	});

	it('Esc vrátí hodnotu, ostatní klávesy nechá být', () => {
		expect(gridAction('Escape', { row: 0, col: 0 }, 1)).toEqual({ type: 'revert' });
		expect(gridAction('Tab', { row: 0, col: 0 }, 1)).toEqual({ type: 'none' });
		expect(gridAction('ArrowDown', { row: 0, col: 0 }, 3, { ctrl: true })).toEqual({
			type: 'none'
		});
	});
});
