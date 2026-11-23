/** Typy editovatelné tabulky (EditableGrid). */

export interface GridColumn {
	key: string;
	label: string;
	unit?: string;
	numeric?: boolean;
	placeholder?: string;
}

export interface CellState {
	unconfirmed: boolean;
	error: string | null;
}
