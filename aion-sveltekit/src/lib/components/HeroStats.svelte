<script lang="ts">
	import { stats } from '$lib/stores/state';
	import { onMount } from 'svelte';

	let mounted = false;
	onMount(() => { mounted = true; });
</script>

<div class="hero-stats fade-in delay-1">
	<div class="hero-stat">
		<div class="stat-number success">{$stats.detectionRate || '54/54'}</div>
		<div class="stat-label">Scenarios Detected</div>
	</div>
	<div class="hero-stat">
		<div class="stat-number primary">{$stats.patterns || 66}</div>
		<div class="stat-label">Attack Patterns</div>
	</div>
	<div class="hero-stat">
		<div class="stat-number warning">{$stats.categories || 15}</div>
		<div class="stat-label">Threat Categories</div>
	</div>
	<div class="hero-stat">
		<div class="stat-number primary">&lt;0.1ms</div>
		<div class="stat-label">Response Time</div>
	</div>
</div>

<style>
	.hero-stats { display: flex; justify-content: center; gap: 60px; margin-bottom: 60px; flex-wrap: wrap; }
	.hero-stat { text-align: center; position: relative; }
	.hero-stat::after {
		content: ''; position: absolute; right: -30px; top: 50%; transform: translateY(-50%);
		width: 1px; height: 60px; background: linear-gradient(180deg, transparent, var(--border), transparent);
	}
	.hero-stat:last-child::after { display: none; }
	.stat-label { font-size: 0.85rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; }
</style>
