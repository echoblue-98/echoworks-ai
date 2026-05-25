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
</script>

{#if loading}
	<div class="loading-state">
		<p>Connecting…</p>
	</div>
{:else}

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
</style>
