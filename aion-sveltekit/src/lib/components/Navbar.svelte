<script lang="ts">
  import { page } from '$app/stores';

  let mobileMenuOpen = $state(false);

  const navLinks = [
    { href: '/', label: 'Home' },
    { href: '/products', label: 'Products' },
    { href: '/demos', label: 'Try Demos' },
    { href: '/pricing', label: 'Pricing' },
    { href: '/about', label: 'About' },
    { href: '/contact', label: 'Contact' },
  ];

  function isActive(href: string, pathname: string): boolean {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  }
</script>

<nav class="navbar">
  <div class="nav-container">
    <a href="/" class="logo">
      <span class="logo-icon">◈</span>
      <span class="logo-text">EchoWorks<span class="logo-ai">AI</span></span>
    </a>

    <div class="nav-links" class:open={mobileMenuOpen}>
      {#each navLinks as link}
        <a
          href={link.href}
          class="nav-link"
          class:active={isActive(link.href, $page.url.pathname)}
          onclick={() => (mobileMenuOpen = false)}
        >
          {link.label}
        </a>
      {/each}
    </div>

    <div class="nav-actions">
      <a href="/contact" class="btn-demo">Book Demo</a>
      <a href="/portal" class="btn-login">Login</a>
    </div>

    <button class="mobile-toggle" onclick={() => (mobileMenuOpen = !mobileMenuOpen)}>
      {#if mobileMenuOpen}
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6L6 18M6 6l12 12" />
        </svg>
      {:else}
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 12h18M3 6h18M3 18h18" />
        </svg>
      {/if}
    </button>
  </div>
</nav>

<style>
  .navbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 1000;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #e5e7eb;
  }

  .nav-container {
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 1.5rem;
    height: 72px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
    font-weight: 700;
    font-size: 1.5rem;
  }

  .logo-icon {
    color: #3b82f6;
    font-size: 1.75rem;
  }

  .logo-text {
    color: #111827;
  }

  .logo-ai {
    color: #3b82f6;
  }

  .nav-links {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .nav-link {
    padding: 0.5rem 1rem;
    color: #4b5563;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95rem;
    border-radius: 6px;
    transition: all 0.2s;
  }

  .nav-link:hover {
    color: #111827;
    background: #f3f4f6;
  }

  .nav-link.active {
    color: #3b82f6;
    background: #eff6ff;
  }

  .nav-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .btn-demo {
    padding: 0.6rem 1.25rem;
    background: #3b82f6;
    color: white;
    text-decoration: none;
    font-weight: 600;
    font-size: 0.9rem;
    border-radius: 8px;
    transition: background 0.2s;
  }

  .btn-demo:hover {
    background: #2563eb;
  }

  .btn-login {
    padding: 0.6rem 1.25rem;
    color: #4b5563;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.9rem;
  }

  .btn-login:hover {
    color: #111827;
  }

  .mobile-toggle {
    display: none;
    padding: 0.5rem;
    background: none;
    border: none;
    color: #374151;
    cursor: pointer;
  }

  @media (max-width: 900px) {
    .nav-links {
      display: none;
      position: absolute;
      top: 72px;
      left: 0;
      right: 0;
      background: white;
      flex-direction: column;
      padding: 1rem;
      border-bottom: 1px solid #e5e7eb;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }

    .nav-links.open {
      display: flex;
    }

    .nav-link {
      width: 100%;
      padding: 0.75rem 1rem;
    }

    .nav-actions {
      display: none;
    }

    .mobile-toggle {
      display: block;
    }
  }
</style>
