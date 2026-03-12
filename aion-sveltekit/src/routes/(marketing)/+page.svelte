<script lang="ts">
  import { onMount } from 'svelte';

  const products = [
    {
      icon: '🔍',
      title: 'Document Intelligence',
      description: 'AI-powered contract analysis that identifies risks, extracts clauses, and summarizes documents in seconds.',
      highlight: '90% faster reviews',
    },
    {
      icon: '🎯',
      title: 'Threat Profiling',
      description: 'Composite risk scoring across legal, operational, and compliance dimensions with actionable recommendations.',
      highlight: 'Real-time assessment',
    },
    {
      icon: '🤖',
      title: 'Custom AI Agents',
      description: 'Specialized AI assistants for legal, risk, and compliance tasks. Available 24/7, trained on your domain.',
      highlight: 'Domain-specific',
    },
    {
      icon: '📊',
      title: 'AI Analytics',
      description: 'Turn unstructured data into strategic insights. Pattern detection, trend analysis, and predictive modeling.',
      highlight: 'Predictive insights',
    },
  ];

  const stats = [
    { value: '90%', label: 'Faster Document Review' },
    { value: '60%', label: 'Cost Reduction' },
    { value: '99.9%', label: 'Data Stays On-Premise' },
    { value: '24/7', label: 'AI Availability' },
  ];

  const testimonials = [
    {
      quote: "EchoWorks transformed how we handle contract review. What took days now takes hours.",
      author: "Sarah Chen",
      role: "General Counsel",
      company: "TechCorp Industries",
    },
    {
      quote: "The threat profiling alone has saved us from three major compliance issues this year.",
      author: "Michael Roberts",
      role: "Chief Risk Officer", 
      company: "Pacific Financial Group",
    },
    {
      quote: "Finally, AI that stays on our servers. No data leakage concerns, just results.",
      author: "Jennifer Walsh",
      role: "Managing Partner",
      company: "Walsh & Associates LLP",
    },
  ];

  const logos = [
    'Fortune 500 Law Firm',
    'Global Bank',
    'Healthcare System',
    'Tech Enterprise',
    'Insurance Co.',
  ];

  let visible = $state(false);
  onMount(() => {
    visible = true;
  });
</script>

<svelte:head>
  <title>EchoWorks AI - Enterprise AI for Legal & Risk Teams</title>
</svelte:head>

