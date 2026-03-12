<script lang="ts">
	import { onMount } from 'svelte';
	import {
		getImprovementStatus,
		getImprovementMetrics,
		getProposals,
		listPolicies,
		getPolicyDiff,
		getNudges,
		runImprovementCycle,
		approveProposal,
		rejectProposal,
		rollbackPolicy,
	} from '$lib/api/client';
	import type {
		ImprovementStatus,
		DetectionMetrics,
		PolicyProposal,
		PolicyVersion,
		Nudge,
	} from '$lib/api/types';

	// State
	let status: ImprovementStatus | null = $state(null);
	let metrics: DetectionMetrics | null = $state(null);
	let proposals: PolicyProposal[] = $state([]);
	let policies: PolicyVersion[] = $state([]);
	let nudges: Nudge[] = $state([]);
	let loading = $state(true);
	let error = $state('');

	// Diff viewer
	let diffFrom = $state(0);
	let diffTo = $state(0);
	let diffResult: Record<string, unknown> | null = $state(null);
	let diffLoading = $state(false);

	// Action feedback
	let actionMsg = $state('');

	// Active tab
	let activeTab: 'overview' | 'proposals' | 'policies' | 'nudges' = $state('overview');

	onMount(() => {
		fetchAll();
	});

	async function fetchAll() {
		loading = true;
		error = '';
		const [sRes, mRes, pRes, polRes, nRes] = await Promise.all([
			getImprovementStatus(),
			getImprovementMetrics(),
			getProposals(),
			listPolicies(),
			getNudges(),
		]);

		if (sRes.ok) status = sRes.data; else error = sRes.error.message;
		if (mRes.ok) metrics = mRes.data;
		if (pRes.ok) proposals = pRes.data.proposals ?? [];
		if (polRes.ok) policies = polRes.data.versions ?? [];
		if (nRes.ok) nudges = nRes.data.nudges ?? [];
		loading = false;
	}

	async function triggerCycle() {
		actionMsg = 'Running improvement cycle…';
		const res = await runImprovementCycle();
		if (res.ok) {
			actionMsg = '✓ Cycle complete';
			fetchAll();
		} else {
			actionMsg = `✗ ${res.error.message}`;
		}
	}

	async function approve(ver: number) {
		const res = await approveProposal(ver, { analyst_id: 'dashboard_user', notes: 'Approved from dashboard' });
		if (res.ok) { actionMsg = `✓ v${ver} approved`; fetchAll(); }
		else actionMsg = `✗ ${res.error.message}`;
	}

	async function reject(ver: number) {
		const res = await rejectProposal(ver, { analyst_id: 'dashboard_user', notes: 'Rejected from dashboard' });
		if (res.ok) { actionMsg = `✓ v${ver} rejected`; fetchAll(); }
		else actionMsg = `✗ ${res.error.message}`;
	}

	async function rollback(ver: number) {
		const res = await rollbackPolicy(ver, { analyst_id: 'dashboard_user', notes: 'Rollback from dashboard' });
		if (res.ok) { actionMsg = `✓ Rolled back to v${ver}`; fetchAll(); }
		else actionMsg = `✗ ${res.error.message}`;
	}

	async function viewDiff() {
		if (!diffFrom || !diffTo) return;
		diffLoading = true;
		const res = await getPolicyDiff(diffFrom, diffTo);
		if (res.ok) diffResult = res.data.diff;
		else actionMsg = `✗ Diff: ${res.error.message}`;
		diffLoading = false;
	}

	function pct(n: number | undefined): string {
		if (n == null) return '—';
		return (n * 100).toFixed(1) + '%';
	}
</script>

