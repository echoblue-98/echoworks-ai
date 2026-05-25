<script lang="ts">
	import { onMount } from 'svelte';
	import { bootComplete, tickerVisible } from '$lib/stores/state';

	let bootLines: Array<{ label: string; result: string }> = [];
	let progressPct = 0;
	let statusText = '';
	let statusOnline = false;
	let visible = true;
	let fadingOut = false;
	let skipped = false;

	const steps = [
		{ label: 'Loading pattern database', result: '66 PATTERNS', pct: 12 },
		{ label: 'Initializing threat categories', result: '15 CATEGORIES ACTIVE', pct: 28 },
		{ label: 'Connecting sovereign LLM', result: 'QWEN 1.5B — LOCAL INFERENCE', pct: 48 },
		{ label: 'Calibrating detection engine', result: '0.07ms LATENCY', pct: 64 },
		{ label: 'Verifying data sovereignty', result: 'ZERO EXTERNAL EGRESS', pct: 80 },
		{ label: 'Running system diagnostics', result: 'BENCHMARK 96/100', pct: 100 }
	];

	function sleep(ms: number) {
		return new Promise((r) => setTimeout(r, ms));
	}

	function skip() {
		skipped = true;
	}

	async function run() {
		await sleep(400);

		for (const step of steps) {
			if (skipped) break;
			bootLines = [...bootLines, { label: step.label, result: '' }];
			progressPct = step.pct;
			await sleep(skipped ? 0 : 300 + Math.random() * 200);
			bootLines = bootLines.map((l, i) =>
				i === bootLines.length - 1 ? { ...l, result: step.result } : l
			);
		}

		if (!skipped) await sleep(350);

		statusText = '████ SYSTEM OPERATIONAL ████';
		statusOnline = true;

		if (!skipped) await sleep(900);

		fadingOut = true;
		tickerVisible.set(true);

		await sleep(skipped ? 300 : 1000);
		visible = false;
		bootComplete.set(true);
	}

	onMount(() => {
		run();
	});
</script>

{#if visible}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="boot-overlay" class:fade-out={fadingOut} on:click={skip}>
		<div class="boot-terminal">
			<div class="boot-logo-text">AION OS</div>
			<div class="boot-version-text">Sovereign Security Intelligence</div>

			<div class="boot-lines">
				{#each bootLines as line, i (i)}
					<div class="boot-line">
						{#if line.result}
							<span class="boot-check">[✓]</span>
							<span class="boot-label">{line.label}</span> →
							<span class="boot-value">{line.result}</span>
						{:else}
							<span class="boot-label">[  ] {line.label}...</span>
							<span class="boot-loading">⟳</span>
						{/if}
					</div>
				{/each}
			</div>

			<div class="boot-progress-bar">
				<div class="boot-progress-fill" style="width: {progressPct}%"></div>
			</div>

			<div class="boot-status" class:online={statusOnline}>
				{statusText}
			</div>
		</div>
		<div class="boot-skip">CLICK TO SKIP</div>
	</div>
{/if}
