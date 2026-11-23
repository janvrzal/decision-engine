import { api } from './api/client.js';
import type { UserEvent, ViewModel } from './api/types.js';

/**
 * Stav relace ve frontendu: jen view model z backendu a co se právě posílá (ADR-0006).
 * Frontend nic nepočítá; během dlouhého požadavku ukazuje průběh a odeslanou zprávu.
 */

const STORAGE_KEY = 'decision-engine:session';

export type Pending = { kind: 'extraction' | 'solving'; text?: string };
export type Problem = 'session_lost' | 'unreachable';

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
	lastEvent: UserEvent | null = null;

	constructor(private readonly client: Client = api) {}

	/** Načte uloženou relaci, nebo založí novou. */
	async start(): Promise<void> {
		const stored = readStoredId();
		if (stored) {
			const { data, response } = await this.client.GET('/api/sessions/{session_id}', {
				params: { path: { session_id: stored } }
			});
			if (data) {
				this.view = data;
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

	get busy(): boolean {
		return this.pending !== null;
	}

	/** Pošle událost a převezme nový view model. */
	async send(event: UserEvent): Promise<void> {
		const id = this.view?.session.id;
		if (!id || this.pending) return;
		this.lastEvent = event;
		this.pending = pendingFor(event);
		try {
			const { data, response } = await this.client.POST('/api/sessions/{session_id}/events', {
				params: { path: { session_id: id } },
				body: event
			});
			if (data) {
				this.view = data;
				this.problem = null;
			} else if (response.status === 404) {
				storeId(null);
				this.problem = 'session_lost';
			} else {
				this.problem = 'unreachable';
			}
		} catch {
			this.problem = 'unreachable';
		} finally {
			this.pending = null;
		}
	}

	/** Zopakuje poslední událost (po výpadku spojení nebo chybě AI). */
	async retry(): Promise<void> {
		if (this.lastEvent) await this.send(this.lastEvent);
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
