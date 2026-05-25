<section class="fade-in delay-5">
	<h2 class="section-title">Privacy Architecture</h2>
	<div class="privacy-grid">
		<div class="card">
			<h3 style="font-size: 1.2rem; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
				<span style="color: var(--success)">✓</span> What Stays Local
			</h3>
			<ul class="privacy-list">
				{#each ['All client & matter data', 'User identities & emails', 'IP addresses & file paths', 'Document contents', 'Privileged information'] as item}
					<li><span class="check">✓</span> {item}</li>
				{/each}
			</ul>
		</div>
		<div class="card">
			<h3 style="font-size: 1.2rem; margin-bottom: 20px; display: flex; align-items: center; gap: 10px;">
				<span style="color: var(--primary)">×</span> Never Leaves Firm
			</h3>
			<ul class="privacy-list">
				{#each ['No PII to cloud', 'No client names', 'No matter numbers', 'No file contents', 'No network details'] as item}
					<li><span class="cross">×</span> {item}</li>
				{/each}
			</ul>
		</div>
	</div>
</section>
