<script lang="ts">
  const products = [
    {
      id: 'document-intelligence',
      icon: '🔍',
      title: 'Document Intelligence',
      tagline: 'AI-Powered Contract Analysis',
      description: 'Analyze contracts, agreements, and legal documents in seconds. Extract key clauses, identify risks, and get actionable summaries.',
      features: [
        'Clause extraction and classification',
        'Risk scoring and red flags',
        'Obligation tracking',
        'Key terms identification',
        'Multi-document comparison',
        'Custom taxonomy support',
      ],
      useCases: ['Contract review', 'Due diligence', 'Compliance audits', 'M&A analysis'],
      metrics: { time: '90%', accuracy: '98.5%', documents: '10K+/day' },
    },
    {
      id: 'threat-profile',
      icon: '🎯',
      title: 'Threat Profiling',
      tagline: 'Composite Risk Assessment',
      description: 'Generate comprehensive threat profiles across legal, operational, regulatory, and financial dimensions. Get prioritized recommendations.',
      features: [
        'Multi-dimensional risk scoring',
        'Industry benchmarking',
        'Threat prioritization',
        'Mitigation recommendations',
        'Trend analysis',
        'Custom risk taxonomies',
      ],
      useCases: ['Vendor assessment', 'Deal evaluation', 'Portfolio risk', 'Compliance monitoring'],
      metrics: { dimensions: '5+', threats: '50+', accuracy: '97%' },
    },
    {
      id: 'ai-agents',
      icon: '🤖',
      title: 'Custom AI Agents',
      tagline: 'Specialized AI Assistants',
      description: 'Deploy domain-specific AI agents for legal, risk, and compliance tasks. Available 24/7, trained on your terminology and processes.',
      features: [
        'Legal analyst agent',
        'Risk advisor agent',
        'Compliance officer agent',
        'Research assistant',
        'Custom persona creation',
        'Context-aware responses',
      ],
      useCases: ['First-line legal advice', 'Policy Q&A', 'Research assistance', 'Training support'],
      metrics: { response: '<3s', availability: '24/7', accuracy: '95%' },
    },
    {
      id: 'analytics',
      icon: '📊',
      title: 'AI Analytics',
      tagline: 'Strategic Intelligence',
      description: 'Transform unstructured data into actionable insights. Pattern detection, trend analysis, and predictive modeling for better decisions.',
      features: [
        'Pattern recognition',
        'Trend analysis',
        'Predictive modeling',
        'Custom dashboards',
        'Automated reporting',
        'Anomaly detection',
      ],
      useCases: ['Matter trends', 'Spend analysis', 'Risk forecasting', 'Performance metrics'],
      metrics: { insights: 'Real-time', accuracy: '96%', sources: 'Unlimited' },
    },
  ];
</script>

<svelte:head>
  <title>Products | EchoWorks AI</title>
</svelte:head>

