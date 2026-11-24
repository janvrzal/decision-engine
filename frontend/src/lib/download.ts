import type { api } from './api/client.js';

/**
 * Uložení zakázky do souboru (UC-06): obsah i název skládá backend, frontend jen předá
 * stažený soubor prohlížeči.
 */

type Client = Pick<typeof api, 'GET'>;

export type SaveResult =
	{ ok: true; fileName: string; revision: number | null } | { ok: false; message: string };

const FALLBACK_NAME = 'zakazka.decision.json';
const REVISION_HEADER = 'X-Project-Revision';

/** Revize zakázky ve staženém souboru; backend ji posílá v hlavičce. */
export function revisionFromHeader(header: string | null): number | null {
	if (header === null || !/^\d+$/.test(header.trim())) return null;
	return Number(header.trim());
}

/** Název souboru z hlavičky `Content-Disposition` (`filename*=UTF-8''…` nebo `filename=…`). */
export function fileNameFromDisposition(header: string | null): string {
	if (!header) return FALLBACK_NAME;
	const encoded = /filename\*=UTF-8''([^;]+)/i.exec(header);
	if (encoded) {
		try {
			return decodeURIComponent(encoded[1].trim());
		} catch {
			return FALLBACK_NAME;
		}
	}
	const plain = /filename="?([^";]+)"?/i.exec(header);
	return plain ? plain[1].trim() : FALLBACK_NAME;
}

export async function saveProject(client: Client, sessionId: string): Promise<SaveResult> {
	try {
		const { data, response } = await client.GET('/api/sessions/{session_id}/project', {
			params: { path: { session_id: sessionId } },
			parseAs: 'blob'
		});
		if (!data || !response.ok) {
			return {
				ok: false,
				message:
					response.status === 409
						? 'Uložit jde potvrzená zakázka.'
						: 'Zakázku se nepodařilo uložit. Zkuste to znovu.'
			};
		}
		const fileName = fileNameFromDisposition(response.headers.get('Content-Disposition'));
		const url = URL.createObjectURL(data);
		const link = document.createElement('a');
		link.href = url;
		link.download = fileName;
		link.click();
		// Některé prohlížeče začnou stahovat až po návratu do smyčky událostí.
		setTimeout(() => URL.revokeObjectURL(url), 0);
		return {
			ok: true,
			fileName,
			revision: revisionFromHeader(response.headers.get(REVISION_HEADER))
		};
	} catch {
		return { ok: false, message: 'Server neodpovídá, zakázka se neuložila.' };
	}
}
