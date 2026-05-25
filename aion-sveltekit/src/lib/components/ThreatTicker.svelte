<script lang="ts">
	import { tickerVisible } from '$lib/stores/state';
	import { tickerItems } from '$lib/data/content';

	const doubled = [...tickerItems, ...tickerItems];
</script>

<div class="threat-ticker" class:visible={$tickerVisible}>
	<div class="ticker-label">LIVE INTEL</div>
	<div class="ticker-track">
		<div class="ticker-content">
			{#each doubled as item, i (i)}
				<span class="ticker-item">
					{item.icon}
					{item.text}
					{#if item.critical}
						<span class="tk-crit">{item.action}</span>
					{:else}
						<strong>{item.action}</strong>
					{/if}
					— {item.source} — {item.time}
				</span>
			{/each}
		</div>
	</div>
</div>
