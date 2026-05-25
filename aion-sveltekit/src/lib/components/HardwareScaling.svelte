<script lang="ts">
	import { hardwareTiers } from '$lib/data/content';
</script>

<section class="fade-in delay-5" style="margin-bottom: 60px;">
	<h2 class="section-title">Sovereign AI Scaling</h2>
	<div class="card" style="padding: 40px;">
		<p style="color: var(--text-dim); font-size: 0.95rem; line-height: 1.7; margin-bottom: 24px; max-width: 700px;">
			Intelligence scales with hardware — not subscriptions. A single GPU card turns AION OS from demo into
			<strong style="color: var(--text)">production-grade SOC analyst</strong>. Still 100% on-premise.
		</p>
		<div class="hw-tier-grid" style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 24px;">
			{#each hardwareTiers as tier (tier.name)}
				{@const rgb = tier.colorVar === 'success' ? '0,255,136' : tier.colorVar === 'warning' ? '255,170,0' : '255,59,59'}
				<div class="tier-card" style="border-color: rgba({rgb}, {tier.badge ? '1' : '0.3'}); background: rgba({rgb}, {tier.badge ? '0.06' : '0.04'});">
					{#if tier.badge}
						<div class="tier-badge" style="background: var(--{tier.colorVar})">{tier.badge}</div>
					{/if}
					<div style="font-size: 1.4rem; margin-bottom: 8px">{tier.icon}</div>
					<div style="font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: var(--{tier.colorVar}); font-weight: 600; margin-bottom: 4px">{tier.name}</div>
					<div style="font-size: 0.72rem; color: var(--text-dim); margin-bottom: 10px">{tier.vram}</div>
					<div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; font-weight: 600; margin-bottom: 2px">{tier.model}</div>
					<div style="font-size: 0.7rem; color: var(--text-dim); margin-bottom: 8px">{tier.quality}</div>
					<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 600; color: var(--success)">{tier.speed}</div>
					<div style="font-size: 0.65rem; color: var(--text-dim)">per report</div>
					<div style="margin-top: 10px; font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; font-weight: 600; color: var(--{tier.colorVar})">{tier.price}</div>
				</div>
			{/each}
		</div>
		<div class="hw-insights" style="display: flex; gap: 24px; padding-top: 20px; border-top: 1px solid var(--border);">
			<div class="insight-box" style="background: rgba(0,255,136,0.04); border-color: rgba(0,255,136,0.12);">
				<span style="font-size: 1.5rem">💡</span>
				<div>
					<div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 2px">Law firms already have workstations</div>
					<div style="font-size: 0.78rem; color: var(--text-dim)">A $400 GPU turns any existing machine into a production SOC analyst — still 100% sovereign</div>
				</div>
			</div>
			<div class="insight-box" style="background: rgba(255,59,59,0.04); border-color: rgba(255,59,59,0.12);">
				<span style="font-size: 1.5rem">📊</span>
				<div>
					<div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 2px">Scales with hardware, not subscriptions</div>
					<div style="font-size: 0.78rem; color: var(--text-dim)">One-time cost. No per-seat fees. No cloud dependency.</div>
				</div>
			</div>
		</div>
	</div>
</section>

<style>
	.tier-card {
		border: 1px solid; border-radius: 14px; padding: 20px 16px;
		text-align: center; position: relative;
	}
	.tier-badge {
		position: absolute; top: -10px; left: 50%; transform: translateX(-50%);
		color: #000; font-size: 0.65rem; font-weight: 700;
		padding: 2px 10px; border-radius: 10px; text-transform: uppercase; letter-spacing: 1px;
	}
	.insight-box {
		flex: 1; display: flex; align-items: center; gap: 14px;
		padding: 14px 18px; border: 1px solid; border-radius: 10px;
	}
</style>
