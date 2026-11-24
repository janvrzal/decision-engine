/**
 * Ochrana neuložené práce (UC-15, UC-06 A1): akce, která zahodí rozpracovanou zakázku,
 * se nejdřív zeptá. O tom, zda je co ztratit, rozhoduje backend (`unsaved_changes`);
 * když klient vycházel ze zastaralého stavu (druhá karta), backend akci odmítne a dialog
 * se otevře podle čerstvého stavu.
 */

export interface GuardedAction {
	/** Text tlačítka, které práci zahodí („Zahodit zakázku“, „Zahodit a načíst“). */
	label: string;
	/**
	 * Provede akci; `discardUnsaved` říká backendu, že uživatel zahození potvrdil.
	 * Vrátí, zda se akce provedla (backend ji bez potvrzení odmítne, je-li co ztratit).
	 */
	run: (discardUnsaved: boolean) => Promise<boolean>;
}

export class DiscardGuard {
	/** Akce, na kterou se dialog ptá. */
	action = $state<GuardedAction | null>(null);
	open = $state(false);
	busy = $state(false);
	error = $state<string | null>(null);

	constructor(
		private readonly hasUnsaved: () => boolean,
		private readonly save: () => Promise<string | null>
	) {}

	/** Bez neuložené práce akci rovnou provede, jinak otevře dialog. */
	async request(action: GuardedAction): Promise<void> {
		if (this.hasUnsaved()) {
			this.ask(action);
			return;
		}
		const applied = await action.run(false);
		// Backend akci odmítl, protože neuložená práce přece jen je: zeptat se.
		if (!applied && this.hasUnsaved()) this.ask(action);
	}

	/** Uživatel rozhodl: uložit a pokračovat, nebo zahodit. */
	async proceed(saveFirst: boolean): Promise<void> {
		const action = this.action;
		if (!action || this.busy) return;
		this.busy = true;
		const error = saveFirst ? await this.save() : null;
		this.busy = false;
		// Uživatel mezitím dialog zrušil: akce se neprovede.
		if (this.action !== action || !this.open) return;
		if (error) {
			this.error = error;
			return;
		}
		this.close();
		await action.run(true);
	}

	close(): void {
		this.open = false;
		this.action = null;
	}

	private ask(action: GuardedAction): void {
		this.action = action;
		this.error = null;
		this.open = true;
	}
}
