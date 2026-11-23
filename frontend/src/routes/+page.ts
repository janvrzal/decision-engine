import { redirect } from '@sveltejs/kit';
import { resolve } from '$app/paths';

// Úvodní obrazovka přijde s UC-09; do té doby rovnou na zakázku.
export function load() {
	redirect(307, resolve('/project'));
}