<div class="products-page">
  <!-- Header -->
  <section class="page-header">
    <div class="header-content">
      <span class="page-badge">Products</span>
      <h1>AI Solutions Built for Enterprise</h1>
      <p>Four powerful products working together to transform how your team handles documents, risk, and compliance.</p>
    </div>
  </section>

  <!-- Products Detail -->
  <section class="products-detail">
    <div class="container">
      {#each products as product, index}
        <div class="product-section" id={product.id}>
          <div class="product-content" class:reverse={index % 2 === 1}>
            <div class="product-info">
              <div class="product-icon">{product.icon}</div>
              <h2>{product.title}</h2>
              <p class="tagline">{product.tagline}</p>
              <p class="description">{product.description}</p>
              
              <div class="features-grid">
                {#each product.features as feature}
                  <div class="feature">
                    <span class="check">✓</span>
                    <span>{feature}</span>
                  </div>
                {/each}
              </div>
              
              <div class="use-cases">
                <span class="use-case-label">Use Cases:</span>
                {#each product.useCases as useCase}
                  <span class="use-case-tag">{useCase}</span>
                {/each}
              </div>
              
              <a href="/demos" class="btn-try">Try Live Demo →</a>
            </div>
            
            <div class="product-metrics">
              <div class="metrics-card">
                {#each Object.entries(product.metrics) as [key, value]}
                  <div class="metric">
                    <span class="metric-value">{value}</span>
                    <span class="metric-label">{key.charAt(0).toUpperCase() + key.slice(1)}</span>
                  </div>
                {/each}
              </div>
            </div>
          </div>
        </div>
      {/each}
    </div>
  </section>

  <!-- CTA -->
  <section class="cta-section">
    <div class="container">
      <div class="cta-card">
        <h2>Ready to See These in Action?</h2>
        <p>Try our live demos with no signup required, or schedule a personalized walkthrough.</p>
        <div class="cta-buttons">
          <a href="/demos" class="btn-primary">Try Live Demos</a>
          <a href="/pricing" class="btn-secondary">View Pricing</a>
        </div>
      </div>
    </div>
  </section>
</div>

<style>
  .products-page {
    background: #f9fafb;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1.5rem;
  }

  /* Header */
  .page-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
    color: white;
    padding: 6rem 1.5rem 4rem;
    text-align: center;
  }

  .header-content {
    max-width: 700px;
    margin: 0 auto;
  }

  .page-badge {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 100px;
    font-size: 0.85rem;
    margin-bottom: 1rem;
  }

  .page-header h1 {
    font-size: 2.75rem;
    font-weight: 700;
    margin-bottom: 1rem;
  }

  .page-header p {
    font-size: 1.15rem;
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.6;
  }

  /* Products Detail */
  .products-detail {
    padding: 4rem 0;
  }

  .product-section {
    padding: 4rem 0;
    border-bottom: 1px solid #e5e7eb;
  }

  .product-section:last-child {
    border-bottom: none;
  }

  .product-content {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 4rem;
    align-items: center;
  }

  .product-content.reverse {
    grid-template-columns: 1fr 1.5fr;
  }

  .product-content.reverse .product-info {
    order: 2;
  }

  .product-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .product-info h2 {
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.5rem;
  }

  .tagline {
    font-size: 1.1rem;
    color: #3b82f6;
    font-weight: 500;
    margin-bottom: 1rem;
  }

  .description {
    font-size: 1.05rem;
    color: #4b5563;
    line-height: 1.7;
    margin-bottom: 1.5rem;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }

  .feature {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.95rem;
    color: #374151;
  }

  .check {
    color: #059669;
    font-weight: 700;
  }

  .use-cases {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
  }

  .use-case-label {
    font-size: 0.9rem;
    color: #6b7280;
  }

  .use-case-tag {
    padding: 0.35rem 0.75rem;
    background: #eff6ff;
    color: #3b82f6;
    font-size: 0.8rem;
    font-weight: 500;
    border-radius: 100px;
  }

  .btn-try {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    background: #3b82f6;
    color: white;
    text-decoration: none;
    font-weight: 600;
    border-radius: 8px;
    transition: all 0.2s;
  }

  .btn-try:hover {
    background: #2563eb;
  }

  .metrics-card {
    background: white;
    padding: 2rem;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .metric {
    text-align: center;
    padding: 1rem;
    background: #f9fafb;
    border-radius: 12px;
  }

  .metric-value {
    display: block;
    font-size: 2rem;
    font-weight: 700;
    color: #3b82f6;
    margin-bottom: 0.25rem;
  }

  .metric-label {
    font-size: 0.85rem;
    color: #6b7280;
    text-transform: capitalize;
  }

  /* CTA */
  .cta-section {
    padding: 4rem 0;
  }

  .cta-card {
    background: linear-gradient(135deg, #3b82f6, #1d4ed8);
    padding: 3rem;
    border-radius: 20px;
    text-align: center;
    color: white;
  }

  .cta-card h2 {
    font-size: 1.75rem;
    margin-bottom: 0.75rem;
  }

  .cta-card p {
    color: rgba(255, 255, 255, 0.85);
    margin-bottom: 1.5rem;
  }

  .cta-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  .btn-primary {
    padding: 0.9rem 2rem;
    background: white;
    color: #1d4ed8;
    text-decoration: none;
    font-weight: 600;
    border-radius: 10px;
    transition: all 0.2s;
  }

  .btn-primary:hover {
    transform: translateY(-2px);
  }

  .btn-secondary {
    padding: 0.9rem 2rem;
    background: transparent;
    color: white;
    text-decoration: none;
    font-weight: 600;
    border-radius: 10px;
    border: 2px solid rgba(255, 255, 255, 0.5);
    transition: all 0.2s;
  }

  .btn-secondary:hover {
    border-color: white;
    background: rgba(255, 255, 255, 0.1);
  }

  @media (max-width: 900px) {
    .product-content,
    .product-content.reverse {
      grid-template-columns: 1fr;
      gap: 2rem;
    }

    .product-content.reverse .product-info {
      order: 0;
    }

    .features-grid {
      grid-template-columns: 1fr;
    }

    .page-header h1 {
      font-size: 2rem;
    }
  }
</style>
