import { defineConfig } from '@playwright/test';

const PORT = 4173;

// End-to-end testy běží proti skutečné aplikaci: sestavený frontend servíruje backend.
export default defineConfig({
	testDir: 'e2e',
	testMatch: '**/*.e2e.ts',
	use: { baseURL: `http://127.0.0.1:${PORT}` },
	webServer: {
		command: `pnpm build && uv run --project .. decision-engine --port ${PORT} --static-dir build`,
		url: `http://127.0.0.1:${PORT}/api/health`,
		reuseExistingServer: !process.env.CI,
		timeout: 120_000
	}
});
