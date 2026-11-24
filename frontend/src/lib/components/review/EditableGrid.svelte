<script lang="ts" generics="Row extends { id: string }">
	import Plus from '@lucide/svelte/icons/plus';
	import Trash from '@lucide/svelte/icons/trash';
	import { tick } from 'svelte';
	import { gridAction } from '#lib/behaviors/grid-navigation.js';
	import Button from '../ui/Button.svelte';
	import IconButton from '../ui/IconButton.svelte';
	import CellInput from './CellInput.svelte';
	import type { CellState, GridColumn } from './grid-types.js';

	/**
	 * Editovatelná tabulka (komponenty.md, EditableGrid): šipky mezi řádky, Enter potvrdí
	 * a přejde dolů (na posledním řádku přidá řádek), Esc vrátí hodnotu, Tab dál.
	 */
	let {
		caption,
		name,
		columns,
		rows = $bindable(),
		cell,
		rowLabel,
		addLabel,
		disabled = false,
		oncommit,
		onadd,
		onremove
	}: {
		caption: string;
		/** Klíč tabulky pro odkazy ze souhrnu chyb (`parts`, buňky `parts.0.length_mm`). */
		name: string;
		columns: GridColumn[];
		rows: Row[];
		cell: (row: number, key: string) => CellState;
		rowLabel: (row: number) => string;
		addLabel: string;
		disabled?: boolean;
		oncommit: () => void;
		onadd: () => void;
		onremove: (row: number) => void;
	} = $props();

	let table = $state<HTMLTableElement | null>(null);
	let original = '';

	// Řádky konceptu mají jen textová pole (hodnoty buněk) a `id`.
	function read(row: number, key: string): string {
		const value: unknown = (rows[row] as unknown as Record<string, unknown>)[key];
		return typeof value === 'string' ? value : '';
	}

	function write(row: number, key: string, value: string) {
		(rows[row] as unknown as Record<string, string>)[key] = value;
	}

	async function focusCell(row: number, col: number) {
		await tick();
		table?.querySelector<HTMLInputElement>(`[data-row="${row}"][data-col="${col}"]`)?.focus();
	}

	async function onkeydown(event: KeyboardEvent, row: number, col: number) {
		const action = gridAction(event.key, { row, col }, rows.length, {
			shift: event.shiftKey,
			alt: event.altKey,
			ctrl: event.ctrlKey || event.metaKey
		});
		switch (action.type) {
			case 'move':
				event.preventDefault();
				await focusCell(action.to.row, action.to.col);
				break;
			case 'commit-and-move':
				event.preventDefault();
				await focusCell(action.to.row, action.to.col);
				break;
			case 'commit-and-add-row':
				event.preventDefault();
				onadd();
				await focusCell(rows.length - 1, 0);
				break;
			case 'revert':
				event.preventDefault();
				write(row, columns[col].key, original);
				break;
		}
	}
</script>

<div class="flex flex-col gap-2" data-cell={name}>
	<table bind:this={table} class="w-full border-collapse">
		<caption class="pb-2 text-left text-heading text-ink">{caption}</caption>
		<thead>
			<tr class="bg-surface-sunken">
				{#each columns as column (column.key)}
					<th
						scope="col"
						class="px-2 py-2 text-label font-medium text-ink-muted uppercase {column.numeric
							? 'text-right'
							: 'text-left'}"
					>
						{column.label}
					</th>
				{/each}
				<th scope="col" class="w-10"><span class="sr-only">Akce</span></th>
			</tr>
		</thead>
		<tbody>
			<!-- Klíčem je pořadí: id řádku může pocházet z načteného souboru a nemusí být jedinečné. -->
			{#each rows, r (r)}
				<tr class="border-b border-border align-top">
					{#each columns as column, c (column.key)}
						{@const state = cell(r, column.key)}
						<td class="px-1 py-1">
							<CellInput
								value={read(r, column.key)}
								onvalue={(value: string) => write(r, column.key, value)}
								label="{rowLabel(r)}, {column.label}"
								unit={column.unit}
								numeric={column.numeric}
								placeholder={column.placeholder}
								unconfirmed={state.unconfirmed}
								error={state.error}
								readonly={disabled}
								data-row={r}
								data-col={c}
								data-cell="{name}.{r}.{column.key}"
								onfocus={() => (original = read(r, column.key))}
								onkeydown={(event: KeyboardEvent) => onkeydown(event, r, c)}
								{oncommit}
							/>
						</td>
					{/each}
					<td class="px-1 py-1 text-right">
						<IconButton
							label="Odebrat {rowLabel(r).toLowerCase()}"
							disabledReason={disabled
								? 'Počkejte na dokončení.'
								: rows.length === 1
									? 'Aspoň jeden řádek musí zůstat.'
									: undefined}
							onclick={() => onremove(r)}
						>
							<Trash size={16} strokeWidth={1.5} aria-hidden="true" />
						</IconButton>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>
	<div>
		<Button
			variant="ghost"
			onclick={async () => {
				onadd();
				await focusCell(rows.length - 1, 0);
			}}
			disabledReason={disabled ? 'Počkejte na dokončení.' : undefined}
		>
			<Plus size={16} strokeWidth={1.5} aria-hidden="true" />
			{addLabel}
		</Button>
	</div>
</div>
