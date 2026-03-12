<script lang="ts">
  let billingCycle: 'monthly' | 'annual' = 'annual';

  const plans = [
    {
      name: 'Starter',
      description: 'For small teams getting started with AI',
      monthlyPrice: 499,
      annualPrice: 399,
      features: [
        '5 users included',
        '1,000 document analyses/mo',
        '100 threat profiles/mo',
        'Basic AI agent access',
        'Email support',
        'Standard SLA',
      ],
      cta: 'Start Free Trial',
      highlighted: false,
    },
    {
      name: 'Professional',
      description: 'For growing teams with advanced needs',
      monthlyPrice: 1499,
      annualPrice: 1199,
      features: [
        '25 users included',
        '10,000 document analyses/mo',
        '1,000 threat profiles/mo',
        'All AI agents + custom personas',
        'API access',
        'Priority support',
        'Custom integrations',
        '99.9% uptime SLA',
      ],
      cta: 'Start Free Trial',
      highlighted: true,
      badge: 'Most Popular',
    },
    {
      name: 'Enterprise',
      description: 'For large organizations with custom requirements',
      monthlyPrice: null,
      annualPrice: null,
      features: [
        'Unlimited users',
        'Unlimited analyses',
        'Unlimited threat profiles',
        'Custom AI model training',
        'Dedicated success manager',
        'On-premise deployment',
        'Custom integrations',
        'Enterprise SLA',
        '24/7 phone support',
      ],
      cta: 'Contact Sales',
      highlighted: false,
    },
  ];

  const faqs = [
    {
      q: 'Does my data leave my network?',
      a: 'Never. EchoWorks AI runs entirely on-premise. Your documents, analyses, and all data stay within your infrastructure.',
    },
    {
      q: 'What cloud providers do you support?',
      a: 'We support AWS, Azure, GCP, and any infrastructure that runs Docker. Air-gapped deployments are fully supported.',
    },
    {
      q: 'Can I try before I buy?',
      a: 'Yes! All plans include a 14-day free trial. Try our live demos right now — no signup required.',
    },
    {
      q: 'What happens if I exceed my limits?',
      a: "We'll notify you before you hit limits. You can upgrade anytime or purchase additional capacity at per-unit rates.",
    },
    {
      q: 'Do you offer discounts for law firms?',
      a: 'Yes, we offer special pricing for law firms, legal departments, and non-profits. Contact our sales team.',
    },
    {
      q: 'How long does deployment take?',
      a: 'Most teams are up and running in under an hour. Enterprise deployments with custom integrations typically take 1-2 weeks.',
    },
  ];

  function getPrice(plan: typeof plans[0]): string {
    if (plan.monthlyPrice === null) return 'Custom';
    const price = billingCycle === 'monthly' ? plan.monthlyPrice : plan.annualPrice;
    return `$${price.toLocaleString()}`;
  }
</script>

<svelte:head>
  <title>Pricing | EchoWorks AI</title>
</svelte:head>