<div class="home-page" class:visible>
  <!-- Hero Section -->
  <section class="hero">
    <div class="hero-bg"></div>
    <div class="hero-content">
      <div class="hero-badge">
        <span class="badge-icon">🔒</span>
        <span>100% On-Premise — Your Data Never Leaves</span>
      </div>
      <h1>AI That Works <span class="gradient-text">For You</span></h1>
      <p class="hero-subtitle">
        Enterprise-grade AI solutions for legal, risk, and compliance teams. 
        Analyze contracts, assess threats, and automate workflows — all while keeping your data secure.
      </p>
      <div class="hero-cta">
        <a href="/demos" class="btn-primary">Try Live Demos</a>
        <a href="/contact" class="btn-secondary">Book a Demo</a>
      </div>
      <div class="hero-stats">
        {#each stats as stat}
          <div class="stat">
            <span class="stat-value">{stat.value}</span>
            <span class="stat-label">{stat.label}</span>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Logo Bar -->
  <section class="logo-bar">
    <p>Trusted by leading organizations</p>
    <div class="logos">
      {#each logos as logo}
        <div class="logo-placeholder">{logo}</div>
      {/each}
    </div>
  </section>

  <!-- Products Section -->
  <section class="products-section">
    <div class="section-container">
      <div class="section-header">
        <span class="section-badge">Products</span>
        <h2>AI Solutions That Deliver Results</h2>
        <p>Four powerful products. One unified platform. Zero data exposure.</p>
      </div>

      <div class="products-grid">
        {#each products as product}
          <div class="product-card">
            <div class="product-icon">{product.icon}</div>
            <h3>{product.title}</h3>
            <p>{product.description}</p>
            <span class="product-highlight">{product.highlight}</span>
          </div>
        {/each}
      </div>

      <div class="products-cta">
        <a href="/products" class="btn-outline">Explore All Products →</a>
      </div>
    </div>
  </section>

  <!-- How It Works -->
  <section class="how-section">
    <div class="section-container">
      <div class="section-header">
        <span class="section-badge">How It Works</span>
        <h2>From Setup to ROI in Days, Not Months</h2>
      </div>

      <div class="steps-grid">
        <div class="step">
          <div class="step-number">1</div>
          <h3>Deploy On-Premise</h3>
          <p>Install on your infrastructure in under an hour. Docker-based, air-gapped capable.</p>
        </div>
        <div class="step">
          <div class="step-number">2</div>
          <h3>Connect Your Data</h3>
          <p>Integrate with your document management, email, and case systems securely.</p>
        </div>
        <div class="step">
          <div class="step-number">3</div>
          <h3>Start Analyzing</h3>
          <p>Upload contracts, run threat assessments, chat with AI agents immediately.</p>
        </div>
        <div class="step">
          <div class="step-number">4</div>
          <h3>Measure Impact</h3>
          <p>Track time saved, risks avoided, and ROI through built-in analytics.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- Demo CTA Section -->
  <section class="demo-section">
    <div class="section-container">
      <div class="demo-card">
        <div class="demo-content">
          <h2>See It In Action</h2>
          <p>Try our AI products live — no signup required. Upload a contract, generate a threat profile, or chat with our AI agents.</p>
          <a href="/demos" class="btn-primary">Launch Live Demos</a>
        </div>
        <div class="demo-preview">
          <div class="demo-mockup">
            <div class="mockup-header">
              <span class="dot red"></span>
              <span class="dot yellow"></span>
              <span class="dot green"></span>
            </div>
            <div class="mockup-body">
              <div class="mockup-line short"></div>
              <div class="mockup-line"></div>
              <div class="mockup-line medium"></div>
              <div class="mockup-result">
                <span class="result-icon">✓</span>
                <span>12 clauses analyzed</span>
              </div>
              <div class="mockup-result warning">
                <span class="result-icon">⚠</span>
                <span>3 risk flags detected</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Testimonials -->
  <section class="testimonials-section">
    <div class="section-container">
      <div class="section-header">
        <span class="section-badge">Testimonials</span>
        <h2>What Our Clients Say</h2>
      </div>

      <div class="testimonials-grid">
        {#each testimonials as t}
          <div class="testimonial-card">
            <p class="quote">"{t.quote}"</p>
            <div class="author">
              <div class="author-avatar">{t.author.charAt(0)}</div>
              <div class="author-info">
                <span class="author-name">{t.author}</span>
                <span class="author-role">{t.role}, {t.company}</span>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Final CTA -->
  <section class="final-cta">
    <div class="section-container">
      <h2>Ready to Transform Your Operations?</h2>
      <p>Join leading organizations using EchoWorks AI to reduce risk, save time, and work smarter.</p>
      <div class="cta-buttons">
        <a href="/contact" class="btn-primary large">Schedule a Demo</a>
        <a href="/pricing" class="btn-secondary large">View Pricing</a>
      </div>
    </div>
  </section>
</div>

<style>
  .home-page {
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.6s ease, transform 0.6s ease;
  }

  .home-page.visible {
    opacity: 1;
    transform: translateY(0);
  }

  /* Hero */
  .hero {
    position: relative;
    padding: 6rem 1.5rem;
    overflow: hidden;
  }

  .hero-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 50%, #f0fdf4 100%);
    z-index: -1;
  }

  .hero-content {
    max-width: 900px;
    margin: 0 auto;
    text-align: center;
  }

  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 100px;
    font-size: 0.9rem;
    color: #374151;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  }

  h1 {
    font-size: 3.5rem;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 1.5rem;
    color: #111827;
  }

  .gradient-text {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .hero-subtitle {
    font-size: 1.25rem;
    color: #4b5563;
    max-width: 700px;
    margin: 0 auto 2rem;
    line-height: 1.6;
  }

  .hero-cta {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-bottom: 3rem;
    flex-wrap: wrap;
  }

  .btn-primary {
    padding: 0.9rem 2rem;
    background: #3b82f6;
    color: white;
    text-decoration: none;
    font-weight: 600;
    border-radius: 10px;
    transition: all 0.2s;
    display: inline-block;
  }

  .btn-primary:hover {
    background: #2563eb;
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
  }

  .btn-primary.large {
    padding: 1rem 2.5rem;
    font-size: 1.1rem;
  }

  .btn-secondary {
    padding: 0.9rem 2rem;
    background: white;
    color: #374151;
    text-decoration: none;
    font-weight: 600;
    border-radius: 10px;
    border: 2px solid #e5e7eb;
    transition: all 0.2s;
    display: inline-block;
  }

  .btn-secondary:hover {
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .btn-secondary.large {
    padding: 1rem 2.5rem;
    font-size: 1.1rem;
  }

  .btn-outline {
    padding: 0.9rem 2rem;
    color: #3b82f6;
    text-decoration: none;
    font-weight: 600;
    border-radius: 10px;
    border: 2px solid #3b82f6;
    transition: all 0.2s;
    display: inline-block;
  }

  .btn-outline:hover {
    background: #3b82f6;
    color: white;
  }

  .hero-stats {
    display: flex;
    justify-content: center;
    gap: 3rem;
    flex-wrap: wrap;
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
  }

  .stat-label {
    font-size: 0.85rem;
    color: #6b7280;
  }

  /* Logo Bar */
  .logo-bar {
    padding: 3rem 1.5rem;
    background: white;
    border-top: 1px solid #e5e7eb;
    border-bottom: 1px solid #e5e7eb;
    text-align: center;
  }

  .logo-bar p {
    font-size: 0.9rem;
    color: #9ca3af;
    margin-bottom: 1.5rem;
  }

  .logos {
    display: flex;
    justify-content: center;
    gap: 3rem;
    flex-wrap: wrap;
  }

  .logo-placeholder {
    padding: 0.75rem 1.5rem;
    background: #f9fafb;
    border-radius: 8px;
    color: #9ca3af;
    font-size: 0.85rem;
    font-weight: 500;
  }

  /* Section Containers */
  .section-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1.5rem;
  }

  .section-header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .section-badge {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    background: #eff6ff;
    color: #3b82f6;
    font-size: 0.85rem;
    font-weight: 600;
    border-radius: 100px;
    margin-bottom: 1rem;
  }

  .section-header h2 {
    font-size: 2.25rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.75rem;
  }

  .section-header p {
    font-size: 1.1rem;
    color: #6b7280;
  }

  /* Products Section */
  .products-section {
    padding: 5rem 0;
    background: #f9fafb;
  }

  .products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
  }

  .product-card {
    background: white;
    padding: 2rem;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    transition: all 0.3s;
  }

  .product-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 12px 40px rgba(59, 130, 246, 0.1);
    transform: translateY(-4px);
  }

  .product-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
  }

  .product-card h3 {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    color: #111827;
  }

  .product-card p {
    color: #6b7280;
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 1rem;
  }

  .product-highlight {
    display: inline-block;
    padding: 0.35rem 0.75rem;
    background: #ecfdf5;
    color: #059669;
    font-size: 0.8rem;
    font-weight: 600;
    border-radius: 4px;
  }

  .products-cta {
    text-align: center;
  }

  /* How Section */
  .how-section {
    padding: 5rem 0;
    background: white;
  }

  .steps-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 2rem;
  }

  .step {
    text-align: center;
    padding: 1.5rem;
  }

  .step-number {
    width: 48px;
    height: 48px;
    background: #3b82f6;
    color: white;
    font-size: 1.25rem;
    font-weight: 700;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1rem;
  }

  .step h3 {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: #111827;
  }

  .step p {
    font-size: 0.9rem;
    color: #6b7280;
    line-height: 1.5;
  }

  /* Demo Section */
  .demo-section {
    padding: 5rem 0;
    background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
  }

  .demo-card {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 3rem;
    align-items: center;
  }

  .demo-content {
    color: white;
  }

  .demo-content h2 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 1rem;
  }

  .demo-content p {
    color: rgba(255, 255, 255, 0.7);
    font-size: 1.1rem;
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }

  .demo-mockup {
    background: #1e293b;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  }

  .mockup-header {
    display: flex;
    gap: 6px;
    padding: 12px 16px;
    background: #0f172a;
  }

  .dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
  }

  .dot.red { background: #ef4444; }
  .dot.yellow { background: #f59e0b; }
  .dot.green { background: #22c55e; }

  .mockup-body {
    padding: 1.5rem;
  }

  .mockup-line {
    height: 12px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    margin-bottom: 0.75rem;
  }

  .mockup-line.short { width: 40%; }
  .mockup-line.medium { width: 70%; }

  .mockup-result {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: rgba(34, 197, 94, 0.2);
    border-radius: 6px;
    color: #22c55e;
    font-size: 0.9rem;
    margin-top: 1rem;
  }

  .mockup-result.warning {
    background: rgba(245, 158, 11, 0.2);
    color: #f59e0b;
    margin-top: 0.5rem;
  }

  /* Testimonials */
  .testimonials-section {
    padding: 5rem 0;
    background: #f9fafb;
  }

  .testimonials-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1.5rem;
  }

  .testimonial-card {
    background: white;
    padding: 2rem;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
  }

  .quote {
    font-size: 1.05rem;
    color: #374151;
    line-height: 1.6;
    margin-bottom: 1.5rem;
    font-style: italic;
  }

  .author {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .author-avatar {
    width: 48px;
    height: 48px;
    background: #3b82f6;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 1.1rem;
  }

  .author-info {
    display: flex;
    flex-direction: column;
  }

  .author-name {
    font-weight: 600;
    color: #111827;
  }

  .author-role {
    font-size: 0.85rem;
    color: #6b7280;
  }

  /* Final CTA */
  .final-cta {
    padding: 5rem 0;
    background: white;
    text-align: center;
  }

  .final-cta h2 {
    font-size: 2.25rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.75rem;
  }

  .final-cta p {
    font-size: 1.1rem;
    color: #6b7280;
    margin-bottom: 2rem;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
  }

  .cta-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  /* Responsive */
  @media (max-width: 900px) {
    h1 {
      font-size: 2.5rem;
    }

    .hero-stats {
      gap: 2rem;
    }

    .demo-card {
      grid-template-columns: 1fr;
    }

    .demo-preview {
      order: -1;
    }
  }

  @media (max-width: 600px) {
    h1 {
      font-size: 2rem;
    }

    .section-header h2 {
      font-size: 1.75rem;
    }

    .hero {
      padding: 3rem 1rem;
    }

    .hero-stats {
      flex-direction: column;
      gap: 1rem;
    }
  }
</style>
