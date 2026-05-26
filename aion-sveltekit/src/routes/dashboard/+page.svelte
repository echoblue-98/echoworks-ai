<script lang="ts">
	// ═══════════════════════════════════════════════════════════
	// AION OS — Sovereign Operator Dashboard (4-tile)
	// ═══════════════════════════════════════════════════════════
	// Four tiles. Equal weight. No charts on the main page.
	// Binary health. Since-visit volume. RSI state. Audit drawer.
	//
	// Subtraction as efficiency. Optimize for what does not exist.
	// The operator surface IS the audit surface.
	//
	// Engineer telemetry (precision/recall/F1) lives at /dashboard/metrics
	// and is reachable from the footer only.
	// ═══════════════════════════════════════════════════════════

	import { onMount } from 'svelte';
	import {
		getHealth,
		getImprovementStatus,
		getAuditLogs,
		sovereignReason,
		sovereignReasonStream,
		type ReasonResponse,
	} from '$lib/api/client';
	import type {
		HealthResponse,
		ImprovementStatus,
		AuditLogsResponse,
	} from '$lib/api/types';

	const LAST_VISIT_KEY = 'aion_last_visit_iso';

	// Reactive state — only what the four tiles need
	let health: HealthResponse | null = $state(null);
	let healthOk = $state(false);
	let improvement: ImprovementStatus | null = $state(null);
	let audit: AuditLogsResponse | null = $state(null);
	let lastVisitIso = $state<string | null>(null);
	let loading = $state(true);

	// Derived tile values
	let volumeSinceVisit = $derived(computeVolume(audit, lastVisitIso));
	let policyVersion = $derived(improvement?.active_policy_version ?? null);
	let pendingProposals = $derived(improvement?.pending_proposals ?? 0);
	let totalFeedback = $derived(improvement?.total_feedback ?? 0);

	onMount(() => {
		// Capture prior visit BEFORE overwriting — that's what "since-visit" is.
		if (typeof window !== 'undefined') {
			lastVisitIso = localStorage.getItem(LAST_VISIT_KEY);
			localStorage.setItem(LAST_VISIT_KEY, new Date().toISOString());
		}

		fetchAll();
		const interval = setInterval(fetchAll, 15_000);
		return () => clearInterval(interval);
	});

	async function fetchAll() {
		const [hRes, impRes, audRes] = await Promise.all([
			getHealth(),
			getImprovementStatus(),
			getAuditLogs({ limit: 200 }),
		]);

		if (hRes.ok) {
			health = hRes.data;
			healthOk = hRes.data?.status === 'operational';
		} else {
			healthOk = false;
		}
		if (impRes.ok) improvement = impRes.data;
		if (audRes.ok) audit = audRes.data;

		loading = false;
	}

	function computeVolume(
		a: AuditLogsResponse | null,
		sinceIso: string | null,
	): number {
		if (!a?.logs) return 0;
		if (!sinceIso) return a.logs.length;
		const sinceMs = new Date(sinceIso).getTime();
		if (Number.isNaN(sinceMs)) return a.logs.length;
		return a.logs.filter((log: any) => {
			const ts = log?.timestamp ?? log?.ts;
			if (!ts) return false;
			const ms = new Date(ts).getTime();
			return !Number.isNaN(ms) && ms >= sinceMs;
		}).length;
	}

	function fmtSinceVisit(iso: string | null): string {
		if (!iso) return 'first visit';
		const d = new Date(iso);
		if (Number.isNaN(d.getTime())) return 'first visit';
		return d.toLocaleString();
	}

	function recentEvents(a: AuditLogsResponse | null, n = 5): any[] {
		if (!a?.logs) return [];
		return a.logs.slice(0, n);
	}

	// ── Sovereign inference panel ───────────────────────────────
	// ICP demo presets — pick once, demo cleanly. Default is the sovereign-architecture one-liner.
	const presetPrompts: { label: string; prompt: string }[] = [
		{
			label: 'Default — why sovereign AI',
			prompt: 'Explain in one sentence why a regulated firm should run AI on-premises.'
		},
		{
			label: 'Legal — departing associate exfiltration',
			prompt: "An associate accessed the client list, downloaded 4GB from our document system after hours, and updated their LinkedIn profile this week. What's the partner-level response sequence?"
		},
		{
			label: 'Legal — conflict-of-interest check',
			prompt: 'A prospective client wants to retain us against a counterparty we represented in an unrelated matter eighteen months ago. Walk through the conflict-of-interest analysis a partner should run before accepting the engagement.'
		},
		{
			label: 'Legal — privilege review checklist',
			prompt: 'Give me a privilege-review checklist a senior associate should apply to a deposition transcript before producing it in discovery.'
		},
		{
			label: 'Healthcare — HIPAA vendor breach',
			prompt: 'A third-party billing vendor just notified us they suffered a ransomware incident affecting systems that held PHI for our patients. What is the partner-level response sequence in the first 72 hours?'
		}
	];
	let selectedPreset = $state(0);
	let reasonPrompt = $state(presetPrompts[0].prompt);
	let reasonResult: ReasonResponse | null = $state(null);
	let reasonError = $state<string | null>(null);
	let reasonPending = $state(false);
	let streamingText = $state(''); // tokens render here as they arrive

	function applyPreset(idx: number) {
		selectedPreset = idx;
		reasonPrompt = presetPrompts[idx].prompt;
		reasonResult = null;
		reasonError = null;
		streamingText = '';
	}

	async function runReason() {
		if (reasonPending || !reasonPrompt.trim()) return;
		reasonPending = true;
		reasonError = null;
		reasonResult = null;
		streamingText = '';

		const handle = sovereignReasonStream(
			reasonPrompt.trim(),
			(tok) => { streamingText += tok; },
			(meta) => { reasonResult = meta; },
			(msg) => { reasonError = msg; },
			2000,
			0.2,
		);
		await handle.done;
		reasonPending = false;
	}
