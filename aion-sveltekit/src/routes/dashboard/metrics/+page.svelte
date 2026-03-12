<script lang="ts">
	import { onMount } from 'svelte';
	import { getMetricsJson, getMetricsPrometheus } from '$lib/api/client';
	import type { MetricsJsonResponse, MetricEntry } from '$lib/api/types';

	let metricsData: MetricsJsonResponse | null = $state(null);
	let prometheusText = $state('');
	let loading = $state(true);
	let error = $state('');
	let viewMode: 'cards' | 'prometheus' = $state('cards');

	// Filter
	let typeFilter: 'all' | 'counter' | 'gauge' | 'histogram' = $state('all');
	let searchQuery = $state('');

	function filterMetrics(data: MetricsJsonResponse | null, typeF: string, query: string): MetricEntry[] {
		const all: MetricEntry[] = data?.metrics ?? [];
		return all.filter((m) => {
			if (typeF !== 'all' && m.type !== typeF) return false;
			if (query && !m.name.toLowerCase().includes(query.toLowerCase())) return false;
			return true;
		});
	}

	let filtered = $derived(filterMetrics(metricsData, typeFilter, searchQuery));

	onMount(() => {
		fetchMetrics();
		const interval = setInterval(fetchMetrics, 10_000);
		return () => clearInterval(interval);
	});

	async function fetchMetrics() {
		const [jRes, pRes] = await Promise.all([getMetricsJson(), getMetricsPrometheus()]);
		if (jRes.ok) { metricsData = jRes.data; error = ''; }
		else error = jRes.error.message;
		if (pRes.ok) prometheusText = pRes.data;
		loading = false;
	}

	function metricIcon(type: string): string {
		switch (type) {
			case 'counter': return '↑';
			case 'gauge': return '◈';
			case 'histogram': return '▤';
			default: return '•';
		}
	}

	function fmtVal(v: number): string {
		if (v >= 1_000_000) return (v / 1_000_000).toFixed(2) + 'M';
		if (v >= 1_000) return (v / 1_000).toFixed(1) + 'K';
		return v % 1 === 0 ? String(v) : v.toFixed(3);
	}
</script>

