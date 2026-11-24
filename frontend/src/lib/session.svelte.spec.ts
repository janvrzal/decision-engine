import { describe, expect, it } from 'vitest';
import type { ViewModel } from './api/types';
import { Session } from './session.svelte';

function view(id: string, messages: ViewModel['messages'] = []): ViewModel {
	return {
		session: { id, ai: { extraction_available: true } },
		capabilities: [{ id: 'cutting_1d', label: 'Řezání tyčí' }],
		project: {
			name: 'Nová zakázka',
			revision: null,
			step: 'input',
			steps: [],
			has_content: false,
			can_edit: false,
			can_save: false,
			save_note: null,
			unsaved_changes: false,
			can_start_new: true
		},
		pending_operation: null,
		messages,
		proposal: null,
		result: null,
		import_error: null
	};
}

type Reply = { data?: ViewModel; status: number };

/** Falešný klient API: vrací připravené odpovědi a zaznamená požadavky. */
function fakeClient(replies: Reply[]) {
	const calls: { path: string; body?: unknown }[] = [];
	// Odpovědi na události čekají na `finish()`; každé volání uvolní nejstarší čekající.
	const waiting: (() => void)[] = [];
	let released = 0;
	const respond = (path: string, body?: unknown) => {
		calls.push({ path, body });
		const reply = replies.shift() ?? { status: 500 };
		return new Promise<{ data?: ViewModel; response: Response }>((resolve) => {
			const done = () =>
				resolve({ data: reply.data, response: new Response(null, { status: reply.status }) });
			if (!path.endsWith('/events')) done();
			else if (released > 0) {
				released -= 1;
				done();
			} else waiting.push(done);
		});
	};
	const client = {
		GET: (path: string) => respond(path),
		POST: (path: string, init?: { body?: unknown }) => respond(path, init?.body)
	};
	const finish = () => {
		const next = waiting.shift();
		if (next) next();
		else released += 1;
	};
	return { client, calls, finish };
}

describe('Session', () => {
	it('založí relaci a během zprávy ukáže průběh s textem zprávy', async () => {
		sessionStorage.clear();
		const reply = view('r1', [{ id: 1, role: 'user', kind: 'text', text: 'regál' }]);
		const fake = fakeClient([
			{ data: view('r1'), status: 200 },
			{ data: reply, status: 200 }
		]);
		const session = new Session(fake.client as never);

		await session.start();
		expect(session.view?.session.id).toBe('r1');
		expect(sessionStorage.getItem('decision-engine:session')).toBe('r1');

		const sending = session.send({ type: 'MessageSent', text: 'regál' });
		expect(session.pending).toEqual({ kind: 'extraction', text: 'regál' });

		fake.finish();
		await sending;
		expect(session.pending).toBeNull();
		expect(session.view?.messages).toHaveLength(1);
	});

	it('během zpracování další událost neodešle', async () => {
		sessionStorage.clear();
		const fake = fakeClient([
			{ data: view('r2'), status: 200 },
			{ data: view('r2'), status: 200 }
		]);
		const session = new Session(fake.client as never);
		await session.start();

		const first = session.send({ type: 'ProposalConfirmed' });
		await session.send({ type: 'SolveRequested' });
		fake.finish();
		await first;

		expect(fake.calls.filter((call) => call.path.endsWith('/events'))).toHaveLength(1);
	});

	it('ztracená relace (404) se ohlásí a zapomene', async () => {
		sessionStorage.clear();
		const fake = fakeClient([{ data: view('r3'), status: 200 }, { status: 404 }]);
		const session = new Session(fake.client as never);
		await session.start();

		const sending = session.send({ type: 'SolveRequested' });
		fake.finish();
		await sending;

		expect(session.problem).toBe('session_lost');
		expect(sessionStorage.getItem('decision-engine:session')).toBeNull();
	});
});

