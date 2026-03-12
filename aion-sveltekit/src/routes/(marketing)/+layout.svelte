<script lang="ts">
  import Navbar from '$lib/components/Navbar.svelte';
  import Footer from '$lib/components/Footer.svelte';

  let { children } = $props();
</script>

<svelte:head>
  <title>EchoWorks AI - Enterprise AI Solutions</title>
  <meta name="description" content="Enterprise AI solutions for legal, risk, and compliance teams. Document Intelligence, Threat Profiling, Custom AI Agents." />
</svelte:head>

<div class="marketing-layout">
  <Navbar />
  <main>
    {@render children()}
  </main>
  <Footer />
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #ffffff;
    color: #111827;
    -webkit-font-smoothing: antialiased;
  }

  :global(*) {
    box-sizing: border-box;
  }

  :global(a) {
    color: inherit;
  }

  .marketing-layout {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  main {
    flex: 1;
    padding-top: 72px; /* navbar height */
  }
</style>
