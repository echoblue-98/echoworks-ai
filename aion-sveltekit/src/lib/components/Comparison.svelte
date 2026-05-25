<script lang="ts">
	import { comparisonData } from '$lib/data/comparison';
</script>

<section class="fade-in delay-5" style="margin-bottom: 60px;">
	<h2 class="section-title">Why Not Just Use CrowdStrike?</h2>
	<div class="card">
		<p class="intro">
			Enterprise SIEM tools weren't built for law firms. They can't distinguish a departing partner from a sys admin,
			and they <strong>send your client data to their cloud for analysis</strong>.
		</p>
		<div class="compare-table-wrap">
			<table class="compare-table">
				<thead>
					<tr>
						<th style="width: 22%">Capability</th>
						<th class="aion-col" style="width: 19.5%">AION OS</th>
						<th style="width: 19.5%">CrowdStrike</th>
						<th style="width: 19.5%">MS Sentinel</th>
						<th style="width: 19.5%">Generic SIEM</th>
					</tr>
				</thead>
				<tbody>
					{#each comparisonData as row (row.feature)}
						<tr>
							<td style="font-weight: 500">{row.feature}</td>
							<td class="aion-cell"><span class="compare-{row.aion.status}">{row.aion.text}</span></td>
							<td><span class="compare-{row.crowdstrike.status}">{row.crowdstrike.text}</span></td>
							<td><span class="compare-{row.sentinel.status}">{row.sentinel.text}</span></td>
							<td><span class="compare-{row.siem.status}">{row.siem.text}</span></td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<div class="bottom-callout">
			<span style="font-size: 1.5rem">⚡</span>
			<div>
				<div style="font-size: 0.85rem; font-weight: 600; margin-bottom: 2px">
					CrowdStrike protects endpoints. AION OS protects the <em>practice</em>.
				</div>
				<div style="font-size: 0.78rem; color: var(--text-dim)">
					Privilege theft, ethics wall breaches, trust account fraud — these aren't IT problems, they're law firm problems.
				</div>
			</div>
		</div>
	</div>
</section>

<style>
	.intro { color: var(--text-dim); font-size: 0.92rem; line-height: 1.7; margin-bottom: 20px; max-width: 800px; }
	.intro strong { color: var(--text); }
	.bottom-callout {
		margin-top: 20px; padding: 14px 18px;
		background: rgba(255,59,59,0.04); border: 1px solid rgba(255,59,59,0.15);
		border-radius: 10px; display: flex; align-items: center; gap: 14px;
	}
</style>
