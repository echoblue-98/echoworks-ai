<script lang="ts">
	import '../../app.css';
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { getHealth } from '$lib/api/client';
	import type { HealthResponse } from '$lib/api/types';

	let { children } = $props();

	let health: HealthResponse | null = $state(null);
	let healthError = $state(false);
	let sidebarCollapsed = $state(false);
	let currentPath = $derived($page.url.pathname);

	const navItems = [
		{ href: '/dashboard', label: 'Overview', icon: '◉' },
		{ href: '/dashboard/soc', label: 'SOC Center', icon: '⚡' },
		{ href: '/dashboard/improvement', label: 'Improvement', icon: '⟳' },
		{ href: '/dashboard/metrics', label: 'Metrics', icon: '▦' },
	];

	onMount(() => {
		pollHealth();
		const interval = setInterval(pollHealth, 15_000);
		return () => clearInterval(interval);
	});

	async function pollHealth() {
		const res = await getHealth();
		if (res.ok) {
			health = res.data;
			healthError = false;
		} else {
			healthError = true;
		}
	}
</script>

<svelte:head>
	<title>AION OS — Operations Dashboard</title>
</svelte:head>

<div class="dash-shell" class:collapsed={sidebarCollapsed}>
	<!-- Sidebar -->
	<aside class="dash-sidebar">
		<div class="sidebar-header">
			<a href="/" class="sidebar-logo">
				<span class="logo-mark">A</span>
				{#if !sidebarCollapsed}
					<span class="logo-text">AION OS</span>
				{/if}
			</a>
			<button class="collapse-btn" onclick={() => sidebarCollapsed = !sidebarCollapsed}>
				{sidebarCollapsed ? '▸' : '◂'}
			</button>
		</div>

		<nav class="sidebar-nav">
			{#each navItems as item}
				<a
					href={item.href}
					class="nav-item"
					class:active={item.href === '/dashboard' ? currentPath === '/dashboard' : currentPath.startsWith(item.href)}
				>
					<span class="nav-icon">{item.icon}</span>
					{#if !sidebarCollapsed}
						<span class="nav-label">{item.label}</span>
					{/if}
				</a>
			{/each}
		</nav>

		<div class="sidebar-footer">
			<div class="health-badge" class:healthy={health?.status === 'operational'} class:error={healthError}>
				<span class="health-dot"></span>
				{#if !sidebarCollapsed}
					<span class="health-text">
						{healthError ? 'API Offline' : health?.status ?? 'Checking…'}
					</span>
				{/if}
			</div>
			{#if !sidebarCollapsed && health}
				<div class="version-text">v{health.version}</div>
			{/if}
		</div>
	</aside>

	<!-- Main content -->
	<main class="dash-main">
		<header class="dash-topbar">
			<div class="topbar-left">
				<h1 class="topbar-title">
					{#if currentPath === '/dashboard'}Overview
					{:else if currentPath.startsWith('/dashboard/soc')}Security Operations
					{:else if currentPath.startsWith('/dashboard/improvement')}Improvement Engine
					{:else if currentPath.startsWith('/dashboard/metrics')}Observability
					{/if}
				</h1>
			</div>
			<div class="topbar-right">
				<a href="/" class="topbar-link">← Pitch Site</a>
				<span class="topbar-time">{new Date().toLocaleDateString()}</span>
			</div>
		</header>
		<div class="dash-content">
			{@render children()}
		</div>
	</main>
</div>

<style>
	/* ── Dashboard Shell ───────────────────────────────── */
	.dash-shell {
		display: flex;
		min-height: 100vh;
		background: var(--bg-dark, #050508);
		color: var(--text, #fff);
	}

	/* ── Sidebar ───────────────────────────────────────── */
	.dash-sidebar {
		width: 240px;
		background: rgba(10, 10, 15, 0.95);
		border-right: 1px solid rgba(255,255,255,0.06);
		display: flex;
		flex-direction: column;
		transition: width 0.2s ease;
		position: fixed;
		top: 0;
		left: 0;
		height: 100vh;
		z-index: 100;
		backdrop-filter: blur(20px);
	}
	.collapsed .dash-sidebar { width: 64px; }

	.sidebar-header {
		padding: 20px 16px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		border-bottom: 1px solid rgba(255,255,255,0.06);
	}

	.sidebar-logo {
		display: flex;
		align-items: center;
		gap: 10px;
		text-decoration: none;
		color: inherit;
	}

	.logo-mark {
		font-family: 'JetBrains Mono', monospace;
		font-size: 1.4rem;
		font-weight: 700;
		background: linear-gradient(135deg, #fff, var(--primary, #ff3b3b));
		-webkit-background-clip: text;
		background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.logo-text {
		font-family: 'JetBrains Mono', monospace;
		font-size: 0.9rem;
		font-weight: 600;
		letter-spacing: -0.5px;
	}

	.collapse-btn {
		background: none;
		border: 1px solid rgba(255,255,255,0.1);
		color: var(--text-dim, rgba(255,255,255,0.7));
		border-radius: 6px;
		padding: 4px 8px;
		cursor: pointer;
		font-size: 0.75rem;
		transition: all 0.2s;
	}
	.collapse-btn:hover { border-color: var(--primary, #ff3b3b); color: #fff; }

	/* ── Navigation ────────────────────────────────────── */
	.sidebar-nav {
		flex: 1;
		padding: 12px 8px;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 10px 12px;
		border-radius: 8px;
		color: var(--text-dim, rgba(255,255,255,0.7));
		text-decoration: none;
		font-size: 0.88rem;
		transition: all 0.15s;
	}
	.nav-item:hover { background: rgba(255,255,255,0.05); color: #fff; }
	.nav-item.active {
		background: rgba(255,59,59,0.12);
		color: var(--primary, #ff3b3b);
		font-weight: 600;
	}

	.nav-icon {
		font-size: 1.1rem;
		width: 24px;
		text-align: center;
		flex-shrink: 0;
	}

	/* ── Sidebar Footer ────────────────────────────────── */
	.sidebar-footer {
		padding: 16px;
		border-top: 1px solid rgba(255,255,255,0.06);
	}

	.health-badge {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 0.78rem;
		color: var(--text-dim);
	}

	.health-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background: var(--warning, #ffaa00);
		flex-shrink: 0;
	}
	.health-badge.healthy .health-dot { background: var(--success, #00ff88); box-shadow: 0 0 8px rgba(0,255,136,0.4); }
	.health-badge.error .health-dot { background: var(--primary, #ff3b3b); box-shadow: 0 0 8px rgba(255,59,59,0.4); }

	.version-text {
		font-size: 0.65rem;
		color: rgba(255,255,255,0.25);
		margin-top: 6px;
		font-family: 'JetBrains Mono', monospace;
	}

	/* ── Main Area ─────────────────────────────────────── */
	.dash-main {
		flex: 1;
		margin-left: 240px;
		display: flex;
		flex-direction: column;
		min-height: 100vh;
		transition: margin-left 0.2s ease;
	}
	.collapsed .dash-main { margin-left: 64px; }

	.dash-topbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16px 32px;
		border-bottom: 1px solid rgba(255,255,255,0.06);
		background: rgba(10,10,15,0.7);
		backdrop-filter: blur(10px);
		position: sticky;
		top: 0;
		z-index: 50;
	}

	.topbar-title {
		font-size: 1.2rem;
		font-weight: 600;
	}

	.topbar-right {
		display: flex;
		align-items: center;
		gap: 20px;
	}

	.topbar-link {
		color: var(--text-dim);
		text-decoration: none;
		font-size: 0.8rem;
		transition: color 0.2s;
	}
	.topbar-link:hover { color: var(--primary); }

	.topbar-time {
		font-size: 0.78rem;
		color: rgba(255,255,255,0.3);
		font-family: 'JetBrains Mono', monospace;
	}

	.dash-content {
		flex: 1;
		padding: 32px;
	}

	/* ── Responsive ────────────────────────────────────── */
	@media (max-width: 768px) {
		.dash-sidebar { width: 64px; }
		.dash-main { margin-left: 64px; }
		.nav-label, .logo-text, .health-text, .version-text { display: none; }
		.dash-content { padding: 16px; }
	}
</style>
