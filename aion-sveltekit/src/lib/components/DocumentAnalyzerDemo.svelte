<script lang="ts">
  import { demos, type DocumentAnalyzeResult } from '$lib/api';

  let documentText = '';
  let documentType: 'contract' | 'agreement' | 'nda' | 'employment' | 'license' | 'other' = 'contract';
  let result: DocumentAnalyzeResult | null = null;
  let loading = false;
  let error = '';

  // Sample contract for demo
  const sampleContract = `RECORDING AGREEMENT

This Agreement is entered into between Artist ("Artist") and Global Music Corp ("Company").

1. GRANT OF RIGHTS: Artist hereby assigns to Company all right, title, and interest in and to any and all Masters recorded during the Term, in perpetuity, throughout the universe.

2. EXCLUSIVITY: During the Term, Artist shall render exclusive recording services to Company and shall not record for any other party.

3. COMPENSATION: Company shall pay Artist a royalty of 15% of net receipts from exploitation of the Masters, payable after full recoupment of all recording costs, advances, and promotional expenses.

4. INDEMNIFICATION: Artist shall indemnify and hold harmless Company from any and all claims, damages, and expenses arising from Artist's breach of any representation or warranty.

5. TERM: This Agreement shall continue for an initial period of five (5) years with four (4) additional option periods of one (1) year each, exercisable solely by Company.

6. TERMINATION: Company may terminate this Agreement at any time upon thirty (30) days written notice.`;

  async function analyze() {
    if (!documentText.trim()) {
      error = 'Please paste a document to analyze';
      return;
    }

    loading = true;
    error = '';
    result = null;

    try {
      result = await demos.analyzeDocument({
        document_text: documentText,
        document_type: documentType,
      });
    } catch (e) {
      error = e instanceof Error ? e.message : 'Analysis failed. Please try again.';
    } finally {
      loading = false;
    }
  }

  function loadSample() {
    documentText = sampleContract;
    documentType = 'contract';
  }

  function getRiskColor(level: string): string {
    switch (level.toLowerCase()) {
      case 'critical': return '#dc2626';
      case 'high': return '#ea580c';
      case 'medium': return '#ca8a04';
      case 'low': return '#16a34a';
      default: return '#6b7280';
    }
  }
</script>

<div class="demo-container">
  <div class="demo-header">
    <h2>🔍 Document Intelligence Demo</h2>
    <p>Paste a contract or agreement below to see AION OS analyze it in real-time.</p>
  </div>

  <div class="demo-input">
    <div class="input-controls">
      <select bind:value={documentType}>
        <option value="contract">Contract</option>
        <option value="agreement">Agreement</option>
        <option value="nda">NDA</option>
        <option value="employment">Employment</option>
        <option value="license">License</option>
        <option value="other">Other</option>
      </select>
      <button type="button" class="sample-btn" on:click={loadSample}>Load Sample</button>
    </div>
    <textarea
      bind:value={documentText}
      placeholder="Paste your contract or agreement text here..."
      rows="12"
    ></textarea>
    <button class="analyze-btn" on:click={analyze} disabled={loading}>
      {loading ? 'Analyzing...' : 'Analyze Document'}
    </button>
    {#if error}
      <div class="error-msg">{error}</div>
    {/if}
  </div>

  {#if result}
    <div class="demo-result">
      <div class="result-header">
        <div class="risk-score" style="--risk-color: {getRiskColor(result.risk_level)}">
          <span class="score">{result.risk_score.toFixed(0)}</span>
          <span class="label">Risk Score</span>
        </div>
        <div class="risk-badge" style="background: {getRiskColor(result.risk_level)}">
          {result.risk_level.toUpperCase()}
        </div>
        <span class="processing-time">{result.processing_time_ms}ms</span>
      </div>

      <div class="summary">
        <h4>Summary</h4>
        <p>{result.summary}</p>
      </div>

      {#if result.red_flags.length > 0}
        <div class="red-flags">
          <h4>🚩 Red Flags ({result.red_flags.length})</h4>
          <ul>
            {#each result.red_flags as flag}
              <li>{flag}</li>
            {/each}
          </ul>
        </div>
      {/if}

      <div class="clauses">
        <h4>Clause Analysis ({result.clauses_found} found)</h4>
        {#each result.clauses as clause}
          <div class="clause" style="--clause-color: {getRiskColor(clause.risk_level)}">
            <div class="clause-header">
              <span class="clause-type">{clause.clause_type.replace(/_/g, ' ')}</span>
              <span class="clause-risk">{clause.risk_level}</span>
            </div>
            <p class="clause-text">"{clause.text}"</p>
            <p class="clause-explanation">{clause.explanation}</p>
            {#if clause.recommendation}
              <p class="clause-recommendation">💡 {clause.recommendation}</p>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<style>
  .demo-container {
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
  }

  .demo-header {
    text-align: center;
    margin-bottom: 2rem;
  }

  .demo-header h2 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
  }

  .demo-header p {
    color: #6b7280;
  }

  .demo-input {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }

  .input-controls {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
  }

  select {
    padding: 0.5rem 1rem;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.95rem;
  }

  .sample-btn {
    padding: 0.5rem 1rem;
    background: #e5e7eb;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.9rem;
  }

  textarea {
    width: 100%;
    padding: 1rem;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-family: inherit;
    font-size: 0.95rem;
    resize: vertical;
    margin-bottom: 1rem;
  }

  .analyze-btn {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .analyze-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error-msg {
    color: #dc2626;
    margin-top: 1rem;
    text-align: center;
  }

  .demo-result {
    margin-top: 2rem;
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }

  .result-header {
    display: flex;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid #e5e7eb;
  }

  .risk-score {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    background: #f3f4f6;
    border-radius: 12px;
    border-left: 4px solid var(--risk-color);
  }

  .risk-score .score {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--risk-color);
  }

  .risk-score .label {
    font-size: 0.75rem;
    color: #6b7280;
    text-transform: uppercase;
  }

  .risk-badge {
    padding: 0.5rem 1rem;
    color: white;
    font-weight: 700;
    font-size: 0.85rem;
    border-radius: 20px;
  }

  .processing-time {
    margin-left: auto;
    color: #9ca3af;
    font-size: 0.85rem;
  }

  h4 {
    font-size: 1.1rem;
    margin-bottom: 0.75rem;
    color: #111827;
  }

  .summary {
    margin-bottom: 1.5rem;
  }

  .summary p {
    color: #374151;
    line-height: 1.6;
  }

  .red-flags {
    background: #fef2f2;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1.5rem;
  }

  .red-flags h4 {
    color: #991b1b;
  }

  .red-flags ul {
    margin: 0;
    padding-left: 1.5rem;
  }

  .red-flags li {
    color: #7f1d1d;
    margin-bottom: 0.25rem;
  }

  .clauses {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .clause {
    padding: 1rem;
    background: #f9fafb;
    border-radius: 8px;
    border-left: 4px solid var(--clause-color);
  }

  .clause-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .clause-type {
    font-weight: 600;
    text-transform: capitalize;
    color: #374151;
  }

  .clause-risk {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--clause-color);
  }

  .clause-text {
    font-style: italic;
    color: #6b7280;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
  }

  .clause-explanation {
    color: #374151;
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
  }

  .clause-recommendation {
    background: #ecfdf5;
    padding: 0.5rem;
    border-radius: 4px;
    color: #047857;
    font-size: 0.9rem;
  }
</style>
