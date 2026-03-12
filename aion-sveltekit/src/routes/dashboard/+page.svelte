<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getHealth,
		getStats,
		getSOCStatus,
		getImprovementStatus,
		getMetricsJson,
		getImprovementMetrics,
	} from '$lib/api/client';
	import type {
		HealthResponse,
		StatsResponse,
		SOCStatusResponse,
		ImprovementStatus,
		MetricsJsonResponse,
		DetectionMetrics,
	} from '$lib/api/types';

	// Reactive state
	let health: HealthResponse | null = $state(null);
	let stats: StatsResponse | null = $state(null);
	let socStatus: SOCStatusResponse | null = $state(null);
	let improvement: ImprovementStatus | null = $state(null);
	let metrics: MetricsJsonResponse | null = $state(null);
	let detectionMetrics: DetectionMetrics | null = $state(null);
	let loading = $state(true);
	let errors: string[] = $state([]);

	onMount(() => {
		fetchAll();
		const interval = setInterval(fetchAll, 10_000);
		return () => clearInterval(interval);
	});

	async function fetchAll() {
		errors = [];
		const [hRes, sRes, socRes, impRes, mRes, dmRes] = await Promise.all([
			getHealth(),
			getStats(),
			getSOCStatus(),
			getImprovementStatus(),
			getMetricsJson(),
			getImprovementMetrics(),
		]);

		if (hRes.ok) health = hRes.data; else errors.push(`Health: ${hRes.error.message}`);
		if (sRes.ok) stats = sRes.data; else errors.push(`Stats: ${sRes.error.message}`);
		if (socRes.ok) socStatus = socRes.data;
		if (impRes.ok) improvement = impRes.data;
		if (mRes.ok) metrics = mRes.data;
		if (dmRes.ok) detectionMetrics = dmRes.data;

		loading = false;
	}

	// Helpers
	function fmtNum(n: number | undefined): string {
		if (n == null) return '—';
		return n >= 1000 ? (n / 1000).toFixed(1) + 'K' : String(n);
	}

	function pct(n: number | undefined): string {
		if (n == null) return '—';
		return (n * 100).toFixed(1) + '%';
	}
</script>