<div class="pricing-page">
  <!-- Header -->
  <section class="page-header">
    <div class="header-content">
      <span class="page-badge">Pricing</span>
      <h1>Simple, Transparent Pricing</h1>
      <p>No per-seat fees. No hidden costs. No data exposure.</p>
      
      <div class="billing-toggle">
        <button class:active={billingCycle === 'monthly'} onclick={() => billingCycle = 'monthly'}>
          Monthly
        </button>
        <button class:active={billingCycle === 'annual'} onclick={() => billingCycle = 'annual'}>
          Annual <span class="save-badge">Save 20%</span>
        </button>
      </div>
    </div>
  </section>

  <!-- Plans -->
  <section class="plans-section">
    <div class="container">
      <div class="plans-grid">
        {#each plans as plan}
          <div class="plan-card" class:highlighted={plan.highlighted}>
            {#if plan.badge}
              <span class="plan-badge">{plan.badge}</span>
            {/if}
            <h3>{plan.name}</h3>
            <p class="plan-description">{plan.description}</p>
            <div class="plan-price">
              <span class="price">{getPrice(plan)}</span>
              {#if plan.monthlyPrice !== null}
                <span class="period">/month</span>
              {/if}
            </div>
            {#if billingCycle === 'annual' && plan.monthlyPrice !== null}
              <p class="annual-note">Billed annually (${(plan.annualPrice * 12).toLocaleString()}/year)</p>
            {/if}
            <ul class="features-list">
              {#each plan.features as feature}
                <li>
                  <span class="check">✓</span>
                  <span>{feature}</span>
                </li>
              {/each}
            </ul>
            <a href={plan.name === 'Enterprise' ? '/contact' : '/contact?trial=true'} 
               class="plan-cta" 
               class:primary={plan.highlighted}>
              {plan.cta}
            </a>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Comparison Table -->
  <section class="comparison-section">
    <div class="container">
      <h2>Compare Features</h2>
      <div class="comparison-table-wrapper">
        <table class="comparison-table">
          <thead>
            <tr>
              <th>Feature</th>
              <th>Starter</th>
              <th>Professional</th>
              <th>Enterprise</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Users</td>
              <td>5</td>
              <td>25</td>
              <td>Unlimited</td>
            </tr>
            <tr>
              <td>Document Analyses</td>
              <td>1,000/mo</td>
              <td>10,000/mo</td>
              <td>Unlimited</td>
            </tr>
            <tr>
              <td>Threat Profiles</td>
              <td>100/mo</td>
              <td>1,000/mo</td>
              <td>Unlimited</td>
            </tr>
            <tr>
              <td>AI Agents</td>
              <td>Basic</td>
              <td>All + Custom</td>
              <td>All + Custom</td>
            </tr>
            <tr>
              <td>API Access</td>
              <td>—</td>
              <td>✓</td>
              <td>✓</td>
            </tr>
            <tr>
              <td>Custom Integrations</td>
              <td>—</td>
              <td>✓</td>
              <td>✓</td>
            </tr>
            <tr>
              <td>On-Premise Deployment</td>
              <td>✓</td>
              <td>✓</td>
              <td>✓</td>
            </tr>
            <tr>
              <td>Custom Model Training</td>
              <td>—</td>
              <td>—</td>
              <td>✓</td>
            </tr>
            <tr>
              <td>Dedicated Success Manager</td>
              <td>—</td>
              <td>—</td>
              <td>✓</td>
            </tr>
            <tr>
              <td>Support</td>
              <td>Email</td>
              <td>Priority</td>
              <td>24/7 Phone</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <!-- FAQs -->
  <section class="faq-section">
    <div class="container">
      <h2>Frequently Asked Questions</h2>
      <div class="faq-grid">
        {#each faqs as faq}
          <div class="faq-item">
            <h4>{faq.q}</h4>
            <p>{faq.a}</p>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- CTA -->
  <section class="cta-section">
    <div class="container">
      <div class="cta-card">
        <h2>Not Sure Which Plan is Right?</h2>
        <p>Our team can help you find the perfect fit for your organization.</p>
        <a href="/contact" class="btn-primary">Talk to Sales</a>
      </div>
    </div>
  </section>
</div>

<style>
  .pricing-page {
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
    max-width: 600px;
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
    margin-bottom: 2rem;
  }

  .billing-toggle {
    display: inline-flex;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 100px;
    padding: 4px;
  }

  .billing-toggle button {
    padding: 0.75rem 1.5rem;
    border: none;
    background: none;
    color: rgba(255, 255, 255, 0.7);
    font-weight: 500;
    cursor: pointer;
    border-radius: 100px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .billing-toggle button.active {
    background: white;
    color: #1e3a5f;
  }

  .save-badge {
    font-size: 0.75rem;
    background: #22c55e;
    color: white;
    padding: 0.15rem 0.5rem;
    border-radius: 100px;
  }

  .billing-toggle button.active .save-badge {
    background: #059669;
  }

  /* Plans */
  .plans-section {
    padding: 4rem 0;
    margin-top: -2rem;
  }

  .plans-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }

  .plan-card {
    background: white;
    border-radius: 20px;
    padding: 2rem;
    border: 2px solid #e5e7eb;
    position: relative;
    transition: all 0.3s;
  }

  .plan-card:hover {
    border-color: #3b82f6;
    box-shadow: 0 12px 40px rgba(59, 130, 246, 0.1);
  }

  .plan-card.highlighted {
    border-color: #3b82f6;
    box-shadow: 0 12px 40px rgba(59, 130, 246, 0.15);
    transform: scale(1.02);
  }

  .plan-badge {
    position: absolute;
    top: -12px;
    left: 50%;
    transform: translateX(-50%);
    background: #3b82f6;
    color: white;
    padding: 0.35rem 1rem;
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .plan-card h3 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #111827;
    margin-bottom: 0.5rem;
  }

  .plan-description {
    color: #6b7280;
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
  }

  .plan-price {
    margin-bottom: 0.5rem;
  }

  .price {
    font-size: 3rem;
    font-weight: 700;
    color: #111827;
  }

  .period {
    color: #6b7280;
    font-size: 1rem;
  }

  .annual-note {
    font-size: 0.85rem;
    color: #6b7280;
    margin-bottom: 1.5rem;
  }

  .features-list {
    list-style: none;
    padding: 0;
    margin: 0 0 1.5rem;
  }

  .features-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.5rem 0;
    font-size: 0.95rem;
    color: #374151;
  }

  .check {
    color: #059669;
    font-weight: 700;
    flex-shrink: 0;
  }

  .plan-cta {
    display: block;
    width: 100%;
    padding: 0.9rem;
    text-align: center;
    text-decoration: none;
    font-weight: 600;
    border-radius: 10px;
    border: 2px solid #e5e7eb;
    color: #374151;
    transition: all 0.2s;
  }

  .plan-cta:hover {
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .plan-cta.primary {
    background: #3b82f6;
    border-color: #3b82f6;
    color: white;
  }

  .plan-cta.primary:hover {
    background: #2563eb;
    border-color: #2563eb;
  }

  /* Comparison */
  .comparison-section {
    padding: 4rem 0;
    background: white;
  }

  .comparison-section h2 {
    font-size: 1.75rem;
    text-align: center;
    margin-bottom: 2rem;
    color: #111827;
  }

  .comparison-table-wrapper {
    overflow-x: auto;
  }

  .comparison-table {
    width: 100%;
    border-collapse: collapse;
  }

  .comparison-table th,
  .comparison-table td {
    padding: 1rem;
    text-align: center;
    border-bottom: 1px solid #e5e7eb;
  }

  .comparison-table th {
    background: #f9fafb;
    font-weight: 600;
    color: #111827;
  }

  .comparison-table th:first-child,
  .comparison-table td:first-child {
    text-align: left;
    font-weight: 500;
  }

  .comparison-table td {
    color: #4b5563;
  }

  /* FAQ */
  .faq-section {
    padding: 4rem 0;
  }

  .faq-section h2 {
    font-size: 1.75rem;
    text-align: center;
    margin-bottom: 2rem;
    color: #111827;
  }

  .faq-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
  }

  .faq-item {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
  }

  .faq-item h4 {
    font-size: 1rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.5rem;
  }

  .faq-item p {
    font-size: 0.95rem;
    color: #6b7280;
    line-height: 1.6;
  }

  /* CTA */
  .cta-section {
    padding: 4rem 0;
  }

  .cta-card {
    background: #111827;
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
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 1.5rem;
  }

  .btn-primary {
    display: inline-block;
    padding: 0.9rem 2rem;
    background: #3b82f6;
    color: white;
    text-decoration: none;
    font-weight: 600;
    border-radius: 10px;
  }

  @media (max-width: 900px) {
    .plans-grid {
      grid-template-columns: 1fr;
    }

    .plan-card.highlighted {
      transform: none;
    }

    .faq-grid {
      grid-template-columns: 1fr;
    }

    .page-header h1 {
      font-size: 2rem;
    }
  }
</style>
