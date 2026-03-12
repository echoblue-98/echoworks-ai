<script lang="ts">
  import { page } from '$app/stores';
  import { bookings } from '$lib/api';

  let formType: 'demo' | 'contact' = $page.url.searchParams.get('trial') ? 'demo' : 'contact';

  // Form state
  let name = $state('');
  let email = $state('');
  let company = $state('');
  let jobTitle = $state('');
  let companySize = $state('');
  let message = $state('');
  let preferredDate = $state('');
  let preferredTime = $state('');
  let products = $state<string[]>([]);
  
  let submitting = $state(false);
  let submitted = $state(false);
  let error = $state('');

  const productOptions = [
    { value: 'document-intelligence', label: 'Document Intelligence' },
    { value: 'threat-profile', label: 'Threat Profiling' },
    { value: 'ai-agents', label: 'Custom AI Agents' },
    { value: 'ai-analytics', label: 'AI Analytics' },
    { value: 'all', label: 'Full Platform' },
  ];

  const companySizes = [
    '1-10',
    '11-50',
    '51-200',
    '201-1000',
    '1000+',
  ];

  async function handleSubmit() {
    if (!name || !email || !company) {
      error = 'Please fill in all required fields';
      return;
    }

    submitting = true;
    error = '';

    try {
      if (formType === 'demo') {
        await bookings.requestDemo({
          name,
          email,
          company,
          job_title: jobTitle,
          company_size: companySize,
          products_interested: products,
          preferred_date: preferredDate,
          preferred_time: preferredTime,
          message,
        });
      } else {
        await bookings.submitContact({
          name,
          email,
          company,
          message,
        });
      }
      submitted = true;
    } catch (e) {
      error = 'Submission failed. Please try again or email us directly.';
    } finally {
      submitting = false;
    }
  }

  function toggleProduct(value: string) {
    if (products.includes(value)) {
      products = products.filter(p => p !== value);
    } else {
      products = [...products, value];
    }
  }
</script>

<svelte:head>
  <title>{formType === 'demo' ? 'Book a Demo' : 'Contact Us'} | EchoWorks AI</title>
</svelte:head>

