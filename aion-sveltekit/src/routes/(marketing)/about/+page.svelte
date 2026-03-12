<script lang="ts">
  const values = [
    {
      icon: '🔒',
      title: 'Privacy First',
      description: 'Your data never leaves your infrastructure. We built AI that works for you, not the other way around.',
    },
    {
      icon: '⚡',
      title: 'Real Results',
      description: 'We measure success by hours saved and risks avoided, not by features shipped.',
    },
    {
      icon: '🤝',
      title: 'Partnership',
      description: 'We succeed when you succeed. Our team becomes an extension of yours.',
    },
    {
      icon: '🎯',
      title: 'Simplicity',
      description: 'Complex problems deserve elegant solutions. We hide the complexity, not the capability.',
    },
  ];

  const team = [
    {
      name: 'Founder',
      role: 'CEO',
      bio: 'Building AI that respects your data.',
    },
  ];

  const milestones = [
    { year: '2024', event: 'Founded with a mission to bring secure AI to enterprises' },
    { year: '2024', event: 'AION OS v1.0 launched — document intelligence for law firms' },
    { year: '2025', event: 'Expanded to threat profiling and custom AI agents' },
    { year: '2026', event: 'Serving Fortune 500 legal and risk teams' },
  ];
</script>

<svelte:head>
  <title>About | EchoWorks AI</title>
</svelte:head>

