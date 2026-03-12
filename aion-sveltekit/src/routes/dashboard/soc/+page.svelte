<script lang="ts">
	import { onMount } from 'svelte';
	import { getSOCStatus, ingestSOCAlert } from '$lib/api/client';
	import type { SOCStatusResponse, SOCAlert } from '$lib/api/types';

	let socStatus: SOCStatusResponse | null = $state(null);
	let loading = $state(true);
	let error = $state('');

	// Ingest test alert form
	let showIngest = $state(false);
	let ingestForm = $state({
		alert_type: 'vpn_anomaly',
		severity: 'medium' as const,
		user_id: '',
		action: 'login_attempt',
		details: '{}',
	});
	let ingestResult = $state<string | null>(null);

	onMount(() => {
		fetchStatus();
		const interval = setInterval(fetchStatus, 8_000);
		return () => clearInterval(interval);
	});

	async function fetchStatus() {
		const res = await getSOCStatus();
		if (res.ok) {
			socStatus = res.data;
			error = '';
		} else {
			error = res.error.message;
		}
		loading = false;
	}

	async function submitAlert() {
		let details = {};
		try { details = JSON.parse(ingestForm.details); } catch { /* ignore */ }

		const res = await ingestSOCAlert({
			alert_type: ingestForm.alert_type,
			severity: ingestForm.severity as SOCAlert['severity'],
			user_id: ingestForm.user_id,
			action: ingestForm.action,
			details,
		});

		if (res.ok) {
			ingestResult = `✓ Alert ingested — Risk: ${res.data.departure_risk_score}` +
				(res.data.pattern_matches?.length ? ` | Patterns: ${res.data.pattern_matches.join(', ')}` : '') +
				(res.data.warning ? ` | ⚠ ${res.data.warning}` : '');
			fetchStatus();
		} else {
			ingestResult = `✗ ${res.error.message}`;
		}
	}

	const alertTypes = [
		'vpn_anomaly', 'database_access', 'file_exfiltration', 'email_forwarding',
		'usb_transfer', 'cloud_upload', 'privilege_escalation', 'mfa_fatigue',
	];

	const severities = ['low', 'medium', 'high', 'critical'];
</script>

