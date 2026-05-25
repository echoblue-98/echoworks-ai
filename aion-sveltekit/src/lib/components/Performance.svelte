<section class="fade-in delay-4">
	<h2 class="section-title">Performance</h2>
	<div class="perf-grid">
		<div class="perf-card">
			<div class="perf-value" style="color: var(--success)">0.07<span class="perf-unit">ms</span></div>
			<div class="perf-label">Per-Event Latency</div>
		</div>
		<div class="perf-card">
			<div class="perf-value" style="color: var(--primary)">15,165<span class="perf-unit">/sec</span></div>
			<div class="perf-label">Event Throughput</div>
		</div>
		<div class="perf-card">
			<div class="perf-value" style="color: var(--warning)">CPU<span class="perf-unit">only</span></div>
			<div class="perf-label">Hardware Required</div>
		</div>
	</div>
</section>

<style>
	.perf-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-bottom: 60px; }
	.perf-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 20px; padding: 32px; text-align: center; }
	.perf-value { font-family: 'JetBrains Mono', monospace; font-size: 3rem; font-weight: 600; margin-bottom: 8px; }
	.perf-unit { font-size: 1.2rem; color: var(--text-dim); }
	.perf-label { font-size: 0.9rem; color: var(--text-dim); text-transform: uppercase; letter-spacing: 1px; margin-top: 8px; }
</style>