</script>

{#if loading}
	<div class="loading-state">
		<p>Connecting…</p>
	</div>
{:else}

<!-- Sovereign brand header — identity + live sovereignty status before any click -->
<header class="sov-header">
	<div class="sov-brand">
		<span class="sov-mark">◈</span>
		<span class="sov-title">AION OS</span>
		<span class="sov-sub">Sovereign Console</span>
	</div>
	<div class="sov-status">
		<span class="sov-pill sov-pill-ok">
			<span class="sov-dot"></span>
			provider: <strong>{reasonResult?.provider ?? 'ollama'}</strong>
		</span>
		<span class="sov-pill sov-pill-ok">
			<span class="sov-dot"></span>
			model: <strong>{reasonResult?.model ?? 'qwen2.5:7b'}</strong>
		</span>
		<span class="sov-pill sov-pill-block">
			<span class="sov-dot"></span>
			frontier-lab egress: <strong>BLOCKED</strong>
		</span>
		<span class="sov-pill sov-pill-sov">
			<span class="sov-dot"></span>
			sovereign: <strong>✓</strong>
		</span>
	</div>
</header>

<!-- Four tiles. Equal weight. -->
<section class="tile-grid">

	<!-- ── Tile 1: HEALTH (binary) ─────────────────── -->
	<a href="/dashboard/improvement" class="tile" class:tile-ok={healthOk} class:tile-bad={!healthOk}>
		<div class="tile-label">Health</div>
		<div class="tile-glyph">{healthOk ? '✓' : '✗'}</div>
		<div class="tile-sub">
			{healthOk ? 'operational' : 'attention required'}
			{#if policyVersion !== null}
				<span class="tile-meta">policy v{policyVersion}</span>
			{/if}
		</div>
	</a>

	<!-- ── Tile 2: VOLUME (since-visit) ────────────── -->
	<a href="#audit" class="tile">
		<div class="tile-label">Volume</div>
		<div class="tile-glyph">{volumeSinceVisit}</div>
		<div class="tile-sub">
			events since your last visit
			<span class="tile-meta">prior: {fmtSinceVisit(lastVisitIso)}</span>
		</div>
	</a>

	<!-- ── Tile 3: RSI (improvement engine) ────────── -->
	<a href="/dashboard/improvement" class="tile">
		<div class="tile-label">RSI</div>
		<div class="tile-glyph">{pendingProposals}</div>
		<div class="tile-sub">
			pending proposals for your review
			<span class="tile-meta">{totalFeedback} feedback items captured</span>
		</div>
	</a>

	<!-- ── Tile 4: AUDIT DRAWER (preview) ──────────── -->
	<a href="/dashboard/soc" class="tile tile-audit" id="audit">
		<div class="tile-label">Audit</div>
		<div class="tile-glyph audit-count">{audit?.count ?? 0}</div>
		<div class="tile-sub">
			events recorded · click for full drawer
		</div>
	</a>
</section>

<!-- Sovereign inference proof — type a prompt, get a local model response.
     No frontier-lab egress. Latency + tokens/sec exposed for verification. -->
<section class="reason-panel">
	<div class="drawer-header">
		<h2>Sovereign inference</h2>
		<span class="reason-meta-hint">local LLM · no frontier-lab egress</span>
	</div>

	<div class="reason-preset-row">
		<label class="reason-preset-label" for="reason-preset">demo scenario</label>
		<select
			id="reason-preset"
			class="reason-preset"
			value={selectedPreset}
			onchange={(e) => applyPreset(Number((e.target as HTMLSelectElement).value))}
			disabled={reasonPending}
		>
			{#each presetPrompts as p, i}
				<option value={i}>{p.label}</option>
			{/each}
		</select>
	</div>

	<div class="reason-input-row">
		<textarea
			class="reason-input"
			bind:value={reasonPrompt}
			rows="3"
			placeholder="Ask anything — runs on this box, never leaves."
			disabled={reasonPending}
		></textarea>
		<button class="reason-btn" onclick={runReason} disabled={reasonPending || !reasonPrompt.trim()}>
			{reasonPending ? 'thinking…' : 'reason'}
		</button>
	</div>

	{#if reasonError}
		<div class="reason-error">{reasonError}</div>
	{:else if streamingText || reasonResult}
		<div class="reason-output">{reasonResult?.response ?? streamingText}{#if reasonPending}<span class="reason-cursor">█</span>{/if}</div>
		{#if reasonResult}
			<div class="reason-meta">
				<span>provider: <strong>{reasonResult.provider}</strong></span>
				<span>model: <strong>{reasonResult.model}</strong></span>
				<span>latency: <strong>{reasonResult.latency_ms} ms</strong></span>
				<span>tokens: <strong>{reasonResult.tokens}</strong> ({reasonResult.tokens_per_sec} tok/s)</span>
				<span class="reason-sov">sovereign: <strong>{reasonResult.sovereign ? '✓' : '✗'}</strong></span>
			</div>
		{:else}
			<div class="reason-meta"><span class="reason-streaming-hint">streaming from local model…</span></div>
		{/if}
	{:else}
		<div class="reason-placeholder">Press <em>reason</em> to call the local model. Watch tokens stream live — this is the box, not a cloud API.</div>
	{/if}
</section>

<!-- Audit drawer — append-only event stream, the operator's full system memory -->
<section class="audit-drawer">
	<div class="drawer-header">
		<h2>Audit drawer</h2>
		<a href="/dashboard/soc" class="drawer-link">open full →</a>
	</div>
	{#if recentEvents(audit, 10).length === 0}
		<p class="empty-text">No events recorded.</p>
	{:else}
		<div class="event-list">
			{#each recentEvents(audit, 10) as evt}
				<div class="event-row">
					<span class="event-time">{evt?.timestamp ?? evt?.ts ?? '—'}</span>
					<span class="event-type">{evt?.event_type ?? evt?.type ?? 'event'}</span>
					<span class="event-actor">{evt?.user_id ?? evt?.actor ?? 'system'}</span>
				</div>
			{/each}
		</div>
	{/if}
</section>

{/if}

<style>
	/* ── Bloomberg-terminal aesthetic ──────────────────
	   Black background, monospace, single accent for OK.
	   No gradients. No animation. No chrome. */

	.loading-state {
		min-height: 40vh;
		display: flex;
		align-items: center;
		justify-content: center;
		color: rgba(255,255,255,0.5);
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.85rem;
	}

	/* ── Tile grid: 4 equal tiles ──────────────────── */
	.tile-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 1px;
		background: rgba(255,255,255,0.06);
		border: 1px solid rgba(255,255,255,0.06);
		margin-bottom: 32px;
	}
	@media (max-width: 1100px) {
		.tile-grid { grid-template-columns: repeat(2, 1fr); }
	}
	@media (max-width: 600px) {
		.tile-grid { grid-template-columns: 1fr; }
	}

	.tile {
		background: #050508;
		padding: 28px 24px;
		display: flex;
		flex-direction: column;
		gap: 10px;
		text-decoration: none;
		color: inherit;
		min-height: 180px;
	}
	.tile:hover { background: #0a0a10; }

	.tile-label {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.72rem;
		text-transform: uppercase;
		letter-spacing: 2px;
		color: rgba(255,255,255,0.5);
	}

	.tile-glyph {
		font-family: 'JetBrains Mono', monospace;
		font-size: 3.2rem;
		font-weight: 600;
		line-height: 1;
		color: #fff;
	}

	.tile-ok .tile-glyph { color: #4ade80; }
	.tile-bad .tile-glyph { color: #f87171; }

	.tile-sub {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.78rem;
		color: rgba(255,255,255,0.65);
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin-top: auto;
	}

	.tile-meta {
		font-size: 0.7rem;
		color: rgba(255,255,255,0.4);
	}

	/* ── Audit drawer (append-only event stream) ───── */
	.audit-drawer {
		background: #050508;
		border: 1px solid rgba(255,255,255,0.06);
		padding: 24px;
	}

	.drawer-header {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		margin-bottom: 16px;
	}

	.drawer-header h2 {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.78rem;
		text-transform: uppercase;
		letter-spacing: 2px;
		color: rgba(255,255,255,0.5);
		margin: 0;
		font-weight: 600;
	}

	.drawer-link {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.75rem;
		color: rgba(255,255,255,0.6);
		text-decoration: none;
	}
	.drawer-link:hover { color: #fff; }

	.event-list {
		display: flex;
		flex-direction: column;
	}

	.event-row {
		display: grid;
		grid-template-columns: 200px 1fr 1fr;
		gap: 16px;
		padding: 10px 0;
		border-bottom: 1px solid rgba(255,255,255,0.04);
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.78rem;
		color: rgba(255,255,255,0.75);
	}
	.event-row:last-child { border-bottom: none; }

	.event-time { color: rgba(255,255,255,0.45); }
	.event-type { color: rgba(255,255,255,0.85); }
	.event-actor { color: rgba(255,255,255,0.55); text-align: right; }

	.empty-text {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.78rem;
		color: rgba(255,255,255,0.4);
	}

	/* ── Sovereign inference panel ────────────────── */
	.reason-panel {
		background: #050508;
		border: 1px solid rgba(255,255,255,0.06);
		padding: 24px;
		margin-bottom: 32px;
	}

	.reason-meta-hint {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.7rem;
		color: rgba(74, 222, 128, 0.7);
		letter-spacing: 1px;
	}

	.reason-preset-row {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 12px;
	}
	.reason-preset-label {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.7rem;
		color: rgba(255,255,255,0.5);
		text-transform: uppercase;
		letter-spacing: 1px;
		min-width: 110px;
	}
	.reason-preset {
		flex: 1;
		background: #000;
		color: #4ade80;
		border: 1px solid rgba(74,222,128,0.4);
		padding: 8px 12px;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.8rem;
		outline: none;
		cursor: pointer;
	}
	.reason-preset:focus { border-color: #4ade80; }
	.reason-preset:disabled { opacity: 0.5; cursor: not-allowed; }

	.reason-input-row {
		display: flex;
		gap: 12px;
		margin-bottom: 16px;
	}

	.reason-input {
		flex: 1;
		background: #000;
		color: #fff;
		border: 1px solid rgba(255,255,255,0.12);
		padding: 12px;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.82rem;
		resize: vertical;
		outline: none;
	}
	.reason-input:focus { border-color: #4ade80; }
	.reason-input:disabled { opacity: 0.5; }

	.reason-btn {
		background: transparent;
		color: #4ade80;
		border: 1px solid #4ade80;
		padding: 0 24px;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.82rem;
		text-transform: uppercase;
		letter-spacing: 2px;
		cursor: pointer;
		min-width: 120px;
	}
	.reason-btn:hover:not(:disabled) { background: rgba(74,222,128,0.1); }
	.reason-btn:disabled { opacity: 0.4; cursor: not-allowed; }

	.reason-output {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.85rem;
		color: #fff;
		line-height: 1.55;
		padding: 16px;
		background: #000;
		border-left: 2px solid #4ade80;
		margin-bottom: 12px;
		white-space: pre-wrap;
	}

	.reason-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 20px;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.72rem;
		color: rgba(255,255,255,0.55);
	}
	.reason-meta strong {
		color: #fff;
		font-weight: 600;
	}
	.reason-sov strong { color: #4ade80; }

	.reason-error {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.78rem;
		color: #f87171;
		padding: 12px;
		border-left: 2px solid #f87171;
		background: #000;
	}

	.reason-placeholder {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.78rem;
		color: rgba(255,255,255,0.4);
		padding: 12px 0;
	}
	.reason-placeholder em {
		color: #4ade80;
		font-style: normal;
	}

	.reason-cursor {
		display: inline-block;
		color: #4ade80;
		animation: cursor-blink 1s steps(2, start) infinite;
		margin-left: 2px;
	}
	@keyframes cursor-blink {
		to { visibility: hidden; }
	}

	.reason-streaming-hint {
		color: rgba(74, 222, 128, 0.7);
		font-style: italic;
		letter-spacing: 0.5px;
	}

	/* ── Sovereign brand header ──────────────────────── */
	.sov-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		flex-wrap: wrap;
		gap: 16px;
		padding: 16px 20px;
		margin-bottom: 24px;
		background: linear-gradient(180deg, rgba(74,222,128,0.04) 0%, rgba(0,0,0,0) 100%);
		border: 1px solid rgba(74,222,128,0.18);
		border-left: 3px solid #4ade80;
		position: relative;
	}
	.sov-header::before {
		content: '';
		position: absolute;
		top: 0; left: 0; right: 0; bottom: 0;
		background: repeating-linear-gradient(
			0deg,
			rgba(74,222,128,0.015) 0px,
			rgba(74,222,128,0.015) 1px,
			transparent 1px,
			transparent 3px
		);
		pointer-events: none;
	}

	.sov-brand {
		display: flex;
		align-items: baseline;
		gap: 10px;
		position: relative;
	}
	.sov-mark {
		color: #4ade80;
		font-size: 1.4rem;
		line-height: 1;
	}
	.sov-title {
		font-family: 'JetBrains Mono', monospace;
		font-size: 1.1rem;
		font-weight: 700;
		letter-spacing: 2px;
		color: #fff;
	}
	.sov-sub {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.72rem;
		color: rgba(74,222,128,0.7);
		text-transform: uppercase;
		letter-spacing: 3px;
	}

	.sov-status {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		position: relative;
	}
	.sov-pill {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 5px 10px;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.7rem;
		border: 1px solid;
		background: #000;
		color: rgba(255,255,255,0.78);
		text-transform: lowercase;
		letter-spacing: 0.5px;
	}
	.sov-pill strong { color: #fff; font-weight: 600; }
	.sov-dot {
		width: 6px; height: 6px; border-radius: 50%;
		display: inline-block;
	}
	.sov-pill-ok { border-color: rgba(74,222,128,0.4); }
	.sov-pill-ok .sov-dot {
		background: #4ade80;
		box-shadow: 0 0 6px #4ade80;
		animation: sov-pulse 2.4s ease-in-out infinite;
	}
	.sov-pill-block { border-color: rgba(248,113,113,0.4); }
	.sov-pill-block .sov-dot {
		background: #f87171;
		box-shadow: 0 0 6px #f87171;
	}
	.sov-pill-block strong { color: #f87171; }
	.sov-pill-sov { border-color: rgba(74,222,128,0.6); background: rgba(74,222,128,0.06); }
	.sov-pill-sov .sov-dot {
		background: #4ade80;
		box-shadow: 0 0 10px #4ade80;
	}
	.sov-pill-sov strong { color: #4ade80; }

	@keyframes sov-pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.45; }
	}
</style>