{#if loading}
	<div class="loading-state">
		<div class="spinner"></div>
		<p>Loading SOC status…</p>
	</div>
{:else if error}
	<div class="error-banner"><span class="error-icon">⚠</span> {error}</div>
{:else if socStatus}

<!-- ── Header Stats ────────────────────────────────── -->
<section class="stat-row">
	<div class="stat-card">
		<div class="stat-value">{socStatus.total_alerts}</div>
		<div class="stat-label">Total Alerts</div>
	</div>
	<div class="stat-card">
		<div class="stat-value primary">{socStatus.pattern_detections}</div>
		<div class="stat-label">Pattern Hits</div>
	</div>
	<div class="stat-card">
		<div class="stat-value warning">{socStatus.high_risk_users.length}</div>
		<div class="stat-label">High-Risk Users</div>
	</div>
	<div class="stat-card">
		<div class="stat-value" class:success={socStatus.status === 'active'}>{socStatus.status}</div>
		<div class="stat-label">Engine Status</div>
	</div>
</section>

<!-- ── Ingest Alert ────────────────────────────────── -->
<section class="panel" style="margin-bottom: 24px;">
	<button class="toggle-btn" onclick={() => showIngest = !showIngest}>
		{showIngest ? '▾' : '▸'} Ingest Test Alert
	</button>

	{#if showIngest}
		<form class="ingest-form" onsubmit={(e) => { e.preventDefault(); submitAlert(); }}>
			<div class="form-row">
				<label>
					<span class="form-label">Alert Type</span>
					<select bind:value={ingestForm.alert_type}>
						{#each alertTypes as t}<option value={t}>{t}</option>{/each}
					</select>
				</label>
				<label>
					<span class="form-label">Severity</span>
					<select bind:value={ingestForm.severity}>
						{#each severities as s}<option value={s}>{s}</option>{/each}
					</select>
				</label>
				<label>
					<span class="form-label">User ID</span>
					<input type="text" bind:value={ingestForm.user_id} placeholder="e.g. jdoe@firm.com" required />
				</label>
			</div>
			<div class="form-row">
				<label style="flex:1">
					<span class="form-label">Action</span>
					<input type="text" bind:value={ingestForm.action} placeholder="login_attempt" />
				</label>
				<label style="flex:2">
					<span class="form-label">Details (JSON)</span>
					<input type="text" bind:value={ingestForm.details} placeholder={'{"ip":"10.0.0.1"}'} />
				</label>
			</div>
			<button type="submit" class="submit-btn">Ingest Alert</button>
			{#if ingestResult}
				<div class="ingest-result" class:success={ingestResult.startsWith('✓')} class:error={ingestResult.startsWith('✗')}>
					{ingestResult}
				</div>
			{/if}
		</form>
	{/if}
</section>

<!-- ── High-Risk Users ─────────────────────────────── -->
<section class="panel" style="margin-bottom: 24px;">
	<h2 class="panel-title">High-Risk Users</h2>
	{#if socStatus.high_risk_users.length > 0}
		<div class="user-table">
			<div class="user-table-header">
				<span>User ID</span>
				<span>Risk Score</span>
				<span>Alerts</span>
				<span></span>
			</div>
			{#each socStatus.high_risk_users as user}
				<a href="/dashboard/soc/users/{user.user_id}" class="user-table-row">
					<span class="user-id-cell">{user.user_id}</span>
					<span class="risk-cell" class:critical={user.risk_score > 75} class:high={user.risk_score > 50}>
						{user.risk_score}
					</span>
					<span>{user.alert_count}</span>
					<span class="view-link">View →</span>
				</a>
			{/each}
		</div>
	{:else}
		<p class="empty-text">No high-risk users detected</p>
	{/if}
</section>

<!-- ── Recent Alerts ───────────────────────────────── -->
<section class="panel">
	<h2 class="panel-title">Recent Alerts</h2>
	{#if socStatus.recent_alerts.length > 0}
		<div class="alert-table">
			{#each socStatus.recent_alerts as alert}
				<div class="alert-table-row">
					<span class="alert-time">{alert.timestamp ? new Date(alert.timestamp).toLocaleString() : '—'}</span>
					<span class="alert-type-cell">{alert.alert_type}</span>
					<span class="sev-badge sev-{alert.severity}">{alert.severity}</span>
					<span class="alert-user-cell">{alert.user_id}</span>
					<span class="alert-action-cell">{alert.action}</span>
				</div>
			{/each}
		</div>
	{:else}
		<p class="empty-text">No recent alerts</p>
	{/if}
</section>

{/if}

<style>
	/* ── Shared ─────────────────────────────────────────── */
	.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 40vh; gap: 16px; color: var(--text-dim); }
	.spinner { width: 32px; height: 32px; border: 3px solid rgba(255,255,255,0.1); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
	.error-banner { background: rgba(255,59,59,0.1); border: 1px solid rgba(255,59,59,0.25); border-radius: 8px; padding: 12px 16px; font-size: 0.85rem; display: flex; align-items: center; gap: 10px; color: var(--primary); }

	.stat-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 24px; }
	.stat-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center; }
	.stat-value { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 700; }
	.stat-value.success { color: var(--success); }
	.stat-value.primary { color: var(--primary); }
	.stat-value.warning { color: var(--warning); }
	.stat-label { font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

	.panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; }
	.panel-title { font-size: 1rem; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
	.panel-title::before { content: ''; width: 3px; height: 16px; background: var(--primary); border-radius: 2px; }
	.empty-text { color: rgba(255,255,255,0.3); font-size: 0.85rem; font-style: italic; }

	/* ── Ingest Form ───────────────────────────────────── */
	.toggle-btn {
		background: none; border: none; color: var(--text); cursor: pointer;
		font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; font-weight: 600;
		padding: 0; transition: color 0.2s;
	}
	.toggle-btn:hover { color: var(--primary); }

	.ingest-form { margin-top: 16px; }
	.form-row { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
	.form-label { display: block; font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
	.ingest-form label { flex: 1; min-width: 180px; }
	.ingest-form input, .ingest-form select {
		width: 100%; padding: 8px 12px;
		background: rgba(255,255,255,0.05); border: 1px solid var(--border);
		border-radius: 6px; color: var(--text); font-size: 0.85rem;
		font-family: 'JetBrains Mono', monospace;
	}
	.ingest-form input:focus, .ingest-form select:focus { border-color: var(--primary); outline: none; }
	.submit-btn {
		padding: 8px 24px; background: rgba(255,59,59,0.15); border: 1px solid rgba(255,59,59,0.3);
		color: var(--text); border-radius: 8px; cursor: pointer; font-size: 0.85rem;
		font-family: 'Inter', sans-serif; transition: all 0.2s;
	}
	.submit-btn:hover { background: rgba(255,59,59,0.3); border-color: var(--primary); }
	.ingest-result {
		margin-top: 12px; padding: 8px 12px; border-radius: 6px;
		font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
	}
	.ingest-result.success { background: rgba(0,255,136,0.08); color: var(--success); }
	.ingest-result.error { background: rgba(255,59,59,0.08); color: var(--primary); }

	/* ── User table ────────────────────────────────────── */
	.user-table { display: flex; flex-direction: column; gap: 4px; }
	.user-table-header {
		display: grid; grid-template-columns: 2fr 1fr 1fr 80px;
		padding: 8px 12px; font-size: 0.72rem; color: var(--text-dim);
		text-transform: uppercase; letter-spacing: 0.5px;
		border-bottom: 1px solid var(--border);
	}
	.user-table-row {
		display: grid; grid-template-columns: 2fr 1fr 1fr 80px;
		padding: 10px 12px; border-radius: 6px;
		text-decoration: none; color: inherit; font-size: 0.85rem;
		transition: background 0.15s;
	}
	.user-table-row:hover { background: rgba(255,255,255,0.04); }
	.user-id-cell { font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }
	.risk-cell { font-family: 'JetBrains Mono', monospace; font-weight: 700; color: var(--warning); }
	.risk-cell.critical { color: var(--primary); }
	.risk-cell.high { color: var(--warning); }
	.view-link { color: var(--primary); font-size: 0.8rem; text-align: right; }

	/* ── Alert table ───────────────────────────────────── */
	.alert-table { display: flex; flex-direction: column; gap: 4px; }
	.alert-table-row {
		display: grid; grid-template-columns: 160px 2fr 80px 1fr 1fr;
		align-items: center; padding: 8px 12px; border-radius: 6px; font-size: 0.82rem; gap: 8px;
	}
	.alert-table-row:nth-child(odd) { background: rgba(255,255,255,0.02); }
	.alert-time { font-size: 0.75rem; color: var(--text-dim); }
	.alert-type-cell { font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; }
	.sev-badge {
		display: inline-block; padding: 1px 8px; border-radius: 8px;
		font-size: 0.7rem; font-weight: 600; text-align: center;
	}
	.sev-critical { background: rgba(255,59,59,0.2); color: var(--primary); }
	.sev-high { background: rgba(255,170,0,0.2); color: var(--warning); }
	.sev-medium { background: rgba(255,255,255,0.08); color: var(--text-dim); }
	.sev-low { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.4); }
	.alert-user-cell { font-size: 0.78rem; color: var(--text-dim); }
	.alert-action-cell { font-size: 0.78rem; color: rgba(255,255,255,0.4); }
</style>
