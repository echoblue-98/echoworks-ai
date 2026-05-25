<script lang="ts">
	import { currentDocAnalysis, docAnalysisLoading } from '$lib/stores/state';
	import { analyzeDocument } from '$lib/stores/websocket';

	let textInput = $state('');
	let docType = $state('contract');
	let titleInput = $state('');

	const riskColor: Record<string, string> = {
		critical: '#ff1744',
		high: '#ff9100',
		medium: '#ffc400',
		low: '#00e676',
		info: '#448aff'
	};

	function handleSubmit() {
		if (!textInput.trim()) return;
		analyzeDocument(textInput, docType, titleInput);
	}

	const DOC_TYPES = [
		'contract',
		'agreement',
		'nda',
		'engagement_letter',
		'recording_agreement',
		'ip_assignment',
		'license',
		'employment',
		'settlement',
		'brief',
		'other'
	];
</script>

<section class="doc-analysis" id="doc-analysis">
	<h2 class="section-title">
		<span class="accent">📄</span> Document Intelligence
	</h2>
	<p class="subtitle">
		Multi-modal contract analysis — extract clauses, flag risks, map obligations. All processing
		is local.
	</p>

	<!-- Input Panel -->
	<div class="input-panel">
		<div class="input-row">
			<input
				type="text"
				bind:value={titleInput}
				placeholder="Document title (optional)"
				class="title-input"
			/>
			<select bind:value={docType} class="type-select">
				{#each DOC_TYPES as dt}
					<option value={dt}>{dt.replace(/_/g, ' ')}</option>
				{/each}
			</select>
		</div>
		<textarea
			bind:value={textInput}
			placeholder="Paste contract or legal document text here..."
			class="doc-textarea"
			rows="6"
		></textarea>
		<button
			class="analyze-btn"
			onclick={handleSubmit}
			disabled={!textInput.trim() || $docAnalysisLoading}
		>
			{#if $docAnalysisLoading}
				<span class="spinner"></span> Analyzing...
			{:else}
				Analyze Document
			{/if}
		</button>
	</div>

	<!-- Analysis Result -->
	{#if $currentDocAnalysis}
		{@const a = $currentDocAnalysis}
		<div class="result-panel">
			<!-- Header -->
			<div class="result-header">
				<div class="result-title">{a.title}</div>
				<div class="risk-badge" style="background: {riskColor[a.overall_risk] ?? '#666'}">
					{a.overall_risk.toUpperCase()} — {a.risk_score}/100
				</div>
			</div>

			<div class="result-meta">
				<span>Parties: {a.parties.join(', ')}</span>
				<span>Type: {a.document_type.replace(/_/g, ' ')}</span>
				<span>Clauses: {a.clauses.length}</span>
			</div>

			<!-- Risk Bar -->
			<div class="risk-bar-container">
				<div
					class="risk-bar-fill"
					style="width: {a.risk_score}%; background: {riskColor[a.overall_risk] ?? '#666'}"
				></div>
			</div>

			<!-- Red Flags -->
			{#if a.red_flags.length > 0}
				<div class="section-block red-flags">
					<h3>Red Flags ({a.red_flags.length})</h3>
					{#each a.red_flags as flag}
						<div class="flag-item">{flag}</div>
					{/each}
				</div>
			{/if}

			<!-- Extracted Clauses -->
			<div class="section-block">
				<h3>Extracted Clauses ({a.clauses.length})</h3>
				{#each a.clauses as clause, i}
					<div class="clause-card" data-risk={clause.risk_level}>
						<div class="clause-header">
							<span class="clause-num">#{i + 1}</span>
							<span class="clause-type"
								>{clause.clause_type.replace(/_/g, ' ').toUpperCase()}</span
							>
							<span
								class="clause-risk"
								style="color: {riskColor[clause.risk_level] ?? '#666'}"
							>
								{clause.risk_level.toUpperCase()}
							</span>
						</div>
						<div class="clause-summary">{clause.summary}</div>
						{#if clause.risk_reason !== 'Standard clause'}
							<div class="clause-reason">⚠ {clause.risk_reason}</div>
						{/if}
						{#if clause.recommendations.length > 0}
							<div class="clause-recs">
								{#each clause.recommendations as rec}
									<div class="rec-item">→ {rec}</div>
								{/each}
							</div>
						{/if}
					</div>
				{/each}
			</div>

			<!-- Obligations -->
			{#if Object.keys(a.key_obligations).length > 0}
				<div class="section-block">
					<h3>Obligation Map</h3>
					{#each Object.entries(a.key_obligations) as [party, obs]}
						<div class="obligation-group">
							<div class="party-name">{party}</div>
							{#each obs as ob}
								<div class="ob-item">• {ob}</div>
							{/each}
						</div>
					{/each}
				</div>
			{/if}

			<!-- Recommendations -->
			{#if a.recommendations.length > 0}
				<div class="section-block recs-block">
					<h3>Recommendations ({a.recommendations.length})</h3>
					{#each a.recommendations as rec}
						<div class="rec-global">• {rec}</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}
</section>

<style>
	.doc-analysis {
		padding: 4rem 2rem;
		max-width: 900px;
		margin: 0 auto;
	}

	.section-title {
		font-size: 1.5rem;
		font-weight: 700;
		margin-bottom: 0.25rem;
	}
	.accent {
		font-size: 1.3rem;
	}
	.subtitle {
		color: #888;
		margin-bottom: 2rem;
		font-size: 0.9rem;
	}

	.input-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 8px;
		padding: 1.25rem;
		margin-bottom: 2rem;
	}

	.input-row {
		display: flex;
		gap: 0.75rem;
		margin-bottom: 0.75rem;
	}
	.title-input {
		flex: 1;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		color: #e0e0e0;
		padding: 0.5rem 0.75rem;
		font-family: 'Inter', sans-serif;
		font-size: 0.85rem;
	}
	.type-select {
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		color: #e0e0e0;
		padding: 0.5rem;
		font-family: 'Inter', sans-serif;
		font-size: 0.85rem;
		text-transform: capitalize;
	}

	.doc-textarea {
		width: 100%;
		background: rgba(0, 0, 0, 0.3);
		border: 1px solid rgba(255, 255, 255, 0.1);
		border-radius: 4px;
		color: #e0e0e0;
		padding: 0.75rem;
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.8rem;
		resize: vertical;
		margin-bottom: 0.75rem;
		line-height: 1.5;
	}
	.doc-textarea::placeholder {
		color: #555;
	}

	.analyze-btn {
		width: 100%;
		padding: 0.7rem;
		background: linear-gradient(135deg, #00e5ff, #0091ea);
		color: #0a0a0a;
		border: none;
		border-radius: 4px;
		font-weight: 700;
		font-size: 0.9rem;
		cursor: pointer;
		transition: opacity 0.2s;
	}
	.analyze-btn:hover:not(:disabled) {
		opacity: 0.85;
	}
	.analyze-btn:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	.spinner {
		display: inline-block;
		width: 14px;
		height: 14px;
		border: 2px solid rgba(0, 0, 0, 0.2);
		border-top-color: #0a0a0a;
		border-radius: 50%;
		animation: spin 0.6s linear infinite;
		vertical-align: middle;
		margin-right: 0.25rem;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	/* ── Result Panel ───────────────────────────── */
	.result-panel {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 8px;
		padding: 1.5rem;
	}

	.result-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}
	.result-title {
		font-weight: 700;
		font-size: 1.1rem;
	}
	.risk-badge {
		padding: 0.25rem 0.75rem;
		border-radius: 12px;
		color: #fff;
		font-weight: 700;
		font-size: 0.75rem;
		letter-spacing: 0.5px;
	}

	.result-meta {
		display: flex;
		gap: 1.5rem;
		color: #888;
		font-size: 0.8rem;
		margin-bottom: 1rem;
	}

	.risk-bar-container {
		height: 6px;
		background: rgba(255, 255, 255, 0.05);
		border-radius: 3px;
		margin-bottom: 1.5rem;
		overflow: hidden;
	}
	.risk-bar-fill {
		height: 100%;
		border-radius: 3px;
		transition: width 0.8s ease-out;
	}

	.section-block {
		margin-bottom: 1.5rem;
	}
	.section-block h3 {
		font-size: 0.9rem;
		color: #00e5ff;
		margin-bottom: 0.75rem;
		font-weight: 600;
	}

	/* Red flags */
	.red-flags {
		background: rgba(255, 23, 68, 0.05);
		border: 1px solid rgba(255, 23, 68, 0.15);
		border-radius: 6px;
		padding: 1rem;
	}
	.flag-item {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.78rem;
		color: #ff8a80;
		margin-bottom: 0.4rem;
		line-height: 1.4;
	}

	/* Clauses */
	.clause-card {
		background: rgba(0, 0, 0, 0.2);
		border: 1px solid rgba(255, 255, 255, 0.06);
		border-radius: 6px;
		padding: 0.75rem;
		margin-bottom: 0.5rem;
		border-left: 3px solid #444;
	}
	.clause-card[data-risk='critical'] {
		border-left-color: #ff1744;
	}
	.clause-card[data-risk='high'] {
		border-left-color: #ff9100;
	}
	.clause-card[data-risk='medium'] {
		border-left-color: #ffc400;
	}
	.clause-card[data-risk='low'] {
		border-left-color: #00e676;
	}

	.clause-header {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		margin-bottom: 0.3rem;
	}
	.clause-num {
		color: #555;
		font-size: 0.75rem;
		font-weight: 700;
	}
	.clause-type {
		font-weight: 700;
		font-size: 0.78rem;
		color: #e0e0e0;
		flex: 1;
	}
	.clause-risk {
		font-weight: 700;
		font-size: 0.72rem;
		letter-spacing: 0.5px;
	}
	.clause-summary {
		font-size: 0.82rem;
		color: #bbb;
		line-height: 1.4;
	}
	.clause-reason {
		font-size: 0.78rem;
		color: #ff9100;
		margin-top: 0.25rem;
	}
	.clause-recs {
		margin-top: 0.4rem;
	}
	.rec-item {
		font-size: 0.76rem;
		color: #00e5ff;
		line-height: 1.4;
	}

	/* Obligations */
	.obligation-group {
		margin-bottom: 0.75rem;
	}
	.party-name {
		font-weight: 700;
		font-size: 0.85rem;
		margin-bottom: 0.25rem;
	}
	.ob-item {
		font-size: 0.8rem;
		color: #bbb;
		margin-left: 0.5rem;
		line-height: 1.4;
	}

	/* Recommendations */
	.recs-block {
		background: rgba(0, 229, 255, 0.03);
		border: 1px solid rgba(0, 229, 255, 0.1);
		border-radius: 6px;
		padding: 1rem;
	}
	.rec-global {
		font-size: 0.82rem;
		color: #e0e0e0;
		margin-bottom: 0.4rem;
		line-height: 1.4;
	}
</style>
