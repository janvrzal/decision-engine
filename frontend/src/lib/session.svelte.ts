import { api } from './api/client.js';
import type { UserEvent, ViewModel } from './api/types.js';

/**
 * Stav relace ve frontendu: jen view model z backendu a co se právě posílá (ADR-0006).
 * Frontend nic nepočítá; během dlouhého požadavku ukazuje průběh a odeslanou zprávu.
 */

const STORAGE_KEY = 'decision-engine:session';

export type Pending = { kind: 'extraction' | 'solving'; text?: string };
/** `rejected`: server akci odmítl jako neplatnou (4xx), opakování nepomůže. */
export type Problem = 'session_lost' | 'unreachable' | 'rejected';

/** Jak často se po obnovení stránky ptát, zda běžící operace skončila. */
const PENDING_POLL_MS = 1000;
/** Události, které počkají ve frontě i za dlouhou operací (nic dalšího nespouštějí). */
const QUEUED_WHILE_BUSY = new Set<UserEvent['type']>(['ProjectSaved']);

type Client = Pick<typeof api, 'GET' | 'POST'>;

function readStoredId(): string | null {
	try {
		return sessionStorage.getItem(STORAGE_KEY);
	} catch {
		return null;
	}
}

function storeId(id: string | null): void {
	try {
		if (id) sessionStorage.setItem(STORAGE_KEY, id);
		else sessionStorage.removeItem(STORAGE_KEY);
	} catch {
		// Úložiště může být nedostupné (soukromé okno); relace pak vydrží jen do obnovení.
	}
}

export class Session {
	view = $state<ViewModel | null>(null);
	pending = $state<Pending | null>(null);
	problem = $state<Problem | null>(null);
	/** Událost, která se kvůli výpadku spojení neprovedla; „Zkusit znovu“ ji pošle znovu. */
	lastFailed: UserEvent | null = null;

	constructor(
		private readonly client: Client = api,
		private readonly pollMs: number = PENDING_POLL_MS
	) {}

	/** Načte uloženou relaci, nebo založí novou. */
	async start(): Promise<void> {
		const stored = readStoredId();
		if (stored) {
			const { data, response } = await this.client.GET('/api/sessions/{session_id}', {
				params: { path: { session_id: stored } }
			});
			if (data) {
				this.view = data;
				// Stránka se obnovila během výpočtu nebo zpracování: počká se na výsledek.
				if (data.pending_operation) void this.follow(stored, data.pending_operation.kind);
				return;
			}
			if (response.status !== 404) {
				this.problem = 'unreachable';
				return;
			}
		}
		await this.restart();
	}

	/** Nová prázdná relace (po ztrátě relace nebo „Nová zakázka“). */
	async restart(): Promise<void> {
		this.problem = null;
		try {
			const { data } = await this.client.POST('/api/sessions');
			if (!data) throw new Error('bez dat');
			this.view = data;
			storeId(data.session.id);
		} catch {
			this.problem = 'unreachable';
		}
	}

	/** Dotazuje se na relaci, dokud běžící operace (z jiného požadavku) neskončí. */
	private async follow(id: string, kind: Pending['kind']): Promise<void> {
		this.pending = { kind };
		try {
			for (;;) {
				await new Promise((resolve) => setTimeout(resolve, this.pollMs));
				const { data } = await this.client.GET('/api/sessions/{session_id}', {
					params: { path: { session_id: id } }
				});
				if (!data) {
					this.problem = 'unreachable';
					return;
				}
				this.view = data;
				if (!data.pending_operation) return;
			}
		} catch {
			this.problem = 'unreachable';
		} finally {
			this.pending = null;
		}
	}

	get busy(): boolean {
		return this.pending !== null;
	}

	/** Řetěz odeslaných událostí: posílají se po jedné, ve stejném pořadí, v jakém vznikly. */
	private chain: Promise<void> = Promise.resolve();
	private queued = 0;

	/**
	 * Pošle událost a převezme nový view model. Rychle za sebou potvrzené úpravy buněk
	 * se neztratí ani nepředběhnou: čekají ve frontě a zobrazí se odpověď na poslední z nich.
	 * Během dlouhé operace (AI, výpočet) se další události neposílají; jen záznam o uložení
	 * souboru počká ve frontě, aby se štítek „neuloženo“ nezasekl.
	 */
	send(event: UserEvent): Promise<void> {
		if (!this.view) return Promise.resolve();
		if (this.pending && !QUEUED_WHILE_BUSY.has(event.type)) return Promise.resolve();
		// Dlouhou operaci je vidět hned a další události se do jejího konce nepřijímají.
		const pending = pendingFor(event);
		if (pending) this.pending = pending;
		this.queued += 1;
		this.chain = this.chain.then(() => this.post(event));
		return this.chain;
	}

	private async post(event: UserEvent): Promise<void> {
		this.queued -= 1;
		const id = this.view?.session.id;
		if (!id) return;
		try {
			const { data, response } = await this.client.POST('/api/sessions/{session_id}/events', {
				params: { path: { session_id: id } },
				body: event
			});
			if (data) {
				// Čeká-li za touto událostí další, její odpověď je novější; mezistav se nezobrazí.
				if (this.queued === 0) this.view = data;
				this.problem = null;
				this.lastFailed = null;
			} else if (response.status === 404) {
				storeId(null);
				this.problem = 'session_lost';
			} else if (response.status >= 400 && response.status < 500) {
				this.problem = 'rejected';
			} else {
				this.fail(event);
			}
		} catch {
			this.fail(event);
		} finally {
			if (pendingFor(event)) this.pending = null;
		}
	}

	private fail(event: UserEvent): void {
		this.problem = 'unreachable';
		this.lastFailed = event;
	}

	/** Zopakuje událost, která se neprovedla kvůli výpadku spojení. */
	async retry(): Promise<void> {
		if (this.lastFailed) await this.send(this.lastFailed);
	}

	/** Pošle znovu zprávu, kterou AI nezpracovala (text drží backend u chybové zprávy). */
	async retryMessage(text: string): Promise<void> {
		await this.send({ type: 'MessageSent', text });
	}
}

function pendingFor(event: UserEvent): Pending | null {
	switch (event.type) {
		case 'MessageSent':
			return { kind: 'extraction', text: event.text };
		case 'ProposalConfirmed':
		case 'SolveRequested':
			return { kind: 'solving' };
		default:
			return null;
	}
}