{#if loading}
	<div class="loading-state">
		<div class="spinner"></div>
		<p>Loading metrics…</p>
	</div>
{:else if error}
	<div class="error-banner"><span>⚠</span> {error}</div>
{:else}

<!-- ── Controls ────────────────────────────────────── -->
<div class="controls-bar">
	<div class="view-toggle">
		<button class="view-btn" class:active={viewMode === 'cards'} onclick={() => viewMode = 'cards'}>Cards</button>
		<button class="view-btn" class:active={viewMode === 'prometheus'} onclick={() => viewMode = 'prometheus'}>Prometheus</button>
	</div>

	{#if viewMode === 'cards'}
		<div class="filter-group">
			<input
				type="text"
				class="search-input"
				placeholder="Filter metrics…"
				bind:value={searchQuery}
			/>
			<select class="type-select" bind:value={typeFilter}>
				<option value="all">All Types</option>
				<option value="counter">Counters</option>
				<option value="gauge">Gauges</option>
				<option value="histogram">Histograms</option>
			</select>
		</div>
	{/if}
</div>

<!-- ── Card View ───────────────────────────────────── -->
{#if viewMode === 'cards'}
	<div class="summary-row">
		<span class="summary-count">{filtered.length} metric{filtered.length !== 1 ? 's' : ''}</span>
		{#if metricsData?.timestamp}
			<span class="summary-time">Updated: {new Date(metricsData.timestamp).toLocaleTimeString()}</span>
		{/if}
	</div>

	<div class="metric-grid">
		{#each filtered as m (m.name)}
			<div class="metric-card type-{m.type}">
				<div class="mc-header">
					<span class="mc-icon">{metricIcon(m.type)}</span>
					<span class="mc-type">{m.type}</span>
				</div>
				<div class="mc-name">{m.name}</div>
				<div class="mc-value">{fmtVal(m.value)}</div>
				{#if m.help}
					<div class="mc-help">{m.help}</div>
				{/if}
				{#if m.labels && Object.keys(m.labels).length > 0}
					<div class="mc-labels">
						{#each Object.entries(m.labels) as [k, v]}
							<span class="label-tag">{k}={v}</span>
						{/each}
					</div>
				{/if}
			</div>
		{/each}
	</div>

	{#if filtered.length === 0}
		<p class="empty-text">No metrics match your filter.</p>
	{/if}

<!-- ── Prometheus View ─────────────────────────────── -->
{:else}
	<div class="prom-container">
		<div class="prom-header">
			<span class="prom-label">Prometheus Text Exposition Format</span>
			<button class="copy-btn" onclick={() => navigator.clipboard.writeText(prometheusText)}>
				Copy
			</button>
		</div>
		<pre class="prom-output">{prometheusText || '# No metrics available'}</pre>
	</div>
{/if}

{/if}

<style>
	.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 40vh; gap: 16px; color: var(--text-dim); }
	.spinner { width: 32px; height: 32px; border: 3px solid rgba(255,255,255,0.1); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
	.error-banner { background: rgba(255,59,59,0.1); border: 1px solid rgba(255,59,59,0.25); border-radius: 8px; padding: 12px 16px; font-size: 0.85rem; display: flex; align-items: center; gap: 10px; color: var(--primary); margin-bottom: 20px; }
	.empty-text { color: rgba(255,255,255,0.3); font-size: 0.85rem; font-style: italic; text-align: center; padding: 40px; }

	/* ── Controls ───────────────────────────────────────── */
	.controls-bar {
		display: flex; align-items: center; justify-content: space-between;
		margin-bottom: 24px; gap: 16px; flex-wrap: wrap;
	}
	.view-toggle { display: flex; gap: 0; border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }
	.view-btn {
		padding: 8px 20px; background: none; border: none; color: var(--text-dim);
		cursor: pointer; font-size: 0.85rem; transition: all 0.15s;
	}
	.view-btn:hover { color: var(--text); }
	.view-btn.active { background: rgba(255,59,59,0.15); color: var(--primary); font-weight: 600; }

	.filter-group { display: flex; gap: 10px; align-items: center; }
	.search-input {
		padding: 8px 14px; background: rgba(255,255,255,0.05); border: 1px solid var(--border);
		border-radius: 6px; color: var(--text); font-size: 0.85rem; width: 200px;
		font-family: 'JetBrains Mono', monospace;
	}
	.search-input:focus { border-color: var(--primary); outline: none; }
	.type-select {
		padding: 8px 12px; background: rgba(255,255,255,0.05); border: 1px solid var(--border);
		border-radius: 6px; color: var(--text); font-size: 0.85rem;
	}

	.summary-row {
		display: flex; align-items: center; justify-content: space-between;
		margin-bottom: 16px; font-size: 0.82rem; color: var(--text-dim);
	}

	/* ── Metric Cards ──────────────────────────────────── */
	.metric-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
		gap: 16px;
	}
	.metric-card {
		background: var(--bg-card); border: 1px solid var(--border);
		border-radius: 12px; padding: 20px; transition: border-color 0.2s;
	}
	.metric-card:hover { border-color: rgba(255,255,255,0.15); }
	.metric-card.type-counter { border-left: 3px solid var(--success); }
	.metric-card.type-gauge { border-left: 3px solid var(--warning); }
	.metric-card.type-histogram { border-left: 3px solid var(--primary); }

	.mc-header { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
	.mc-icon { font-size: 1rem; }
	.mc-type {
		font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;
		color: var(--text-dim);
	}
	.mc-name {
		font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
		margin-bottom: 8px; word-break: break-all;
	}
	.mc-value {
		font-family: 'JetBrains Mono', monospace; font-size: 1.8rem; font-weight: 700;
		margin-bottom: 8px;
	}
	.mc-help { font-size: 0.75rem; color: var(--text-dim); line-height: 1.4; }
	.mc-labels { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
	.label-tag {
		padding: 2px 8px; background: rgba(255,255,255,0.05);
		border-radius: 4px; font-family: 'JetBrains Mono', monospace;
		font-size: 0.68rem; color: var(--text-dim);
	}

	/* ── Prometheus View ───────────────────────────────── */
	.prom-container {
		background: var(--bg-card); border: 1px solid var(--border);
		border-radius: 12px; overflow: hidden;
	}
	.prom-header {
		display: flex; align-items: center; justify-content: space-between;
		padding: 12px 16px; border-bottom: 1px solid var(--border);
	}
	.prom-label { font-size: 0.78rem; color: var(--text-dim); font-family: 'JetBrains Mono', monospace; }
	.copy-btn {
		padding: 4px 14px; background: rgba(255,255,255,0.06); border: 1px solid var(--border);
		color: var(--text-dim); border-radius: 6px; cursor: pointer; font-size: 0.78rem;
		transition: all 0.2s;
	}
	.copy-btn:hover { border-color: var(--primary); color: var(--primary); }
	.prom-output {
		padding: 20px; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
		line-height: 1.6; max-height: 600px; overflow: auto; white-space: pre-wrap;
		color: var(--text-dim); margin: 0;
	}
</style>
