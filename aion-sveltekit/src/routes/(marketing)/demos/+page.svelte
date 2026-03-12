<script lang="ts">
  import {
    DocumentAnalyzerDemo,
    ThreatProfileDemo,
    ROICalculatorDemo,
    AgentChatDemo,
  } from '$lib/components';

  type DemoTab = 'document' | 'threat' | 'roi' | 'agent';
  let activeTab: DemoTab = 'document';

  const tabs = [
    { id: 'document', label: 'Document Intelligence', icon: '🔍' },
    { id: 'threat', label: 'Threat Profile', icon: '🎯' },
    { id: 'roi', label: 'ROI Calculator', icon: '📊' },
    { id: 'agent', label: 'AI Agent', icon: '🤖' },
  ] as const;
</script>

<svelte:head>
  <title>Live Demos | EchoWorks AI</title>
</svelte:head>

<div class="demos-page">
  <div class="page-header">
    <h1>Experience Our AI in Action</h1>
    <p>Try our products live. No signup required.</p>
  </div>

  <div class="tabs">
    {#each tabs as tab}
      <button
        class="tab"
        class:active={activeTab === tab.id}
        on:click={() => (activeTab = tab.id)}
      >
        <span class="tab-icon">{tab.icon}</span>
        <span class="tab-label">{tab.label}</span>
      </button>
    {/each}
  </div>

  <div class="demo-content">
    {#if activeTab === 'document'}
      <DocumentAnalyzerDemo />
    {:else if activeTab === 'threat'}
      <ThreatProfileDemo />
    {:else if activeTab === 'roi'}
      <ROICalculatorDemo />
    {:else if activeTab === 'agent'}
      <AgentChatDemo />
    {/if}
  </div>

  <div class="cta-banner">
    <div class="cta-content">
      <h3>Ready to transform your operations?</h3>
      <p>Schedule a personalized demo to see how AION OS can work for your business.</p>
    </div>
    <a href="/contact" class="cta-btn">Book a Demo</a>
  </div>
</div>

<style>
  .demos-page {
    min-height: 100vh;
    background: #f9fafb;
    padding-bottom: 4rem;
  }

  .page-header {
    text-align: center;
    padding: 4rem 2rem 2rem;
    background: linear-gradient(135deg, #1e3a5f, #0f172a);
    color: white;
  }

  .page-header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }

  .page-header p {
    color: rgba(255, 255, 255, 0.7);
    font-size: 1.1rem;
  }

  .tabs {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    padding: 1rem;
    background: white;
    border-bottom: 1px solid #e5e7eb;
    flex-wrap: wrap;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    border: 2px solid transparent;
    border-radius: 8px;
    background: #f3f4f6;
    cursor: pointer;
    transition: all 0.2s;
  }

  .tab:hover {
    background: #e5e7eb;
  }

  .tab.active {
    background: white;
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .tab-icon {
    font-size: 1.25rem;
  }

  .tab-label {
    font-weight: 500;
  }

  .demo-content {
    padding: 2rem 0;
  }

  .cta-banner {
    max-width: 900px;
    margin: 2rem auto;
    padding: 2rem;
    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    border-radius: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 2rem;
    color: white;
  }

  .cta-content h3 {
    font-size: 1.5rem;
    margin-bottom: 0.25rem;
  }

  .cta-content p {
    opacity: 0.9;
  }

  .cta-btn {
    padding: 1rem 2rem;
    background: white;
    color: #1d4ed8;
    text-decoration: none;
    border-radius: 8px;
    font-weight: 600;
    white-space: nowrap;
  }

  @media (max-width: 768px) {
    .page-header h1 {
      font-size: 1.75rem;
    }

    .tab-label {
      display: none;
    }

    .tab {
      padding: 0.75rem;
    }

    .cta-banner {
      flex-direction: column;
      text-align: center;
      margin: 2rem 1rem;
    }
  }
</style>
