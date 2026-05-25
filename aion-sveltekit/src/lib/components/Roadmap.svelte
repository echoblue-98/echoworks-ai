<script lang="ts">
	import { roadmapPhases } from '$lib/data/content';
</script>

<section class="fade-in delay-5" style="margin-bottom: 60px;">
	<h2 class="section-title">Enterprise Roadmap</h2>
	<div class="card" style="padding: 40px;">
		<div class="roadmap-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px; position: relative;">
			<div class="roadmap-line" style="position: absolute; top: 28px; left: 12.5%; right: 12.5%; height: 2px; background: linear-gradient(90deg, var(--success), var(--warning), var(--primary), var(--primary)); z-index: 0;"></div>
			{#each roadmapPhases as phase (phase.period)}
				<div style="text-align: center; position: relative; z-index: 1;">
					<div class="phase-circle" style="border-color: var(--{phase.colorVar}); background: rgba(var(--{phase.colorVar === 'success' ? '0,255,136' : phase.colorVar === 'warning' ? '255,170,0' : '255,59,59'}), 0.15);">
						{phase.icon}
					</div>
					<div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--{phase.colorVar}); font-weight: 600; margin-bottom: 4px;">{phase.period}</div>
					<div style="font-size: 0.9rem; font-weight: 600; margin-bottom: 6px;">{phase.title}</div>
					<div style="font-size: 0.75rem; color: var(--text-dim); line-height: 1.5;">
						{#each phase.details as detail}{detail}<br />{/each}
					</div>
				</div>
			{/each}
		</div>
		<div class="roadmap-stats" style="margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--border); display: flex; justify-content: center; gap: 40px; font-size: 0.82rem;">
			<div style="text-align: center;">
				<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 600; color: var(--success);">1</div>
				<div style="color: var(--text-dim);">Current — moves fast</div>
			</div>
			<div style="text-align: center;">
				<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 600; color: var(--warning);">3-5</div>
				<div style="color: var(--text-dim);">Hiring with first clients</div>
			</div>
			<div style="text-align: center;">
				<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 600; color: var(--primary);">$0</div>
				<div style="color: var(--text-dim);">Pilot cost to firm</div>
			</div>
		</div>
	</div>
</section>

<style>
	.phase-circle {
		width: 56px; height: 56px; border-radius: 50%; border: 2px solid;
		display: flex; align-items: center; justify-content: center;
		margin: 0 auto 12px; font-size: 1.3rem;
	}
</style>
