<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { getUserRisk, submitFeedback } from '$lib/api/client';
	import type { UserRiskProfile, FeedbackRequest } from '$lib/api/types';

	let userId = $derived($page.params.id);
	let profile: UserRiskProfile | null = $state(null);
	let loading = $state(true);
	let error = $state('');

	// Feedback form
	let showFeedback = $state(false);
	let feedbackForm = $state<FeedbackRequest>({
		feedback_type: 'alert_correct',
		analyst_id: 'analyst_1',
		notes: '',
	});
	let feedbackResult = $state<string | null>(null);

	$effect(() => {
		if (userId) fetchProfile();
	});

	async function fetchProfile() {
		if (!userId) return;
		loading = true;
		const res = await getUserRisk(userId);
		if (res.ok) {
			profile = res.data;
			error = '';
		} else {
			error = res.error.message;
		}
		loading = false;
	}

	async function sendFeedback() {
		const res = await submitFeedback(feedbackForm);
		if (res.ok) {
			feedbackResult = `✓ Feedback submitted (${res.data.feedback_id})`;
			showFeedback = false;
		} else {
			feedbackResult = `✗ ${res.error.message}`;
		}
	}

	function riskColor(score: number): string {
		if (score > 75) return 'var(--primary)';
		if (score > 50) return 'var(--warning)';
		return 'var(--success)';
	}
</script>

<a href="/dashboard/soc" class="back-link">← Back to SOC</a>