{#if loading}
	<div class="loading-state">
		<div class="spinner"></div>
		<p>Loading Improvement Engine…</p>
	</div>
{:else if error}
	<div class="error-banner"><span>⚠</span> {error}</div>
{:else}

<!-- ── Action banner ───────────────────────────────── -->
{#if actionMsg}
	<div class="action-msg" class:success={actionMsg.startsWith('✓')} class:error={actionMsg.startsWith('✗')}>
		{actionMsg}
		<button class="dismiss-btn" onclick={() => actionMsg = ''}>×</button>
	</div>
{/if}

<!-- ── Tabs ────────────────────────────────────────── -->
<div class="tab-bar">
	{#each (['overview', 'proposals', 'policies', 'nudges'] as const) as tab}
		<button
			class="tab-btn"
			class:active={activeTab === tab}
			onclick={() => activeTab = tab}
		>
			{tab.charAt(0).toUpperCase() + tab.slice(1)}
			{#if tab === 'proposals' && proposals.length > 0}
				<span class="tab-badge">{proposals.length}</span>
			{/if}
			{#if tab === 'nudges' && nudges.length > 0}
				<span class="tab-badge">{nudges.length}</span>
			{/if}
		</button>
	{/each}
</div>

<!-- ═══ Overview Tab ═══════════════════════════════════ -->
{#if activeTab === 'overview'}
	<section class="stat-row">
		<div class="stat-card">
			<div class="stat-value">{status?.active_policy_version ?? '—'}</div>
			<div class="stat-label">Active Policy</div>
		</div>
		<div class="stat-card">
			<div class="stat-value">{status?.total_feedback ?? 0}</div>
			<div class="stat-label">Feedback Items</div>
		</div>
		<div class="stat-card">
			<div class="stat-value warning">{status?.pending_proposals ?? 0}</div>
			<div class="stat-label">Pending Proposals</div>
		</div>
		<div class="stat-card">
			<div class="stat-value">{status?.cycle_count ?? 0}</div>
			<div class="stat-label">Cycles</div>
		</div>
	</section>

	<!-- Detection Metrics -->
	{#if metrics}
		<div class="panel" style="margin-bottom: 24px;">
			<h2 class="panel-title">Detection Quality Metrics</h2>
			<div class="metrics-grid">
				<div class="metric-item">
					<div class="metric-val success">{pct(metrics.metrics?.precision)}</div>
					<div class="metric-lbl">Precision</div>
				</div>
				<div class="metric-item">
					<div class="metric-val success">{pct(metrics.metrics?.recall)}</div>
					<div class="metric-lbl">Recall</div>
				</div>
				<div class="metric-item">
					<div class="metric-val">{pct(metrics.metrics?.f1_score)}</div>
					<div class="metric-lbl">F1 Score</div>
				</div>
				<div class="metric-item">
					<div class="metric-val warning">{pct(metrics.metrics?.noise_ratio)}</div>
					<div class="metric-lbl">Noise Ratio</div>
				</div>
			</div>
			<div class="composite-score">
				<span>Composite Score</span>
				<span class="score-val">{metrics.score?.toFixed(2) ?? '—'}</span>
			</div>
		</div>
	{/if}

	<button class="action-btn" onclick={triggerCycle}>
		⟳ Run Improvement Cycle
	</button>

<!-- ═══ Proposals Tab ══════════════════════════════════ -->
{:else if activeTab === 'proposals'}
	{#if proposals.length === 0}
		<p class="empty-text">No pending proposals. Run an improvement cycle to generate candidates.</p>
	{:else}
		<div class="proposals-list">
			{#each proposals as p}
				<div class="proposal-card">
					<div class="proposal-header">
						<span class="proposal-ver">v{p.version}</span>
						<span class="proposal-status status-{p.status}">{p.status}</span>
					</div>
					{#if p.created_at}
						<div class="proposal-time">{new Date(p.created_at).toLocaleString()}</div>
					{/if}
					{#if p.changes}
						<div class="proposal-changes">{p.changes}</div>
					{/if}
					<div class="proposal-actions">
						<button class="approve-btn" onclick={() => approve(p.version)}>✓ Approve</button>
						<button class="reject-btn" onclick={() => reject(p.version)}>✗ Reject</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}

<!-- ═══ Policies Tab ═══════════════════════════════════ -->
{:else if activeTab === 'policies'}
	{#if policies.length === 0}
		<p class="empty-text">No policy versions recorded yet.</p>
	{:else}
		<div class="policy-list">
			{#each policies as pol}
				<div class="policy-row" class:active-pol={pol.active}>
					<span class="pol-ver">v{pol.version}</span>
					{#if pol.active}<span class="active-badge">ACTIVE</span>{/if}
					<span class="pol-time">{pol.created_at ? new Date(pol.created_at).toLocaleString() : '—'}</span>
					<button class="rollback-btn" onclick={() => rollback(pol.version)}>Rollback</button>
				</div>
			{/each}
		</div>

		<!-- Diff viewer -->
		<div class="panel" style="margin-top: 24px;">
			<h2 class="panel-title">Policy Diff</h2>
			<div class="diff-controls">
				<label>
					<span class="form-label">From</span>
					<input type="number" bind:value={diffFrom} min="1" />
				</label>
				<label>
					<span class="form-label">To</span>
					<input type="number" bind:value={diffTo} min="1" />
				</label>
				<button class="action-btn" onclick={viewDiff} disabled={diffLoading}>
					{diffLoading ? 'Loading…' : 'View Diff'}
				</button>
			</div>
			{#if diffResult}
				<pre class="diff-output">{JSON.stringify(diffResult, null, 2)}</pre>
			{/if}
		</div>
	{/if}

<!-- ═══ Nudges Tab ═════════════════════════════════════ -->
{:else if activeTab === 'nudges'}
	{#if nudges.length === 0}
		<p class="empty-text">No active nudges — the system has no improvement suggestions right now.</p>
	{:else}
		<div class="nudge-list">
			{#each nudges as n}
				<div class="nudge-card">
					<div class="nudge-header">
						<span class="nudge-cat">{n.category}</span>
						<span class="nudge-priority">P{n.priority}</span>
					</div>
					<div class="nudge-msg">{n.message}</div>
				</div>
			{/each}
		</div>
	{/if}
{/if}

{/if}

<style>
	/* ── Shared ─────────────────────────────────────────── */
	.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 40vh; gap: 16px; color: var(--text-dim); }
	.spinner { width: 32px; height: 32px; border: 3px solid rgba(255,255,255,0.1); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
	.error-banner { background: rgba(255,59,59,0.1); border: 1px solid rgba(255,59,59,0.25); border-radius: 8px; padding: 12px 16px; font-size: 0.85rem; display: flex; align-items: center; gap: 10px; color: var(--primary); margin-bottom: 20px; }
	.empty-text { color: rgba(255,255,255,0.3); font-size: 0.85rem; font-style: italic; padding: 40px 0; text-align: center; }

	/* Action banner */
	.action-msg {
		padding: 10px 16px; border-radius: 8px; margin-bottom: 20px;
		font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;
		display: flex; align-items: center; justify-content: space-between;
	}
	.action-msg.success { background: rgba(0,255,136,0.08); color: var(--success); }
	.action-msg.error { background: rgba(255,59,59,0.08); color: var(--primary); }
	.dismiss-btn { background: none; border: none; color: inherit; cursor: pointer; font-size: 1.1rem; opacity: 0.5; }
	.dismiss-btn:hover { opacity: 1; }

	/* ── Tabs ──────────────────────────────────────────── */
	.tab-bar {
		display: flex; gap: 4px; margin-bottom: 24px;
		border-bottom: 1px solid var(--border); padding-bottom: 0;
	}
	.tab-btn {
		padding: 10px 20px; background: none; border: none; border-bottom: 2px solid transparent;
		color: var(--text-dim); cursor: pointer; font-size: 0.88rem;
		font-family: 'Inter', sans-serif; transition: all 0.2s;
		display: flex; align-items: center; gap: 8px;
	}
	.tab-btn:hover { color: var(--text); }
	.tab-btn.active {
		color: var(--primary); border-bottom-color: var(--primary); font-weight: 600;
	}
	.tab-badge {
		background: var(--primary); color: #fff;
		font-size: 0.65rem; font-weight: 700;
		padding: 1px 6px; border-radius: 10px;
	}

	/* ── Stat Row ──────────────────────────────────────── */
	.stat-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px; margin-bottom: 24px; }
	.stat-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; text-align: center; }
	.stat-value { font-family: 'JetBrains Mono', monospace; font-size: 1.6rem; font-weight: 700; }
	.stat-value.warning { color: var(--warning); }
	.stat-label { font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }

	/* ── Panel ─────────────────────────────────────────── */
	.panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; }
	.panel-title { font-size: 1rem; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
	.panel-title::before { content: ''; width: 3px; height: 16px; background: var(--primary); border-radius: 2px; }

	.metrics-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
	.metric-item { text-align: center; }
	.metric-val { font-family: 'JetBrains Mono', monospace; font-size: 1.4rem; font-weight: 700; }
	.metric-val.success { color: var(--success); }
	.metric-val.warning { color: var(--warning); }
	.metric-lbl { font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 2px; }
	.composite-score { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding: 12px 16px; background: rgba(255,255,255,0.03); border-radius: 8px; font-size: 0.88rem; }
	.score-val { font-family: 'JetBrains Mono', monospace; font-weight: 700; color: var(--success); }

	.action-btn {
		padding: 10px 24px; background: rgba(255,59,59,0.15); border: 1px solid rgba(255,59,59,0.3);
		color: var(--text); border-radius: 8px; cursor: pointer; font-size: 0.88rem;
		font-family: 'Inter', sans-serif; font-weight: 600; transition: all 0.2s;
	}
	.action-btn:hover { background: rgba(255,59,59,0.3); border-color: var(--primary); }
	.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }

	/* ── Proposals ─────────────────────────────────────── */
	.proposals-list { display: flex; flex-direction: column; gap: 16px; }
	.proposal-card {
		background: var(--bg-card); border: 1px solid var(--border);
		border-radius: 12px; padding: 20px;
	}
	.proposal-header { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
	.proposal-ver { font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; }
	.proposal-status {
		padding: 2px 10px; border-radius: 12px;
		font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
	}
	.status-pending { background: rgba(255,170,0,0.15); color: var(--warning); }
	.status-approved { background: rgba(0,255,136,0.12); color: var(--success); }
	.status-rejected { background: rgba(255,59,59,0.12); color: var(--primary); }
	.proposal-time { font-size: 0.78rem; color: var(--text-dim); margin-bottom: 8px; }
	.proposal-changes {
		font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
		padding: 12px; background: rgba(255,255,255,0.03); border-radius: 6px;
		margin-bottom: 12px; white-space: pre-wrap;
	}
	.proposal-actions { display: flex; gap: 10px; }
	.approve-btn {
		padding: 6px 16px; background: rgba(0,255,136,0.12); border: 1px solid rgba(0,255,136,0.3);
		color: var(--success); border-radius: 6px; cursor: pointer; font-size: 0.82rem; transition: all 0.2s;
	}
	.approve-btn:hover { background: rgba(0,255,136,0.25); }
	.reject-btn {
		padding: 6px 16px; background: rgba(255,59,59,0.1); border: 1px solid rgba(255,59,59,0.25);
		color: var(--primary); border-radius: 6px; cursor: pointer; font-size: 0.82rem; transition: all 0.2s;
	}
	.reject-btn:hover { background: rgba(255,59,59,0.2); }

	/* ── Policies ──────────────────────────────────────── */
	.policy-list { display: flex; flex-direction: column; gap: 4px; }
	.policy-row {
		display: flex; align-items: center; gap: 12px;
		padding: 12px 16px; border-radius: 8px;
		background: var(--bg-card); border: 1px solid var(--border);
	}
	.policy-row.active-pol { border-color: rgba(0,255,136,0.3); }
	.pol-ver { font-family: 'JetBrains Mono', monospace; font-weight: 700; min-width: 48px; }
	.active-badge {
		background: rgba(0,255,136,0.15); color: var(--success);
		padding: 2px 8px; border-radius: 8px;
		font-size: 0.65rem; font-weight: 700; letter-spacing: 1px;
	}
	.pol-time { flex: 1; font-size: 0.78rem; color: var(--text-dim); }
	.rollback-btn {
		padding: 4px 12px; background: none; border: 1px solid var(--border);
		color: var(--text-dim); border-radius: 6px; cursor: pointer; font-size: 0.78rem;
		transition: all 0.2s;
	}
	.rollback-btn:hover { border-color: var(--warning); color: var(--warning); }

	/* ── Diff ──────────────────────────────────────────── */
	.diff-controls {
		display: flex; align-items: flex-end; gap: 12px; margin-bottom: 16px;
	}
	.diff-controls label { flex: 0; }
	.form-label { display: block; font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
	.diff-controls input {
		width: 80px; padding: 8px; background: rgba(255,255,255,0.05); border: 1px solid var(--border);
		border-radius: 6px; color: var(--text); font-family: 'JetBrains Mono', monospace; font-size: 0.88rem;
	}
	.diff-controls input:focus { border-color: var(--primary); outline: none; }
	.diff-output {
		background: rgba(0,0,0,0.3); border: 1px solid var(--border);
		border-radius: 8px; padding: 16px; font-family: 'JetBrains Mono', monospace;
		font-size: 0.78rem; overflow-x: auto; max-height: 400px;
		white-space: pre-wrap; line-height: 1.6;
	}

	/* ── Nudges ────────────────────────────────────────── */
	.nudge-list { display: flex; flex-direction: column; gap: 12px; }
	.nudge-card {
		background: var(--bg-card); border: 1px solid rgba(255,170,0,0.2);
		border-radius: 12px; padding: 16px;
	}
	.nudge-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
	.nudge-cat {
		font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;
		color: var(--warning);
	}
	.nudge-priority {
		font-family: 'JetBrains Mono', monospace; font-size: 0.72rem;
		color: var(--text-dim); font-weight: 600;
	}
	.nudge-msg { font-size: 0.88rem; line-height: 1.5; }
</style>
