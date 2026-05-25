<script lang="ts">
	import { detectionCategories } from '$lib/data/detections';
</script>

<section class="fade-in delay-3">
	<h2 class="section-title">Threat Detection Coverage</h2>
	<div class="detection-grid">
		{#each detectionCategories as cat (cat.title)}
			<div class="detection-card">
				<div class="card-header">
					<div class="card-icon">{cat.icon}</div>
					<div class="card-rate">{cat.rate}</div>
				</div>
				<div class="card-title">{cat.title}</div>
				<div class="card-scenarios">{cat.scenarios}</div>
				<div class="progress-bar">
					<div class="progress-fill" style="animation-delay: {cat.animationDelay}s"></div>
				</div>
			</div>
		{/each}
	</div>
</section>

<style>
	.detection-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 60px; }
	.detection-card {
		background: var(--bg-card); border: 1px solid var(--border);
		border-radius: 16px; padding: 24px; transition: all 0.3s ease;
		position: relative; overflow: hidden;
	}
	.detection-card::before {
		content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 3px;
		background: linear-gradient(90deg, var(--success), var(--success));
		opacity: 0; transition: opacity 0.3s;
	}
	.detection-card:hover { background: var(--bg-card-hover); border-color: rgba(255,255,255,0.15); transform: translateY(-4px); }
	.detection-card:hover::before { opacity: 1; }
	.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px; }
	.card-icon {
		width: 44px; height: 44px; border-radius: 12px;
		display: flex; align-items: center; justify-content: center;
		font-size: 1.5rem; background: rgba(255,59,59,0.1);
	}
	.card-rate { font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 600; color: var(--success); }
	.card-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 8px; }
	.card-scenarios { font-size: 0.85rem; color: var(--text-dim); margin-bottom: 16px; }
</style>
