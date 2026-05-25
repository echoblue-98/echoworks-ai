<script lang="ts">
  import { catalog, type Product } from '$lib/api';
  import { onMount } from 'svelte';

  let products: Product[] = [];
  let loading = true;
  let error = '';

  onMount(async () => {
    try {
      products = await catalog.getFeatured();
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load products';
    } finally {
      loading = false;
    }
  });

  function getPriceDisplay(product: Product): string {
    if (!product.starting_price.amount) return 'Contact Us';
    const amount = product.starting_price.amount.toLocaleString();
    const cycle = product.starting_price.cycle === 'annual' ? '/yr' : '/mo';
    return `$${amount}${cycle}`;
  }
</script>

<section class="products-grid">
  {#if loading}
    <div class="loading">Loading AI Solutions...</div>
  {:else if error}
    <div class="error">{error}</div>
  {:else}
    {#each products as product}
      <a href="/products/{product.slug}" class="product-card" class:featured={product.is_featured}>
        {#if product.hero_image}
          <img src={product.hero_image} alt={product.name} class="product-image" />
        {/if}
        <div class="product-content">
          <span class="category">{product.category_name}</span>
          <h3>{product.name}</h3>
          <p>{product.tagline}</p>
          <div class="features">
            {#each product.features.slice(0, 3) as feature}
              <span class="feature">✓ {feature}</span>
            {/each}
          </div>
          <div class="product-footer">
            <span class="price">{getPriceDisplay(product)}</span>
            <span class="cta">Learn More →</span>
          </div>
        </div>
      </a>
    {/each}
  {/if}
</section>

<style>
  .products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 2rem;
    padding: 2rem 0;
  }

  .product-card {
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    overflow: hidden;
    text-decoration: none;
    color: inherit;
    transition: transform 0.2s, box-shadow 0.2s;
  }

  .product-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  }

  .product-card.featured {
    border: 2px solid #3b82f6;
  }

  .product-image {
    width: 100%;
    height: 200px;
    object-fit: cover;
  }

  .product-content {
    padding: 1.5rem;
  }

  .category {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    color: #6b7280;
    letter-spacing: 0.05em;
  }

  h3 {
    margin: 0.5rem 0;
    font-size: 1.25rem;
    font-weight: 700;
    color: #111827;
  }

  p {
    color: #6b7280;
    font-size: 0.95rem;
    line-height: 1.5;
    margin-bottom: 1rem;
  }

  .features {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    margin-bottom: 1rem;
  }

  .feature {
    font-size: 0.85rem;
    color: #059669;
  }

  .product-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 1rem;
    border-top: 1px solid #e5e7eb;
  }

  .price {
    font-size: 1.25rem;
    font-weight: 700;
    color: #111827;
  }

  .cta {
    color: #3b82f6;
    font-weight: 600;
  }

  .loading, .error {
    grid-column: 1 / -1;
    text-align: center;
    padding: 3rem;
    color: #6b7280;
  }

  .error {
    color: #dc2626;
  }
</style>