<div class="about-page">
  <!-- Header -->
  <section class="page-header">
    <div class="header-content">
      <span class="page-badge">About Us</span>
      <h1>AI That Stays On Your Side</h1>
      <p>We're building the future of enterprise AI — where powerful capabilities meet uncompromising privacy.</p>
    </div>
  </section>

  <!-- Mission -->
  <section class="mission-section">
    <div class="container">
      <div class="mission-content">
        <div class="mission-text">
          <h2>Our Mission</h2>
          <p class="lead">
            Enterprises deserve AI that works on their terms — on their infrastructure, with their data, under their control.
          </p>
          <p>
            We started EchoWorks AI because we saw a fundamental problem: the most powerful AI tools required 
            organizations to send their most sensitive data to external servers. For legal teams, risk managers, 
            and compliance officers, this was a non-starter.
          </p>
          <p>
            So we built something different. AION OS delivers enterprise-grade AI that runs entirely on-premise. 
            No data ever leaves your network. No cloud dependencies. No compromises.
          </p>
        </div>
        <div class="mission-stats">
          <div class="stat-card">
            <span class="stat-value">100%</span>
            <span class="stat-label">On-Premise</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">0</span>
            <span class="stat-label">Data Sent to Cloud</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">∞</span>
            <span class="stat-label">Your Control</span>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- Values -->
  <section class="values-section">
    <div class="container">
      <div class="section-header">
        <h2>What We Stand For</h2>
      </div>
      <div class="values-grid">
        {#each values as value}
          <div class="value-card">
            <div class="value-icon">{value.icon}</div>
            <h3>{value.title}</h3>
            <p>{value.description}</p>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Timeline -->
  <section class="timeline-section">
    <div class="container">
      <div class="section-header">
        <h2>Our Journey</h2>
      </div>
      <div class="timeline">
        {#each milestones as milestone, i}
          <div class="milestone">
            <div class="milestone-marker">
              <span class="year">{milestone.year}</span>
            </div>
            <div class="milestone-content">
              <p>{milestone.event}</p>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Tech Stack -->
  <section class="tech-section">
    <div class="container">
      <div class="tech-card">
        <h2>Built on Proven Technology</h2>
        <p>
          AION OS runs on your infrastructure using industry-standard technologies. 
          Deploy with Docker on any cloud or on-premise environment. Air-gapped? No problem.
        </p>
        <div class="tech-badges">
          <span class="tech-badge">Docker</span>
          <span class="tech-badge">Python</span>
          <span class="tech-badge">PostgreSQL</span>
          <span class="tech-badge">Local LLMs</span>
          <span class="tech-badge">REST API</span>
          <span class="tech-badge">Air-Gap Ready</span>
        </div>
      </div>
    </div>
  </section>

  <!-- CTA -->
  <section class="cta-section">
    <div class="container">
      <div class="cta-content">
        <h2>Join Us in Redefining Enterprise AI</h2>
        <p>Whether you're looking to transform your legal operations or build the future with us, we'd love to connect.</p>
        <div class="cta-buttons">
          <a href="/contact" class="btn-primary">Get in Touch</a>
          <a href="/demos" class="btn-secondary">See the Product</a>
        </div>
      </div>
    </div>
  </section>
</div>

<style>
  .about-page {
    background: #f9fafb;
  }

  .container {
    max-width: 1100px;
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

  /* Mission */
  .mission-section {
    padding: 5rem 0;
    background: white;
  }

  .mission-content {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 4rem;
    align-items: center;
  }

  .mission-text h2 {
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 1.5rem;
  }

  .lead {
    font-size: 1.2rem;
    color: #374151;
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }

  .mission-text p {
    color: #6b7280;
    line-height: 1.7;
    margin-bottom: 1rem;
  }

  .mission-stats {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .stat-card {
    background: linear-gradient(135deg, #eff6ff, #f0fdf4);
    padding: 1.5rem;
    border-radius: 16px;
    text-align: center;
  }

  .stat-value {
    display: block;
    font-size: 2.5rem;
    font-weight: 700;
    color: #3b82f6;
    margin-bottom: 0.25rem;
  }

  .stat-label {
    font-size: 0.9rem;
    color: #6b7280;
  }

  /* Section Header */
  .section-header {
    text-align: center;
    margin-bottom: 3rem;
  }

  .section-header h2 {
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
  }

  /* Values */
  .values-section {
    padding: 5rem 0;
  }

  .values-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.5rem;
  }

  .value-card {
    background: white;
    padding: 2rem;
    border-radius: 16px;
    border: 1px solid #e5e7eb;
    text-align: center;
  }

  .value-icon {
    font-size: 2.5rem;
    margin-bottom: 1rem;
  }

  .value-card h3 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.75rem;
  }

  .value-card p {
    font-size: 0.95rem;
    color: #6b7280;
    line-height: 1.6;
  }

  /* Timeline */
  .timeline-section {
    padding: 5rem 0;
    background: white;
  }

  .timeline {
    max-width: 700px;
    margin: 0 auto;
    position: relative;
  }

  .timeline::before {
    content: '';
    position: absolute;
    left: 60px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #e5e7eb;
  }

  .milestone {
    display: flex;
    gap: 2rem;
    margin-bottom: 2rem;
    position: relative;
  }

  .milestone-marker {
    width: 120px;
    flex-shrink: 0;
    text-align: right;
    position: relative;
  }

  .milestone-marker::after {
    content: '';
    position: absolute;
    right: -30px;
    top: 50%;
    transform: translateY(-50%);
    width: 12px;
    height: 12px;
    background: #3b82f6;
    border-radius: 50%;
    border: 3px solid white;
    box-shadow: 0 0 0 2px #e5e7eb;
  }

  .year {
    font-weight: 700;
    color: #3b82f6;
    font-size: 1.1rem;
  }

  .milestone-content {
    flex: 1;
    padding: 0.5rem 0 0.5rem 1rem;
  }

  .milestone-content p {
    color: #374151;
    font-size: 1rem;
  }

  /* Tech */
  .tech-section {
    padding: 5rem 0;
  }

  .tech-card {
    background: linear-gradient(135deg, #1e3a5f, #0f172a);
    padding: 3rem;
    border-radius: 20px;
    text-align: center;
    color: white;
  }

  .tech-card h2 {
    font-size: 1.75rem;
    margin-bottom: 1rem;
  }

  .tech-card > p {
    color: rgba(255, 255, 255, 0.8);
    max-width: 600px;
    margin: 0 auto 2rem;
    line-height: 1.6;
  }

  .tech-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
    justify-content: center;
  }

  .tech-badge {
    padding: 0.5rem 1rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 100px;
    font-size: 0.9rem;
  }

  /* CTA */
  .cta-section {
    padding: 5rem 0;
    background: white;
  }

  .cta-content {
    text-align: center;
    max-width: 600px;
    margin: 0 auto;
  }

  .cta-content h2 {
    font-size: 2rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 1rem;
  }

  .cta-content p {
    color: #6b7280;
    margin-bottom: 2rem;
    line-height: 1.6;
  }

  .cta-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
  }

  .btn-primary {
    padding: 0.9rem 2rem;
    background: #3b82f6;
    color: white;
    text-decoration: none;
    font-weight: 600;
    border-radius: 10px;
  }

  .btn-secondary {
    padding: 0.9rem 2rem;
    border: 2px solid #e5e7eb;
    color: #374151;
    text-decoration: none;
    font-weight: 600;
    border-radius: 10px;
  }

  @media (max-width: 900px) {
    .mission-content {
      grid-template-columns: 1fr;
      gap: 2rem;
    }

    .mission-stats {
      flex-direction: row;
    }

    .stat-card {
      flex: 1;
    }

    .values-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .page-header h1 {
      font-size: 2rem;
    }
  }

  @media (max-width: 600px) {
    .values-grid {
      grid-template-columns: 1fr;
    }

    .mission-stats {
      flex-direction: column;
    }

    .timeline::before {
      left: 40px;
    }

    .milestone-marker {
      width: 80px;
    }
  }
</style>
