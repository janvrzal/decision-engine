import { defineConfig } from '@playwright/test';

const PORT = 4173;

// End-to-end testy běží proti skutečné aplikaci: sestavený frontend servíruje backend.
// Model AI se přehrává ze souboru (deterministicky, bez sítě a klíčů), solver je skutečný.
export default defineConfig({
	testDir: 'e2e',
	testMatch: '**/*.e2e.ts',
	use: { baseURL: `http://127.0.0.1:${PORT}` },
	workers: 1,
	webServer: {
		command: `pnpm build && uv run --project .. decision-engine --port ${PORT} --static-dir build`,
		url: `http://127.0.0.1:${PORT}/api/health`,
		env: { LLM_REPLAY_FILE: 'e2e/fixtures/uc01.json' },
		reuseExistingServer: false,
		timeout: 120_000
	}
});
