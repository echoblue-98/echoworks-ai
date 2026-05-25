<script lang="ts">
  import { demos, type ThreatProfileResult } from '$lib/api';

  let riskFactors = ['contract_dispute', 'data_breach'];
  let industryContext = 'technology';
  let companySize = 'medium';
  let result: ThreatProfileResult | null = null;
  let loading = false;
  let error = '';

  const allRiskFactors = [
    { value: 'contract_dispute', label: 'Contract Disputes' },
    { value: 'data_breach', label: 'Data Breach Risk' },
    { value: 'regulatory_compliance', label: 'Regulatory Compliance' },
    { value: 'ip_infringement', label: 'IP Infringement' },
    { value: 'employment_issues', label: 'Employment Issues' },
    { value: 'vendor_dependency', label: 'Vendor Dependency' },
    { value: 'cyber_threat', label: 'Cyber Threats' },
    { value: 'litigation_exposure', label: 'Litigation Exposure' },
  ];

  const industries = [
    'technology',
    'healthcare',
    'finance',
    'manufacturing',
    'retail',
    'legal',
    'education',
    'energy',
  ];

  async function generateProfile() {
    if (riskFactors.length === 0) {
      error = 'Select at least one risk factor';
      return;
    }

    loading = true;
    error = '';
    result = null;

    try {
      result = await demos.generateThreatProfile({
        risk_factors: riskFactors,
        industry_context: industryContext,
        company_size: companySize,
      });
    } catch (e) {
      error = e instanceof Error ? e.message : 'Profile generation failed';
    } finally {
      loading = false;
    }
  }

  function toggleFactor(factor: string) {
    if (riskFactors.includes(factor)) {
      riskFactors = riskFactors.filter(f => f !== factor);
    } else {
      riskFactors = [...riskFactors, factor];
    }
  }

  function getScoreColor(score: number): string {
    if (score >= 80) return '#dc2626';
    if (score >= 60) return '#ea580c';
    if (score >= 40) return '#ca8a04';
    return '#16a34a';
  }

  function getPriorityColor(priority: string): string {
    switch (priority.toLowerCase()) {
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
    <h2>🎯 Threat Profile Generator</h2>
    <p>Configure your risk factors and see your organization's comprehensive threat assessment.</p>
  </div>

  <div class="demo-input">
    <div class="input-section">
      <h4>Risk Factors</h4>
      <div class="factor-grid">
        {#each allRiskFactors as factor}
          <button
            class="factor-btn"
            class:active={riskFactors.includes(factor.value)}
            on:click={() => toggleFactor(factor.value)}
          >
            {factor.label}
          </button>
        {/each}
      </div>
    </div>

    <div class="input-row">
      <div class="input-group">
        <label for="industry">Industry</label>
        <select id="industry" bind:value={industryContext}>
          {#each industries as industry}
            <option value={industry}>{industry.charAt(0).toUpperCase() + industry.slice(1)}</option>
          {/each}
        </select>
      </div>

      <div class="input-group">
        <label for="size">Company Size</label>
        <select id="size" bind:value={companySize}>
          <option value="startup">Startup (1-50)</option>
          <option value="small">Small (51-200)</option>
          <option value="medium">Medium (201-1000)</option>
          <option value="large">Large (1000+)</option>
          <option value="enterprise">Enterprise (10000+)</option>
        </select>
      </div>
    </div>

    <button class="generate-btn" on:click={generateProfile} disabled={loading}>
      {loading ? 'Generating Profile...' : 'Generate Threat Profile'}
    </button>

    {#if error}
      <div class="error-msg">{error}</div>
    {/if}
  </div>

  {#if result}
    <div class="demo-result">
      <div class="score-dashboard">
        <div class="score-card main-score" style="--score-color: {getScoreColor(result.composite_score)}">
          <div class="score-ring">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="#e5e7eb" stroke-width="8" />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke={getScoreColor(result.composite_score)}
                stroke-width="8"
                stroke-dasharray={`${result.composite_score * 2.83} 283`}
                stroke-linecap="round"
                transform="rotate(-90 50 50)"
              />
            </svg>
            <span class="score-value">{result.composite_score.toFixed(0)}</span>
          </div>
          <span class="score-label">Composite Risk Score</span>
        </div>

        <div class="dimension-scores">
          {#each result.risk_dimensions as dim}
            <div class="dimension" style="--dim-color: {getScoreColor(dim.score)}">
              <div class="dim-header">
                <span class="dim-name">{dim.dimension.replace(/_/g, ' ')}</span>
                <span class="dim-score">{dim.score.toFixed(0)}</span>
              </div>
              <div class="dim-bar">
                <div class="dim-fill" style="width: {dim.score}%"></div>
              </div>
              <p class="dim-summary">{dim.summary}</p>
            </div>
          {/each}
        </div>
      </div>

      <div class="threats-section">
        <h4>⚠️ Identified Threats ({result.threats.length})</h4>
        <div class="threats-grid">
          {#each result.threats as threat}
            <div class="threat-card" style="--threat-color: {getPriorityColor(threat.priority)}">
              <div class="threat-header">
                <span class="threat-category">{threat.category}</span>
                <span class="threat-priority">{threat.priority}</span>
              </div>
              <p class="threat-desc">{threat.description}</p>
              <div class="threat-meta">
                <span>Likelihood: {(threat.likelihood * 100).toFixed(0)}%</span>
                <span>Impact: ${threat.potential_impact.toLocaleString()}</span>
              </div>
            </div>
          {/each}
        </div>
      </div>

      <div class="recommendations-section">
        <h4>✅ Recommendations</h4>
        <div class="recommendations-list">
          {#each result.recommendations as rec, i}
            <div class="recommendation">
              <span class="rec-number">{i + 1}</span>
              <span class="rec-text">{rec}</span>
            </div>
          {/each}
        </div>
      </div>

      <div class="meta-info">
        <span>Analysis completed in {result.processing_time_ms}ms</span>
        <span>Profile ID: {result.profile_id}</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .demo-container {
    max-width: 1000px;
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

  .input-section {
    margin-bottom: 1.5rem;
  }

  h4 {
    font-size: 1rem;
    margin-bottom: 0.75rem;
    color: #374151;
  }

  .factor-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .factor-btn {
    padding: 0.5rem 1rem;
    border: 2px solid #e5e7eb;
    border-radius: 20px;
    background: white;
    color: #6b7280;
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .factor-btn:hover {
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .factor-btn.active {
    border-color: #3b82f6;
    background: #3b82f6;
    color: white;
  }

  .input-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .input-group label {
    display: block;
    font-size: 0.9rem;
    color: #374151;
    margin-bottom: 0.5rem;
  }

  .input-group select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 0.95rem;
  }

  .generate-btn {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, #8b5cf6, #6d28d9);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
  }

  .generate-btn:disabled {
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
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }

  .score-dashboard {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 2rem;
    margin-bottom: 2rem;
    padding-bottom: 2rem;
    border-bottom: 1px solid #e5e7eb;
  }

  .main-score {
    text-align: center;
  }

  .score-ring {
    position: relative;
    width: 150px;
    height: 150px;
    margin: 0 auto 0.5rem;
  }

  .score-ring svg {
    width: 100%;
    height: 100%;
  }

  .score-value {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--score-color);
  }

  .score-label {
    font-size: 0.85rem;
    color: #6b7280;
  }

  .dimension-scores {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .dimension {
    padding: 0.75rem;
    background: #f9fafb;
    border-radius: 8px;
  }

  .dim-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.25rem;
  }

  .dim-name {
    font-weight: 600;
    text-transform: capitalize;
    color: #374151;
    font-size: 0.9rem;
  }

  .dim-score {
    font-weight: 700;
    color: var(--dim-color);
  }

  .dim-bar {
    height: 6px;
    background: #e5e7eb;
    border-radius: 3px;
    margin-bottom: 0.5rem;
  }

  .dim-fill {
    height: 100%;
    background: var(--dim-color);
    border-radius: 3px;
    transition: width 0.5s ease;
  }

  .dim-summary {
    font-size: 0.8rem;
    color: #6b7280;
    margin: 0;
  }

  .threats-section, .recommendations-section {
    margin-bottom: 1.5rem;
  }

  .threats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 1rem;
  }

  .threat-card {
    padding: 1rem;
    background: #f9fafb;
    border-radius: 8px;
    border-left: 4px solid var(--threat-color);
  }

  .threat-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .threat-category {
    font-weight: 600;
    color: #374151;
  }

  .threat-priority {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--threat-color);
  }

  .threat-desc {
    font-size: 0.9rem;
    color: #6b7280;
    margin-bottom: 0.75rem;
  }

  .threat-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.8rem;
    color: #9ca3af;
  }

  .recommendations-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .recommendation {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 0.75rem;
    background: #f0fdf4;
    border-radius: 8px;
  }

  .rec-number {
    width: 24px;
    height: 24px;
    background: #22c55e;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
    flex-shrink: 0;
  }

  .rec-text {
    color: #166534;
    font-size: 0.95rem;
  }

  .meta-info {
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: #9ca3af;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }
</style>
