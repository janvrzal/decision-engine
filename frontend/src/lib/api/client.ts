import createClient from 'openapi-fetch';
import type { paths } from './schema';

/**
 * Typovaný klient API. Typy se generují z OpenAPI backendu (`pnpm generate:api`),
 * ručně psané typy odpovědí jsou zakázané (ADR-0007).
 */
export const api = createClient<paths>({ baseUrl: '' });