{#if loading}
	<div class="loading-state">
		<div class="spinner"></div>
		<p>Loading risk profile for {userId}…</p>
	</div>
{:else if error}
	<div class="error-banner"><span>⚠</span> {error}</div>
{:else if profile}

<div class="profile-header">
	<div class="profile-id">{profile.user_id}</div>
	<div class="profile-risk" style="color: {riskColor(profile.risk_score)}">
		Risk Score: {profile.risk_score}
	</div>
</div>

<!-- ── Risk Meter ──────────────────────────────────── -->
<div class="risk-meter">
	<div class="risk-fill" style="width: {Math.min(profile.risk_score, 100)}%; background: {riskColor(profile.risk_score)}"></div>
</div>

<!-- ── Recommendations ─────────────────────────────── -->
{#if profile.recommendations?.length}
	<section class="panel" style="margin-bottom: 24px;">
		<h2 class="panel-title">Recommendations</h2>
		<ul class="rec-list">
			{#each profile.recommendations as rec}
				<li>{rec}</li>
			{/each}
		</ul>
	</section>
{/if}

<!-- ── Alert History ───────────────────────────────── -->
<section class="panel" style="margin-bottom: 24px;">
	<h2 class="panel-title">Alert History</h2>
	{#if profile.alert_history?.length}
		<div class="alert-timeline">
			{#each profile.alert_history as alert}
				<div class="timeline-item">
					<div class="tl-dot sev-dot-{alert.severity}"></div>
					<div class="tl-content">
						<div class="tl-header">
							<span class="tl-type">{alert.alert_type}</span>
							<span class="sev-badge sev-{alert.severity}">{alert.severity}</span>
						</div>
						<div class="tl-time">{alert.timestamp ? new Date(alert.timestamp).toLocaleString() : '—'}</div>
						<div class="tl-action">Action: {alert.action}</div>
						{#if Object.keys(alert.details || {}).length > 0}
							<div class="tl-details">{JSON.stringify(alert.details)}</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<p class="empty-text">No alerts recorded</p>
	{/if}
</section>

<!-- ── Submit Feedback ─────────────────────────────── -->
<section class="panel">
	<button class="toggle-btn" onclick={() => showFeedback = !showFeedback}>
		{showFeedback ? '▾' : '▸'} Submit Analyst Feedback
	</button>

	{#if showFeedback}
		<form class="feedback-form" onsubmit={(e) => { e.preventDefault(); sendFeedback(); }}>
			<div class="form-row">
				<label>
					<span class="form-label">Feedback Type</span>
					<select bind:value={feedbackForm.feedback_type}>
						<option value="alert_correct">Correct</option>
						<option value="alert_noisy">Noisy (False Positive)</option>
						<option value="alert_missed">Missed (False Negative)</option>
						<option value="mis_categorized">Mis-categorized</option>
						<option value="near_miss">Near Miss</option>
						<option value="duplicate">Duplicate</option>
					</select>
				</label>
				<label>
					<span class="form-label">Analyst ID</span>
					<input type="text" bind:value={feedbackForm.analyst_id} />
				</label>
			</div>
			<label style="display:block; margin-bottom: 12px;">
				<span class="form-label">Notes</span>
				<textarea bind:value={feedbackForm.notes} rows="3" placeholder="Optional notes…"></textarea>
			</label>
			<button type="submit" class="submit-btn">Submit Feedback</button>
		</form>
	{/if}

	{#if feedbackResult}
		<div class="feedback-result" class:success={feedbackResult.startsWith('✓')} class:error={feedbackResult.startsWith('✗')}>
			{feedbackResult}
		</div>
	{/if}
</section>

{/if}

<style>
	.back-link {
		display: inline-block; margin-bottom: 20px;
		color: var(--text-dim); text-decoration: none; font-size: 0.85rem;
		transition: color 0.2s;
	}
	.back-link:hover { color: var(--primary); }

	.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 40vh; gap: 16px; color: var(--text-dim); }
	.spinner { width: 32px; height: 32px; border: 3px solid rgba(255,255,255,0.1); border-top-color: var(--primary); border-radius: 50%; animation: spin 0.8s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
	.error-banner { background: rgba(255,59,59,0.1); border: 1px solid rgba(255,59,59,0.25); border-radius: 8px; padding: 12px 16px; font-size: 0.85rem; display: flex; align-items: center; gap: 10px; color: var(--primary); }

	.profile-header {
		display: flex; align-items: center; justify-content: space-between;
		margin-bottom: 16px;
	}
	.profile-id {
		font-family: 'JetBrains Mono', monospace;
		font-size: 1.5rem; font-weight: 700;
	}
	.profile-risk {
		font-family: 'JetBrains Mono', monospace;
		font-size: 1.2rem; font-weight: 700;
	}

	.risk-meter {
		height: 8px; background: rgba(255,255,255,0.08);
		border-radius: 4px; overflow: hidden; margin-bottom: 28px;
	}
	.risk-fill { height: 100%; border-radius: 4px; transition: width 0.5s ease; }

	.panel { background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 24px; }
	.panel-title { font-size: 1rem; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; gap: 10px; }
	.panel-title::before { content: ''; width: 3px; height: 16px; background: var(--primary); border-radius: 2px; }
	.empty-text { color: rgba(255,255,255,0.3); font-size: 0.85rem; font-style: italic; }

	.rec-list {
		list-style: none; padding: 0;
	}
	.rec-list li {
		padding: 8px 12px; border-left: 3px solid var(--success);
		margin-bottom: 8px; font-size: 0.88rem;
		background: rgba(0,255,136,0.03); border-radius: 0 6px 6px 0;
	}

	/* Timeline */
	.alert-timeline { display: flex; flex-direction: column; gap: 0; padding-left: 12px; }
	.timeline-item {
		display: flex; gap: 14px; padding: 12px 0;
		border-left: 2px solid rgba(255,255,255,0.08); padding-left: 16px;
		position: relative;
	}
	.tl-dot {
		width: 10px; height: 10px; border-radius: 50%;
		position: absolute; left: -6px; top: 16px;
		background: var(--text-dim);
	}
	.sev-dot-critical { background: var(--primary); box-shadow: 0 0 8px rgba(255,59,59,0.4); }
	.sev-dot-high { background: var(--warning); }
	.sev-dot-medium { background: var(--text-dim); }
	.sev-dot-low { background: rgba(255,255,255,0.3); }
	.tl-content { flex: 1; }
	.tl-header { display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }
	.tl-type { font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 600; }
	.tl-time { font-size: 0.75rem; color: var(--text-dim); }
	.tl-action { font-size: 0.82rem; color: var(--text-dim); margin-top: 4px; }
	.tl-details { font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: rgba(255,255,255,0.3); margin-top: 4px; word-break: break-all; }

	.sev-badge {
		display: inline-block; padding: 1px 8px; border-radius: 8px;
		font-size: 0.7rem; font-weight: 600;
	}
	.sev-critical { background: rgba(255,59,59,0.2); color: var(--primary); }
	.sev-high { background: rgba(255,170,0,0.2); color: var(--warning); }
	.sev-medium { background: rgba(255,255,255,0.08); color: var(--text-dim); }
	.sev-low { background: rgba(255,255,255,0.05); color: rgba(255,255,255,0.4); }

	/* Feedback form */
	.toggle-btn { background: none; border: none; color: var(--text); cursor: pointer; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; font-weight: 600; padding: 0; }
	.toggle-btn:hover { color: var(--primary); }
	.feedback-form { margin-top: 16px; }
	.form-row { display: flex; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
	.form-label { display: block; font-size: 0.72rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
	.feedback-form label { flex: 1; min-width: 180px; }
	.feedback-form input, .feedback-form select, .feedback-form textarea {
		width: 100%; padding: 8px 12px; background: rgba(255,255,255,0.05); border: 1px solid var(--border);
		border-radius: 6px; color: var(--text); font-size: 0.85rem; font-family: 'JetBrains Mono', monospace; resize: vertical;
	}
	.feedback-form input:focus, .feedback-form select:focus, .feedback-form textarea:focus { border-color: var(--primary); outline: none; }
	.submit-btn {
		padding: 8px 24px; background: rgba(255,59,59,0.15); border: 1px solid rgba(255,59,59,0.3);
		color: var(--text); border-radius: 8px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s;
	}
	.submit-btn:hover { background: rgba(255,59,59,0.3); border-color: var(--primary); }
	.feedback-result { margin-top: 12px; padding: 8px 12px; border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; }
	.feedback-result.success { background: rgba(0,255,136,0.08); color: var(--success); }
	.feedback-result.error { background: rgba(255,59,59,0.08); color: var(--primary); }
</style>
