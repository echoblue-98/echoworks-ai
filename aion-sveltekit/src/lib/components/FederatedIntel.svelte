<section class="fade-in delay-5" style="margin-bottom: 60px;">
	<h2 class="section-title">Federated Threat Intelligence</h2>
	<div class="fed-intel-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
		<!-- Left: Network Effect -->
		<div class="card">
			<h3 style="font-size: 1.1rem; margin-bottom: 16px; display: flex; align-items: center; gap: 10px;">
				<span style="color: var(--success)">⟁</span> Network Effect Without Data Exposure
			</h3>
			<p style="color: var(--text-dim); font-size: 0.9rem; line-height: 1.7; margin-bottom: 16px;">
				Each AION OS deployment contributes <strong style="color: var(--text)">anonymized attack pattern signatures</strong> —
				never client data, never PII, never file contents.
			</p>
			<div class="code-block">
				<div style="color: var(--text-dim)">// What gets shared:</div>
				<div style="color: var(--success)">pattern_hash: "a3f8c2..." <span style="color: #555">// anonymous</span></div>
				<div style="color: var(--success)">attack_class: "pre_departure_exfil"</div>
				<div style="color: var(--success)">stage_count: 4</div>
				<div style="color: var(--success)">sector: "legal"</div>
				<div style="color: var(--text-dim); margin-top: 8px">// What NEVER leaves:</div>
				<div style="color: var(--primary)">✗ firm_name, user_id, client_data</div>
				<div style="color: var(--primary)">✗ file_paths, ip_addresses, emails</div>
			</div>
		</div>
		<!-- Right: Growth -->
		<div class="card">
			<h3 style="font-size: 1.1rem; margin-bottom: 16px; display: flex; align-items: center; gap: 10px;">
				<span style="color: var(--warning)">⬡</span> CrowdStrike Model, Law Firm Rules
			</h3>
			<p style="color: var(--text-dim); font-size: 0.9rem; line-height: 1.7; margin-bottom: 16px;">
				More firms = more patterns = better detection. But unlike CrowdStrike,
				<strong style="color: var(--text)">privilege and confidentiality are preserved by design</strong>.
			</p>
			<div style="display: flex; flex-direction: column; gap: 12px;">
				{#each [
					{ firms: '5 firms', patterns: '66 patterns', color: 'success', bg: '0,255,136' },
					{ firms: '25 firms', patterns: '200+ patterns', color: 'warning', bg: '255,170,0' },
					{ firms: '100 firms', patterns: '500+ patterns', color: 'primary', bg: '255,59,59' }
				] as tier}
					<div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: rgba({tier.bg}, 0.05); border-radius: 8px; border: 1px solid rgba({tier.bg}, 0.1);">
						<span style="font-size: 0.85rem">{tier.firms}</span>
						<span style="font-family: 'JetBrains Mono', monospace; color: var(--{tier.color}); font-weight: 600">{tier.patterns}</span>
					</div>
				{/each}
				<div style="font-size: 0.78rem; color: var(--text-dim); text-align: center; margin-top: 4px">
					Each deployment strengthens the network. Attackers face a growing wall.
				</div>
			</div>
		</div>
	</div>
</section>

<style>
	.code-block {
		font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
		background: #0a0a0f; border-radius: 8px; padding: 16px; line-height: 1.8;
	}
</style>
