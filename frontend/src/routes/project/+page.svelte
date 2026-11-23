<script lang="ts">
	import ProjectScreen from '#lib/components/ProjectScreen.svelte';
	import { emptyProject } from '#lib/fixtures/empty-project.js';
</script>

<svelte:head>
	<title>{emptyProject.name} · DecisionEngine</title>
</svelte:head>

<ProjectScreen project={emptyProject} />
