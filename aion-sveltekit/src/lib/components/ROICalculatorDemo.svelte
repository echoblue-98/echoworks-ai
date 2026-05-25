<script lang="ts">
  import { leads, type ROIResult } from '$lib/api';

  let companySize = 50;
  let avgContractValue = 25000;
  let contractsPerMonth = 10;
  let hoursPerContract = 4;
  let hourlyRate = 150;
  
  let result: ROIResult | null = null;
  let loading = false;
  let error = '';

  async function calculateROI() {
    loading = true;
    error = '';
    result = null;

    try {
      result = await leads.calculateROI({
        company_size: companySize,
        avg_contract_value: avgContractValue,
        contracts_per_month: contractsPerMonth,
        hours_per_contract: hoursPerContract,
        hourly_rate: hourlyRate,
      });
    } catch (e) {
      error = e instanceof Error ? e.message : 'Calculation failed';
    } finally {
      loading = false;
    }
  }

  function formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0,
    }).format(value);
  }
</script>

<div class="demo-container">
  <div class="demo-header">
    <h2>📊 ROI Calculator</h2>
    <p>See how much time and money AION OS can save your organization.</p>
  </div>

  <div class="calculator-layout">
    <div class="inputs-panel">
      <div class="input-group">
        <label for="companySize">
          <span class="label-text">Company Size</span>
          <span class="label-value">{companySize} employees</span>
        </label>
        <input type="range" id="companySize" bind:value={companySize} min="10" max="500" step="10" />
      </div>

      <div class="input-group">
        <label for="avgContractValue">
          <span class="label-text">Average Contract Value</span>
          <span class="label-value">{formatCurrency(avgContractValue)}</span>
        </label>
        <input type="range" id="avgContractValue" bind:value={avgContractValue} min="5000" max="500000" step="5000" />
      </div>

      <div class="input-group">
        <label for="contractsPerMonth">
          <span class="label-text">Contracts per Month</span>
          <span class="label-value">{contractsPerMonth}</span>
        </label>
        <input type="range" id="contractsPerMonth" bind:value={contractsPerMonth} min="1" max="100" step="1" />
      </div>

      <div class="input-group">
        <label for="hoursPerContract">
          <span class="label-text">Hours per Contract Review</span>
          <span class="label-value">{hoursPerContract} hours</span>
        </label>
        <input type="range" id="hoursPerContract" bind:value={hoursPerContract} min="1" max="20" step="1" />
      </div>

      <div class="input-group">
        <label for="hourlyRate">
          <span class="label-text">Attorney/Analyst Hourly Rate</span>
          <span class="label-value">{formatCurrency(hourlyRate)}/hr</span>
        </label>
        <input type="range" id="hourlyRate" bind:value={hourlyRate} min="50" max="500" step="25" />
      </div>

      <button class="calculate-btn" on:click={calculateROI} disabled={loading}>
        {loading ? 'Calculating...' : 'Calculate ROI'}
      </button>

      {#if error}
        <div class="error-msg">{error}</div>
      {/if}
    </div>

    <div class="results-panel">
      {#if result}
        <div class="savings-highlight">
          <div class="savings-amount">{formatCurrency(result.annual_savings)}</div>
          <div class="savings-label">Annual Savings</div>
        </div>

        <div class="metrics-grid">
          <div class="metric-card">
            <span class="metric-value">{result.hours_saved.toLocaleString()}</span>
            <span class="metric-label">Hours Saved Annually</span>
          </div>
          <div class="metric-card">
            <span class="metric-value">{result.roi_percentage.toFixed(0)}%</span>
            <span class="metric-label">Return on Investment</span>
          </div>
          <div class="metric-card">
            <span class="metric-value">{result.payback_months.toFixed(1)} mo</span>
            <span class="metric-label">Payback Period</span>
          </div>
          <div class="metric-card">
            <span class="metric-value">{formatCurrency(result.monthly_savings)}</span>
            <span class="metric-label">Monthly Savings</span>
          </div>
        </div>

        <div class="breakdown">
          <h4>Investment Breakdown</h4>
          <div class="breakdown-row">
            <span>Current Annual Cost</span>
            <span>{formatCurrency(result.current_cost)}</span>
          </div>
          <div class="breakdown-row">
            <span>AION OS Annual Cost</span>
            <span>{formatCurrency(result.aion_cost)}</span>
          </div>
          <div class="breakdown-row highlight">
            <span>Net Annual Benefit</span>
            <span class="positive">{formatCurrency(result.annual_savings)}</span>
          </div>
        </div>

        <div class="cta-section">
          <p>Ready to start saving?</p>
          <button class="cta-btn">Schedule Demo</button>
        </div>
      {:else}
        <div class="placeholder">
          <div class="placeholder-icon">📈</div>
          <p>Adjust the sliders and click Calculate to see your potential ROI</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .demo-container {
    max-width: 1100px;
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

  .calculator-layout {
    display: grid;
    grid-template-columns: 1fr 1.2fr;
    gap: 2rem;
  }

  .inputs-panel {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }

  .input-group {
    margin-bottom: 1.5rem;
  }

  .input-group label {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
  }

  .label-text {
    font-size: 0.9rem;
    color: #374151;
  }

  .label-value {
    font-weight: 600;
    color: #3b82f6;
  }

  input[type="range"] {
    width: 100%;
    height: 8px;
    -webkit-appearance: none;
    background: #e5e7eb;
    border-radius: 4px;
    outline: none;
  }

  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 20px;
    height: 20px;
    background: #3b82f6;
    border-radius: 50%;
    cursor: pointer;
  }

  .calculate-btn {
    width: 100%;
    padding: 1rem;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    margin-top: 0.5rem;
  }

  .calculate-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error-msg {
    color: #dc2626;
    margin-top: 1rem;
    text-align: center;
  }

  .results-panel {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }

  .placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #9ca3af;
    text-align: center;
  }

  .placeholder-icon {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }

  .savings-highlight {
    text-align: center;
    padding: 2rem;
    background: linear-gradient(135deg, #ecfdf5, #d1fae5);
    border-radius: 12px;
    margin-bottom: 1.5rem;
  }

  .savings-amount {
    font-size: 3rem;
    font-weight: 700;
    color: #059669;
  }

  .savings-label {
    font-size: 1rem;
    color: #047857;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .metric-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    background: #f9fafb;
    border-radius: 8px;
  }

  .metric-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
  }

  .metric-label {
    font-size: 0.8rem;
    color: #6b7280;
    text-align: center;
  }

  .breakdown {
    padding: 1rem;
    background: #f9fafb;
    border-radius: 8px;
    margin-bottom: 1.5rem;
  }

  .breakdown h4 {
    font-size: 0.9rem;
    margin-bottom: 0.75rem;
    color: #374151;
  }

  .breakdown-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    font-size: 0.9rem;
    color: #6b7280;
  }

  .breakdown-row.highlight {
    border-top: 1px solid #e5e7eb;
    padding-top: 0.75rem;
    margin-top: 0.25rem;
    font-weight: 600;
    color: #111827;
  }

  .positive {
    color: #059669;
  }

  .cta-section {
    text-align: center;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }

  .cta-section p {
    color: #6b7280;
    margin-bottom: 0.75rem;
  }

  .cta-btn {
    padding: 0.75rem 2rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
  }

  @media (max-width: 768px) {
    .calculator-layout {
      grid-template-columns: 1fr;
    }
  }
</style>