describe('Session – fronta úprav', () => {
	it('úpravy rychle za sebou odejdou všechny, po jedné a ve stejném pořadí', async () => {
		sessionStorage.clear();
		const fake = fakeClient([
			{ data: view('r4'), status: 200 },
			{ data: view('r4', [{ id: 1, role: 'user', kind: 'text', text: 'první' }]), status: 200 },
			{ data: view('r4', [{ id: 2, role: 'user', kind: 'text', text: 'druhá' }]), status: 200 }
		]);
		const session = new Session(fake.client as never);
		await session.start();

		const first = session.send({ type: 'ProposalRejected' });
		const second = session.send({ type: 'EditRequested' });
		await Promise.resolve();
		// Druhá úprava čeká, dokud backend neodpoví na první.
		expect(fake.calls.filter((call) => call.path.endsWith('/events'))).toHaveLength(1);

		fake.finish();
		await first;
		fake.finish();
		await second;

		const events = fake.calls.filter((call) => call.path.endsWith('/events'));
		expect(events.map((call) => (call.body as { type: string }).type)).toEqual([
			'ProposalRejected',
			'EditRequested'
		]);
		expect(session.view?.messages[0]?.text).toBe('druhá');
	});
});

describe('Session – opakování a dlouhé operace', () => {
	it('záznam o uložení počká ve frontě za výpočtem a neztratí se', async () => {
		sessionStorage.clear();
		const fake = fakeClient([
			{ data: view('r5'), status: 200 },
			{ data: view('r5'), status: 200 },
			{ data: view('r5'), status: 200 }
		]);
		const session = new Session(fake.client as never);
		await session.start();

		const solving = session.send({ type: 'ProposalConfirmed' });
		const saved = session.send({ type: 'ProjectSaved', revision: 0 });
		fake.finish();
		fake.finish();
		await Promise.all([solving, saved]);

		const events = fake.calls.filter((call) => call.path.endsWith('/events'));
		expect(events.map((call) => (call.body as { type: string }).type)).toEqual([
			'ProposalConfirmed',
			'ProjectSaved'
		]);
	});

	it('„Zkusit znovu“ po výpadku pošle událost, která se neprovedla, ne jinou', async () => {
		sessionStorage.clear();
		const fake = fakeClient([
			{ data: view('r6'), status: 200 },
			{ data: view('r6'), status: 200 },
			{ status: 503 },
			{ data: view('r6'), status: 200 }
		]);
		const session = new Session(fake.client as never);
		await session.start();

		const edit = session.send({ type: 'EditRequested' });
		fake.finish();
		await edit;
		const solve = session.send({ type: 'SolveRequested' });
		fake.finish();
		await solve;
		expect(session.problem).toBe('unreachable');

		const retry = session.retry();
		fake.finish();
		await retry;

		const events = fake.calls.filter((call) => call.path.endsWith('/events'));
		expect((events.at(-1)?.body as { type: string }).type).toBe('SolveRequested');
		expect(session.problem).toBeNull();
	});

	it('odmítnutou akci (422) ohlásí jako odmítnutou, ne jako výpadek', async () => {
		sessionStorage.clear();
		const fake = fakeClient([{ data: view('r7'), status: 200 }, { status: 422 }]);
		const session = new Session(fake.client as never);
		await session.start();

		const sending = session.send({ type: 'EditRequested' });
		fake.finish();
		await sending;

		expect(session.problem).toBe('rejected');
		expect(session.lastFailed).toBeNull();
	});

	it('po obnovení stránky během výpočtu počká na jeho konec', async () => {
		sessionStorage.setItem('decision-engine:session', 'r8');
		const running = { ...view('r8'), pending_operation: { kind: 'solving' as const, label: '' } };
		const fake = fakeClient([
			{ data: running, status: 200 },
			{ data: running, status: 200 },
			{ data: view('r8'), status: 200 }
		]);
		const session = new Session(fake.client as never, 1);

		await session.start();
		expect(session.pending).toEqual({ kind: 'solving' });

		await expect.poll(() => session.pending).toBeNull();
		expect(fake.calls).toHaveLength(3);
	});
});
