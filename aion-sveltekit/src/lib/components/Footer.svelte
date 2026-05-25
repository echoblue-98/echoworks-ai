<script lang="ts">
  const currentYear = new Date().getFullYear();

  const productLinks = [
    { href: '/products#document-intelligence', label: 'Document Intelligence' },
    { href: '/products#threat-profile', label: 'Threat Profile' },
    { href: '/products#ai-agents', label: 'Custom AI Agents' },
    { href: '/products#analytics', label: 'AI Analytics' },
  ];

  const companyLinks = [
    { href: '/about', label: 'About Us' },
    { href: '/contact', label: 'Contact' },
    { href: '/careers', label: 'Careers' },
    { href: '/blog', label: 'Blog' },
  ];

  const resourceLinks = [
    { href: '/demos', label: 'Live Demos' },
    { href: '/docs', label: 'Documentation' },
    { href: '/case-studies', label: 'Case Studies' },
    { href: '/pricing', label: 'Pricing' },
  ];

  const legalLinks = [
    { href: '/privacy', label: 'Privacy Policy' },
    { href: '/terms', label: 'Terms of Service' },
    { href: '/security', label: 'Security' },
  ];
</script>

<footer class="footer">
  <div class="footer-container">
    <div class="footer-main">
      <div class="footer-brand">
        <a href="/" class="footer-logo">
          <span class="logo-icon">◈</span>
          <span class="logo-text">EchoWorks<span class="logo-ai">AI</span></span>
        </a>
        <p class="brand-tagline">
          Enterprise AI solutions for legal, risk, and compliance teams. 
          Secure. On-premise. No data leakage.
        </p>
        <div class="social-links">
          <a href="https://linkedin.com/company/echoworks" aria-label="LinkedIn" class="social-link">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
            </svg>
          </a>
          <a href="https://twitter.com/echoworksai" aria-label="Twitter" class="social-link">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
          </a>
          <a href="https://github.com/echoworks" aria-label="GitHub" class="social-link">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
          </a>
        </div>
      </div>

      <div class="footer-links">
        <div class="link-group">
          <h4>Products</h4>
          {#each productLinks as link}
            <a href={link.href}>{link.label}</a>
          {/each}
        </div>

        <div class="link-group">
          <h4>Company</h4>
          {#each companyLinks as link}
            <a href={link.href}>{link.label}</a>
          {/each}
        </div>

        <div class="link-group">
          <h4>Resources</h4>
          {#each resourceLinks as link}
            <a href={link.href}>{link.label}</a>
          {/each}
        </div>

        <div class="link-group">
          <h4>Legal</h4>
          {#each legalLinks as link}
            <a href={link.href}>{link.label}</a>
          {/each}
        </div>
      </div>
    </div>

    <div class="footer-bottom">
      <p>&copy; {currentYear} EchoWorks AI LLC (EchoBlue Holdings LLC). All rights reserved.</p>
      <p class="footer-badge">Powered by AION OS</p>
    </div>
  </div>
</footer>

<style>
  .footer {
    background: #0f172a;
    color: white;
    padding: 4rem 0 2rem;
  }

  .footer-container {
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 1.5rem;
  }

  .footer-main {
    display: grid;
    grid-template-columns: 1.5fr 2fr;
    gap: 4rem;
    padding-bottom: 3rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .footer-brand {
    max-width: 320px;
  }

  .footer-logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
    font-weight: 700;
    font-size: 1.5rem;
    margin-bottom: 1rem;
  }

  .logo-icon {
    color: #3b82f6;
    font-size: 1.75rem;
  }

  .logo-text {
    color: white;
  }

  .logo-ai {
    color: #3b82f6;
  }

  .brand-tagline {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 1.5rem;
  }

  .social-links {
    display: flex;
    gap: 1rem;
  }

  .social-link {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.7);
    transition: all 0.2s;
  }

  .social-link:hover {
    background: #3b82f6;
    color: white;
  }

  .footer-links {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 2rem;
  }

  .link-group h4 {
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: white;
  }

  .link-group a {
    display: block;
    color: rgba(255, 255, 255, 0.6);
    text-decoration: none;
    font-size: 0.9rem;
    padding: 0.35rem 0;
    transition: color 0.2s;
  }

  .link-group a:hover {
    color: white;
  }

  .footer-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 2rem;
    font-size: 0.85rem;
    color: rgba(255, 255, 255, 0.5);
  }

  .footer-badge {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
    padding: 0.35rem 0.75rem;
    border-radius: 4px;
    font-weight: 500;
  }

  @media (max-width: 900px) {
    .footer-main {
      grid-template-columns: 1fr;
      gap: 2.5rem;
    }

    .footer-brand {
      max-width: none;
    }

    .footer-links {
      grid-template-columns: repeat(2, 1fr);
    }

    .footer-bottom {
      flex-direction: column;
      gap: 1rem;
      text-align: center;
    }
  }

  @media (max-width: 500px) {
    .footer-links {
      grid-template-columns: 1fr;
    }
  }
</style>