<div class="contact-page">
  <section class="page-header">
    <div class="header-content">
      <span class="page-badge">{formType === 'demo' ? 'Book a Demo' : 'Contact'}</span>
      <h1>{formType === 'demo' ? 'See EchoWorks AI in Action' : "Let's Talk"}</h1>
      <p>
        {formType === 'demo' 
          ? 'Schedule a personalized walkthrough with our team.' 
          : 'Have questions? We\'re here to help.'}
      </p>
    </div>

    <div class="form-toggle">
      <button class:active={formType === 'demo'} onclick={() => formType = 'demo'}>
        Book Demo
      </button>
      <button class:active={formType === 'contact'} onclick={() => formType = 'contact'}>
        General Inquiry
      </button>
    </div>
  </section>

  <section class="form-section">
    <div class="container">
      <div class="form-grid">
        <div class="form-container">
          {#if submitted}
            <div class="success-message">
              <div class="success-icon">✓</div>
              <h2>Thank You!</h2>
              <p>
                {formType === 'demo' 
                  ? 'We\'ve received your demo request. Our team will contact you within 24 hours to schedule your session.'
                  : 'We\'ve received your message and will get back to you shortly.'}
              </p>
              <a href="/demos" class="btn-secondary">Try Live Demos While You Wait</a>
            </div>
          {:else}
            <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
              <div class="form-row">
                <div class="form-group">
                  <label for="name">Full Name *</label>
                  <input type="text" id="name" bind:value={name} required />
                </div>
                <div class="form-group">
                  <label for="email">Work Email *</label>
                  <input type="email" id="email" bind:value={email} required />
                </div>
              </div>

              <div class="form-row">
                <div class="form-group">
                  <label for="company">Company *</label>
                  <input type="text" id="company" bind:value={company} required />
                </div>
                {#if formType === 'demo'}
                  <div class="form-group">
                    <label for="jobTitle">Job Title</label>
                    <input type="text" id="jobTitle" bind:value={jobTitle} />
                  </div>
                {/if}
              </div>

              {#if formType === 'demo'}
                <div class="form-group">
                  <label for="companySize">Company Size</label>
                  <select id="companySize" bind:value={companySize}>
                    <option value="">Select...</option>
                    {#each companySizes as size}
                      <option value={size}>{size} employees</option>
                    {/each}
                  </select>
                </div>

                <div class="form-group">
                  <label>Products of Interest</label>
                  <div class="product-options">
                    {#each productOptions as product}
                      <button
                        type="button"
                        class="product-btn"
                        class:active={products.includes(product.value)}
                        onclick={() => toggleProduct(product.value)}
                      >
                        {product.label}
                      </button>
                    {/each}
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label for="preferredDate">Preferred Date</label>
                    <input type="date" id="preferredDate" bind:value={preferredDate} />
                  </div>
                  <div class="form-group">
                    <label for="preferredTime">Preferred Time</label>
                    <select id="preferredTime" bind:value={preferredTime}>
                      <option value="">Select...</option>
                      <option value="morning">Morning (9am - 12pm)</option>
                      <option value="afternoon">Afternoon (12pm - 5pm)</option>
                      <option value="evening">Evening (5pm - 8pm)</option>
                    </select>
                  </div>
                </div>
              {/if}

              <div class="form-group">
                <label for="message">{formType === 'demo' ? 'Anything specific you\'d like to see?' : 'Message'}</label>
                <textarea id="message" bind:value={message} rows="4"></textarea>
              </div>

              {#if error}
                <div class="error-message">{error}</div>
              {/if}

              <button type="submit" class="submit-btn" disabled={submitting}>
                {submitting ? 'Submitting...' : formType === 'demo' ? 'Request Demo' : 'Send Message'}
              </button>
            </form>
          {/if}
        </div>

        <div class="contact-info">
          <div class="info-card">
            <h3>Quick Response</h3>
            <p>Our team typically responds within 2-4 hours during business hours.</p>
          </div>

          <div class="info-card">
            <h3>Email Us</h3>
            <a href="mailto:hello@echoworks.ai">hello@echoworks.ai</a>
          </div>

          <div class="info-card">
            <h3>Call Us</h3>
            <a href="tel:+1-555-0123">+1 (555) 012-3456</a>
          </div>

          <div class="info-card highlight">
            <h3>Try It Now</h3>
            <p>Skip the wait — test our AI products live with no signup required.</p>
            <a href="/demos" class="demo-link">Launch Live Demos →</a>
          </div>
        </div>
      </div>
    </div>
  </section>
</div>

<style>
  .contact-page {
    background: #f9fafb;
    min-height: 100vh;
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
    max-width: 600px;
    margin: 0 auto 2rem;
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
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
  }

  .page-header p {
    font-size: 1.1rem;
    color: rgba(255, 255, 255, 0.8);
  }

  .form-toggle {
    display: inline-flex;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 100px;
    padding: 4px;
  }

  .form-toggle button {
    padding: 0.75rem 1.5rem;
    border: none;
    background: none;
    color: rgba(255, 255, 255, 0.7);
    font-weight: 500;
    cursor: pointer;
    border-radius: 100px;
    transition: all 0.2s;
  }

  .form-toggle button.active {
    background: white;
    color: #1e3a5f;
  }

  /* Form Section */
  .form-section {
    padding: 4rem 0;
    margin-top: -2rem;
  }

  .form-grid {
    display: grid;
    grid-template-columns: 1.5fr 1fr;
    gap: 3rem;
  }

  .form-container {
    background: white;
    padding: 2.5rem;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
  }

  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .form-group {
    margin-bottom: 1.25rem;
  }

  .form-group label {
    display: block;
    font-size: 0.9rem;
    font-weight: 500;
    color: #374151;
    margin-bottom: 0.5rem;
  }

  .form-group input,
  .form-group select,
  .form-group textarea {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    font-size: 1rem;
    font-family: inherit;
    transition: border-color 0.2s;
  }

  .form-group input:focus,
  .form-group select:focus,
  .form-group textarea:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .product-options {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .product-btn {
    padding: 0.5rem 1rem;
    border: 2px solid #e5e7eb;
    border-radius: 100px;
    background: white;
    color: #6b7280;
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .product-btn:hover {
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .product-btn.active {
    border-color: #3b82f6;
    background: #3b82f6;
    color: white;
  }

  .submit-btn {
    width: 100%;
    padding: 1rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 10px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  .submit-btn:hover {
    background: #2563eb;
  }

  .submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .error-message {
    color: #dc2626;
    background: #fef2f2;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    font-size: 0.9rem;
  }

  .success-message {
    text-align: center;
    padding: 2rem;
  }

  .success-icon {
    width: 64px;
    height: 64px;
    background: #22c55e;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    margin: 0 auto 1.5rem;
  }

  .success-message h2 {
    font-size: 1.5rem;
    margin-bottom: 0.75rem;
    color: #111827;
  }

  .success-message p {
    color: #6b7280;
    margin-bottom: 1.5rem;
  }

  .btn-secondary {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    border: 2px solid #3b82f6;
    color: #3b82f6;
    text-decoration: none;
    font-weight: 600;
    border-radius: 8px;
  }

  /* Contact Info */
  .contact-info {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .info-card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #e5e7eb;
  }

  .info-card h3 {
    font-size: 1rem;
    font-weight: 600;
    color: #111827;
    margin-bottom: 0.5rem;
  }

  .info-card p {
    font-size: 0.95rem;
    color: #6b7280;
    margin-bottom: 0.5rem;
  }

  .info-card a {
    color: #3b82f6;
    text-decoration: none;
    font-weight: 500;
  }

  .info-card.highlight {
    background: linear-gradient(135deg, #eff6ff, #f0fdf4);
    border-color: #bfdbfe;
  }

  .demo-link {
    display: inline-block;
    margin-top: 0.5rem;
    font-weight: 600;
  }

  @media (max-width: 900px) {
    .form-grid {
      grid-template-columns: 1fr;
    }

    .form-row {
      grid-template-columns: 1fr;
    }

    .page-header h1 {
      font-size: 2rem;
    }
  }
</style>
