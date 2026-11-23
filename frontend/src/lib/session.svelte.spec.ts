import { describe, expect, it } from 'vitest';
import type { ViewModel } from './api/types';
import { Session } from './session.svelte';

function view(id: string, messages: ViewModel['messages'] = []): ViewModel {
	return {
		session: { id, ai: { extraction_available: true } },
		capabilities: [{ id: 'cutting_1d', label: 'Řezání tyčí' }],
		project: { name: 'Nová zakázka', revision: null, step: 'input', steps: [], has_content: false },
		pending_operation: null,
		messages,
		proposal: null,
		result: null
	};
}

type Reply = { data?: ViewModel; status: number };

/** Falešný klient API: vrací připravené odpovědi a zaznamená požadavky. */
function fakeClient(replies: Reply[]) {
	const calls: { path: string; body?: unknown }[] = [];
	let release: (() => void) | null = null;
	const respond = (path: string, body?: unknown) => {
		calls.push({ path, body });
		const reply = replies.shift() ?? { status: 500 };
		return new Promise<{ data?: ViewModel; response: Response }>((resolve) => {
			const done = () =>
				resolve({ data: reply.data, response: new Response(null, { status: reply.status }) });
			if (path.endsWith('/events')) release = done;
			else done();
		});
	};
	const client = {
		GET: (path: string) => respond(path),
		POST: (path: string, init?: { body?: unknown }) => respond(path, init?.body)
	};
	return { client, calls, finish: () => release?.() };
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