{#if loading}
	<div class="loading-state">
		<div class="spinner"></div>
		<p>Connecting to AION OS backend…</p>
	</div>
{:else}

<!-- Error banner -->
{#if errors.length > 0}
	<div class="error-banner">
		<span class="error-icon">⚠</span>
		<span>{errors.join(' · ')}</span>
	</div>
{/if}

<!-- ── Row 1: Key Stats ────────────────────────────── -->
<section class="stat-row">
	<div class="stat-card">
		<div class="stat-value" class:success={health?.status === 'operational'}>
			{health?.status ?? 'unknown'}
		</div>
		<div class="stat-label">API Status</div>
	</div>
	<div class="stat-card">
		<div class="stat-value primary">{fmtNum(stats?.statistics?.total_analyses)}</div>
		<div class="stat-label">Analyses Run</div>
	</div>
	<div class="stat-card">
		<div class="stat-value warning">{fmtNum(stats?.statistics?.total_vulnerabilities)}</div>
		<div class="stat-label">Vulns Found</div>
	</div>
	<div class="stat-card">
		<div class="stat-value primary">{fmtNum(stats?.statistics?.total_critical)}</div>
		<div class="stat-label">Critical</div>
	</div>
	<div class="stat-card">
		<div class="stat-value">{fmtNum(socStatus?.total_alerts)}</div>
		<div class="stat-label">SOC Alerts</div>
	</div>
	<div class="stat-card">
		<div class="stat-value">{fmtNum(socStatus?.pattern_detections)}</div>
		<div class="stat-label">Patterns Hit</div>
	</div>
</section>

<!-- ── Row 2: Detection Quality + SOC Summary ──────── -->
<section class="grid-2col">
	<!-- Detection Quality -->
	<div class="panel">
		<h2 class="panel-title">Detection Quality</h2>
		{#if detectionMetrics}
			<div class="metrics-grid">
				<div class="metric-item">
					<div class="metric-val success">{pct(detectionMetrics.metrics?.precision)}</div>
					<div class="metric-lbl">Precision</div>
				</div>
				<div class="metric-item">
					<div class="metric-val success">{pct(detectionMetrics.metrics?.recall)}</div>
					<div class="metric-lbl">Recall</div>
				</div>
				<div class="metric-item">
					<div class="metric-val">{pct(detectionMetrics.metrics?.f1_score)}</div>
					<div class="metric-lbl">F1 Score</div>
				</div>
				<div class="metric-item">
					<div class="metric-val warning">{pct(detectionMetrics.metrics?.noise_ratio)}</div>
					<div class="metric-lbl">Noise Ratio</div>
				</div>
			</div>
			<div class="composite-score">
				<span>Composite Score</span>
				<span class="score-val">{detectionMetrics.score?.toFixed(2) ?? '—'}</span>
			</div>
		{:else}
			<p class="empty-text">No detection metrics available</p>
		{/if}
	</div>

	<!-- SOC Summary -->
	<div class="panel">
		<h2 class="panel-title">SOC Status</h2>
		{#if socStatus}
			<div class="soc-status-line">
				Status: <span class="badge" class:badge-ok={socStatus.status === 'active'}>{socStatus.status}</span>
			</div>

			{#if socStatus.high_risk_users.length > 0}
				<h3 class="sub-title">High-Risk Users</h3>
				<div class="risk-user-list">
					{#each socStatus.high_risk_users.slice(0, 5) as user}
						<a href="/dashboard/soc/users/{user.user_id}" class="risk-user-row">
							<span class="user-id">{user.user_id}</span>
							<span class="risk-badge" class:critical={user.risk_score > 75} class:high={user.risk_score > 50 && user.risk_score <= 75}>
								{user.risk_score}
							</span>
						</a>
					{/each}
				</div>
			{:else}
				<p class="empty-text">No high-risk users</p>
			{/if}

			{#if socStatus.recent_alerts.length > 0}
				<h3 class="sub-title">Recent Alerts</h3>
				<div class="alert-list">
					{#each socStatus.recent_alerts.slice(0, 4) as alert}
						<div class="alert-row">
							<span class="alert-type">{alert.alert_type}</span>
							<span class="alert-sev sev-{alert.severity}">{alert.severity}</span>
							<span class="alert-user">{alert.user_id}</span>
						</div>
					{/each}
				</div>
			{/if}

			<a href="/dashboard/soc" class="panel-link">View Full SOC →</a>
		{:else}
			<p class="empty-text">SOC offline or unavailable</p>
		{/if}
	</div>
</section>

<!-- ── Row 3: Improvement Engine + System Metrics ──── -->
<section class="grid-2col">
	<!-- Improvement Engine -->
	<div class="panel">
		<h2 class="panel-title">Improvement Engine</h2>
		{#if improvement}
			<div class="metrics-grid">
				<div class="metric-item">
					<div class="metric-val">{improvement.active_policy_version ?? '—'}</div>
					<div class="metric-lbl">Policy Version</div>
				</div>
				<div class="metric-item">
					<div class="metric-val">{improvement.total_feedback ?? 0}</div>
					<div class="metric-lbl">Feedback Items</div>
				</div>
				<div class="metric-item">
					<div class="metric-val warning">{improvement.pending_proposals ?? 0}</div>
					<div class="metric-lbl">Pending Proposals</div>
				</div>
				<div class="metric-item">
					<div class="metric-val">{improvement.cycle_count ?? 0}</div>
					<div class="metric-lbl">Cycles Run</div>
				</div>
			</div>
			<a href="/dashboard/improvement" class="panel-link">Manage Improvement →</a>
		{:else}
			<p class="empty-text">Improvement engine unavailable</p>
		{/if}
	</div>

	<!-- System Metrics snapshot -->
	<div class="panel">
		<h2 class="panel-title">System Metrics</h2>
		{#if metrics?.metrics}
			<div class="metric-table">
				{#each (metrics.metrics ?? []).slice(0, 8) as m}
					<div class="metric-row">
						<span class="metric-name">{m.name}</span>
						<span class="metric-type">{m.type}</span>
						<span class="metric-val-sm">{typeof m.value === 'number' ? m.value.toLocaleString() : m.value}</span>
					</div>
				{/each}
			</div>
			<a href="/dashboard/metrics" class="panel-link">Full Metrics →</a>
		{:else}
			<p class="empty-text">Metrics unavailable</p>
		{/if}
	</div>
</section>

{/if}

<style>
	/* ── Loading ────────────────────────────────────────── */
	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 60vh;
		gap: 16px;
		color: var(--text-dim);
	}
	.spinner {
		width: 32px; height: 32px;
		border: 3px solid rgba(255,255,255,0.1);
		border-top-color: var(--primary);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}
	@keyframes spin { to { transform: rotate(360deg); } }

	/* ── Error ──────────────────────────────────────────── */
	.error-banner {
		background: rgba(255,59,59,0.1);
		border: 1px solid rgba(255,59,59,0.25);
		border-radius: 8px;
		padding: 12px 16px;
		margin-bottom: 24px;
		font-size: 0.85rem;
		display: flex;
		align-items: center;
		gap: 10px;
		color: var(--primary);
	}
	.error-icon { font-size: 1.1rem; }

	/* ── Stat Row ──────────────────────────────────────── */
	.stat-row {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: 16px;
		margin-bottom: 28px;
	}
	.stat-card {
		background: var(--bg-card);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 20px;
		text-align: center;
	}
	.stat-value {
		font-family: 'JetBrains Mono', monospace;
		font-size: 1.8rem;
		font-weight: 700;
		line-height: 1.2;
		margin-bottom: 4px;
	}
	.stat-value.success { color: var(--success); }
	.stat-value.primary { color: var(--primary); }
	.stat-value.warning { color: var(--warning); }
	.stat-label {
		font-size: 0.75rem;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 1px;
	}

	/* ── Grid Layout ───────────────────────────────────── */
	.grid-2col {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 24px;
		margin-bottom: 28px;
	}
	@media (max-width: 900px) {
		.grid-2col { grid-template-columns: 1fr; }
	}

	/* ── Panels ────────────────────────────────────────── */
	.panel {
		background: var(--bg-card);
		border: 1px solid var(--border);
		border-radius: 16px;
		padding: 24px;
	}
	.panel-title {
		font-size: 1rem;
		font-weight: 600;
		margin-bottom: 20px;
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.panel-title::before {
		content: '';
		width: 3px;
		height: 16px;
		background: var(--primary);
		border-radius: 2px;
	}
	.panel-link {
		display: inline-block;
		margin-top: 16px;
		font-size: 0.82rem;
		color: var(--primary);
		text-decoration: none;
		transition: opacity 0.2s;
	}
	.panel-link:hover { opacity: 0.7; }

	.sub-title {
		font-size: 0.82rem;
		font-weight: 600;
		color: var(--text-dim);
		margin: 16px 0 8px;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.empty-text {
		color: rgba(255,255,255,0.3);
		font-size: 0.85rem;
		font-style: italic;
	}

	/* ── Metrics Grid ──────────────────────────────────── */
	.metrics-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 16px;
	}
	.metric-item { text-align: center; }
	.metric-val {
		font-family: 'JetBrains Mono', monospace;
		font-size: 1.6rem;
		font-weight: 700;
	}
	.metric-val.success { color: var(--success); }
	.metric-val.warning { color: var(--warning); }
	.metric-lbl {
		font-size: 0.72rem;
		color: var(--text-dim);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin-top: 2px;
	}

	.composite-score {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: 16px;
		padding: 12px 16px;
		background: rgba(255,255,255,0.03);
		border-radius: 8px;
		font-size: 0.88rem;
	}
	.score-val {
		font-family: 'JetBrains Mono', monospace;
		font-weight: 700;
		color: var(--success);
	}

	/* ── SOC items ─────────────────────────────────────── */
	.soc-status-line {
		font-size: 0.88rem;
		margin-bottom: 12px;
	}
	.badge {
		display: inline-block;
		padding: 2px 10px;
		border-radius: 12px;
		font-size: 0.75rem;
		font-weight: 600;
		background: rgba(255,170,0,0.15);
		color: var(--warning);
	}
	.badge-ok {
		background: rgba(0,255,136,0.12);
		color: var(--success);
	}

	.risk-user-list {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.risk-user-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 8px 12px;
		background: rgba(255,255,255,0.03);
		border-radius: 6px;
		text-decoration: none;
		color: inherit;
		font-size: 0.85rem;
		transition: background 0.15s;
	}
	.risk-user-row:hover { background: rgba(255,255,255,0.06); }
	.user-id { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }
	.risk-badge {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.78rem;
		font-weight: 700;
		color: var(--warning);
	}
	.risk-badge.critical { color: var(--primary); }
	.risk-badge.high { color: var(--warning); }

	.alert-list { display: flex; flex-direction: column; gap: 6px; }
	.alert-row {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 6px 10px;
		background: rgba(255,255,255,0.02);
		border-radius: 6px;
		font-size: 0.8rem;
	}
	.alert-type { flex: 1; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; }
	.alert-sev {
		padding: 1px 8px;
		border-radius: 8px;
		font-size: 0.7rem;
		font-weight: 600;
	}
	.sev-critical { background: rgba(255,59,59,0.2); color: var(--primary); }
	.sev-high { background: rgba(255,170,0,0.2); color: var(--warning); }
	.sev-medium { background: rgba(255,255,255,0.08); color: var(--text-dim); }
	.sev-low { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.4); }
	.alert-user { color: var(--text-dim); font-size: 0.78rem; }

	/* ── Metric Table ──────────────────────────────────── */
	.metric-table {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.metric-row {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 6px 10px;
		border-radius: 6px;
		font-size: 0.8rem;
	}
	.metric-row:nth-child(odd) { background: rgba(255,255,255,0.02); }
	.metric-name {
		flex: 1;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.75rem;
		color: var(--text-dim);
	}
	.metric-type {
		font-size: 0.65rem;
		color: rgba(255,255,255,0.3);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		width: 60px;
	}
	.metric-val-sm {
		font-family: 'JetBrains Mono', monospace;
		font-weight: 600;
		font-size: 0.82rem;
		min-width: 60px;
		text-align: right;
	}
</style>
