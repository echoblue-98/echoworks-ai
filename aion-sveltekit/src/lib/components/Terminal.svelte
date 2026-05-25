<script lang="ts">
	import { terminalLines, clearTerminal, activeAttack, buttonsDisabled, currentReport, reportLoading, voiceEnabled } from '$lib/stores/state';
	import type { ForensicReport } from '$lib/stores/state';
	import { connectionStatus } from '$lib/stores/state';
	import { triggerAttack, toggleVoice } from '$lib/stores/websocket';
	import { attackButtons } from '$lib/data/content';
	import { onMount, afterUpdate, tick } from 'svelte';

	let terminalEl: HTMLDivElement;

	afterUpdate(() => {
		if (terminalEl) terminalEl.scrollTop = terminalEl.scrollHeight;
	});

	const colorMap: Record<string, string> = {
		alert: 'var(--primary)',
		success: 'var(--success)',
		scenario: 'var(--warning)',
		info: 'var(--text-dim)',
		event: '#888',
		error: '#ff6666',
		divider: 'var(--border)',
		analysis: 'var(--warning)'
	};

	function riskColor(score: number): string {
		if (score >= 80) return 'var(--primary)';
		if (score >= 50) return 'var(--warning)';
		return 'var(--success)';
	}
</script>

<section class="demo-section fade-in delay-2">
	<h2 class="section-title">Live Threat Detection</h2>

	<div class="attack-controls" style="margin-bottom:20px; display:flex; gap:12px; flex-wrap:wrap;">
		{#each attackButtons as btn (btn.id)}
			<button
				class="attack-btn"
				class:running={$activeAttack === btn.id}
				disabled={$buttonsDisabled}
				title={btn.title}
				onclick={() => triggerAttack(btn.id)}
			>
				{btn.icon} {btn.label}
			</button>
		{/each}
		<button class="clear-btn" onclick={() => clearTerminal()}>🗑️ Clear</button>
		<button 
			class="voice-btn" 
			class:active={$voiceEnabled}
			onclick={(e) => { e.preventDefault(); toggleVoice(); }}
			title={$voiceEnabled ? 'Disable voice' : 'Enable voice synthesis'}
		>
			{$voiceEnabled ? '🔊' : '🔇'} Voice
		</button>
	</div>

	<div class="connection-status">
		<span class="status-dot" class:connected={$connectionStatus === 'connected'} class:offline={$connectionStatus === 'offline'}></span>
		<span>
			{#if $connectionStatus === 'connected'}Connected to AION OS Backend
			{:else if $connectionStatus === 'offline'}Backend offline — Run showcase_server.py
			{:else}Connecting to AION OS...
			{/if}
		</span>
	</div>

	<div class="terminal" bind:this={terminalEl}>
		{#each $terminalLines as line (line.id)}
			<div class="terminal-line">
				{#if line.type === 'alert'}
					<span style="color:var(--primary); font-weight:600">{line.prefix}</span>
					<span style="color:var(--success)">{line.text}</span>
					<span style="background:rgba(255,59,59,0.2); color:var(--primary); padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:600">CRITICAL</span>
				{:else if line.type === 'divider'}
					<span style="color:var(--border)">{line.text}</span>
				{:else}
					<span style="color:var(--text-dim)">{line.prefix}</span>
					<span style="color:{colorMap[line.type] || '#888'}">{line.text}</span>
				{/if}
			</div>
		{/each}

		<!-- Loading spinner while LLM is running -->
		{#if $reportLoading}
			<div class="scan-bar">
				<div><span class="scan-text">⟐ ANALYZING THREAT VECTOR</span> <span class="scan-progress">...</span></div>
				<div class="scan-detail">Cross-referencing 66 attack patterns via sovereign LLM...</div>
			</div>
		{/if}

		<!-- Forensic Report -->
		{#if $currentReport}
			<div class="forensic-report wow-entrance">
				<div class="report-header">🔍 SOVEREIGN FORENSIC REPORT</div>

				{#each $currentReport.vulnerabilities as vuln}
					<div style="margin-bottom: 8px;">
						<span class="vuln-title">{vuln.title}</span>
						<span class="vuln-severity {vuln.severity === 'critical' ? 'sev-critical' : 'sev-high'}">{vuln.severity}</span>
					</div>
					{#if vuln.description}
						<div style="color: var(--text-dim); margin: 4px 0; font-size: 0.82rem;">{vuln.description}</div>
					{/if}
					{#if vuln.attack_vector}
						<div style="color: #888; font-size: 0.78rem;">⚡ {vuln.attack_vector}</div>
					{/if}
					{#if vuln.countermeasures && vuln.countermeasures.length > 0}
						<div style="margin-top: 6px; color: var(--success); font-weight: 500;">▸ Countermeasures:</div>
						{#each vuln.countermeasures as cm}
							<div class="countermeasure">→ {cm}</div>
						{/each}
					{/if}
				{/each}

				<div style="margin-top: 8px;">
					Risk Score: <span style="color: {riskColor($currentReport.risk_score)}; font-weight: 600;">{$currentReport.risk_score}/100</span>
				</div>
				<div class="risk-bar">
					<div class="risk-fill" style="width: {$currentReport.risk_score}%; background: {riskColor($currentReport.risk_score)};"></div>
				</div>

				{#if $currentReport.immediate_actions && $currentReport.immediate_actions.length > 0}
					<div style="margin-top: 6px; color: var(--primary); font-weight: 500;">▸ Immediate Actions:</div>
					{#each $currentReport.immediate_actions as action, i}
						<div style="color: var(--text-dim); padding-left: 12px;">{i + 1}. {action}</div>
					{/each}
				{/if}

				<div style="margin-top: 6px; color: #555; font-size: 0.72rem;">
					Model: {$currentReport.model || 'local'} | 100% sovereign — zero data left your machine
				</div>

				<div class="threat-stamp">✓ THREAT CONTAINED</div>
			</div>
		{/if}
	</div>
</section>

<style>
	.demo-section {
		background: var(--bg-card); border: 1px solid var(--border);
		border-radius: 20px; padding: 40px; margin-bottom: 60px;
	}
	.connection-status {
		display: flex; align-items: center; gap: 8px;
		margin-bottom: 12px; font-size: 0.8rem; color: var(--text-dim);
	}
	.status-dot {
		width: 8px; height: 8px; border-radius: 50%;
		background: var(--warning); animation: blink 1s infinite;
	}
	.status-dot.connected { background: var(--success); animation: none; }
	.status-dot.offline { background: var(--primary); animation: none; }
	@keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0.3; } }

	/* Scan bar */
	.scan-bar {
		background: rgba(0, 255, 136, 0.08);
		border: 1px solid rgba(0, 255, 136, 0.15);
		border-radius: 6px; padding: 12px 16px; margin: 8px 0;
		font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
		overflow: hidden; position: relative;
	}
	.scan-bar::after {
		content: ''; position: absolute; top: 0; left: -100%;
		width: 100%; height: 100%;
		background: linear-gradient(90deg, transparent, rgba(0,255,136,0.1), transparent);
		animation: scanSweep 1.5s ease-in-out infinite;
	}
	@keyframes scanSweep { 0% { left: -100%; } 100% { left: 100%; } }
	.scan-text { color: var(--success); font-weight: 500; }
	.scan-progress { color: var(--warning); font-weight: 600; }
	.scan-detail { color: var(--text-dim); font-size: 0.75rem; margin-top: 4px; }

	/* Forensic report */
	.forensic-report {
		background: rgba(0, 255, 136, 0.05);
		border: 1px solid rgba(0, 255, 136, 0.2);
		border-radius: 8px; padding: 16px; margin: 8px 0; font-size: 0.82rem;
	}
	.forensic-report.wow-entrance {
		animation: fadeIn 0.3s ease forwards, reportGlow 1.5s ease-out;
	}
	@keyframes reportGlow {
		0% { border-color: rgba(0,255,136,0); box-shadow: 0 0 0 rgba(0,255,136,0); }
		50% { border-color: rgba(0,255,136,0.6); box-shadow: 0 0 30px rgba(0,255,136,0.2); }
		100% { border-color: rgba(0,255,136,0.2); box-shadow: 0 0 10px rgba(0,255,136,0.1); }
	}
	@keyframes fadeIn { to { opacity: 1; } }
	.report-header { color: var(--success); font-weight: 600; margin-bottom: 8px; font-size: 0.85rem; }
	.vuln-title { color: var(--warning); font-weight: 600; }
	.vuln-severity {
		display: inline-block; padding: 1px 6px; border-radius: 3px;
		font-size: 0.7rem; font-weight: 600; text-transform: uppercase; margin-left: 6px;
	}
	.sev-critical { background: rgba(255,59,59,0.2); color: var(--primary); }
	.sev-high { background: rgba(255,170,0,0.2); color: var(--warning); }
	.countermeasure { color: var(--text-dim); padding-left: 12px; font-size: 0.82rem; }
	.risk-bar {
		height: 4px; background: rgba(255,255,255,0.1);
		border-radius: 2px; margin: 6px 0; overflow: hidden;
	}
	.risk-fill {
		height: 100%; border-radius: 2px;
		transition: width 1.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
	}
	.threat-stamp {
		display: inline-block; border: 3px solid var(--success); color: var(--success);
		padding: 6px 20px; font-family: 'JetBrains Mono', monospace;
		font-size: 0.9rem; font-weight: 700; letter-spacing: 3px;
		text-transform: uppercase; transform: rotate(-3deg);
		margin: 12px 0 4px; animation: stampSlam 0.4s ease-out forwards;
	}
	@keyframes stampSlam {
		0% { transform: rotate(-3deg) scale(3); opacity: 0; }
		60% { transform: rotate(-3deg) scale(0.9); opacity: 1; }
		100% { transform: rotate(-3deg) scale(1); opacity: 1; }
	}
</style>
