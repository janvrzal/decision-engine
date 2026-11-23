import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { describe, expect, it } from 'vitest';

/**
 * Hlídá pravidlo „jen tokeny“ (ADR-0010, skill ui-frontend): v kódu frontendu nejsou
 * pevné barvy ani libovolné hodnoty Tailwindu (`p-[13px]`, `bg-[#fff]`). Hodnoty patří
 * do docs/design-system/tokens.css.
 */

const SRC = join(import.meta.dirname, '..');

function sourceFiles(dir: string): string[] {
	return readdirSync(dir).flatMap((name) => {
		const path = join(dir, name);
		if (statSync(path).isDirectory()) return name === 'api' ? [] : sourceFiles(path);
		const isSource = /\.(svelte|ts)$/.test(name) && !/\.(spec|test)\.ts$/.test(name);
		return isSource ? [path] : [];
	});
}

const RULES: [string, RegExp][] = [
	['pevná barva', /#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/],
	['libovolná hodnota Tailwindu', /\b[a-z][\w-]*-\[[^\]]+\]/]
];

describe('design tokeny', () => {
	const files = sourceFiles(SRC);

	it('našel zdrojové soubory', () => {
		expect(files.length).toBeGreaterThan(5);
	});

	it.each(RULES)('žádný soubor nemá %s', (_name, pattern) => {
		const offenders = files.flatMap((file) =>
			readFileSync(file, 'utf8')
				.split('\n')
				.map((line, index) => ({ line, index }))
				.filter(({ line }) => pattern.test(line))
				.map(({ line, index }) => `${relative(SRC, file)}:${index + 1}: ${line.trim()}`)
		);
		expect(offenders).toEqual([]);
	});
});
