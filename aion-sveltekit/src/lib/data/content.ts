export interface HardwareTier {
	icon: string;
	name: string;
	vram: string;
	model: string;
	quality: string;
	speed: string;
	price: string;
	badge?: string;
	colorVar: string;
}

export const hardwareTiers: HardwareTier[] = [
	{
		icon: '💻',
		name: 'CPU Only',
		vram: '7.6 GB RAM',
		model: 'Qwen 1.5B',
		quality: 'Structured reports',
		speed: '~25s',
		price: '$0',
		badge: 'Current',
		colorVar: 'success'
	},
	{
		icon: '🎮',
		name: 'RTX 3060',
		vram: '12 GB VRAM',
		model: 'Qwen 7B',
		quality: 'Real forensic reasoning',
		speed: '~3-5s',
		price: '~$250',
		colorVar: 'warning'
	},
	{
		icon: '⚡',
		name: 'RTX 4060 Ti',
		vram: '16 GB VRAM',
		model: 'Qwen 14B',
		quality: 'Near-GPT-4 quality',
		speed: '~3-6s',
		price: '~$400',
		badge: 'Sweet Spot',
		colorVar: 'warning'
	},
	{
		icon: '🔥',
		name: 'RTX 4090',
		vram: '24 GB VRAM',
		model: 'Llama 70B 4-bit',
		quality: 'CrowdStrike-tier',
		speed: '~8-12s',
		price: '~$1,600',
		colorVar: 'primary'
	},
	{
		icon: '🏢',
		name: 'A6000 / Dual',
		vram: '48 GB VRAM',
		model: 'Mixtral 8x7B',
		quality: 'Enterprise SOC grade',
		speed: '~4-6s',
		price: '~$3K+',
		colorVar: 'primary'
	}
];

export interface RoadmapPhase {
	icon: string;
	period: string;
	title: string;
	details: string[];
	colorVar: string;
	status: 'done' | 'in-progress' | 'planned';
}

export const roadmapPhases: RoadmapPhase[] = [
	{
		icon: '✓',
		period: 'NOW',
		title: 'Sovereign Core',
		details: ['66 patterns', 'Local LLM', '15K events/sec', 'Zero data leakage'],
		colorVar: 'success',
		status: 'done'
	},
	{
		icon: '⟳',
		period: 'Q2 2026',
		title: 'SIEM Integration',
		details: ['Splunk/Sentinel', 'connector', 'Auto-ingest logs', '7B model upgrade'],
		colorVar: 'warning',
		status: 'in-progress'
	},
	{
		icon: '⬡',
		period: 'Q3 2026',
		title: 'Federated Network',
		details: ['Cross-firm intel', 'Anonymous patterns', 'Threat feed API', 'Multi-tenant'],
		colorVar: 'primary',
		status: 'planned'
	},
	{
		icon: '◉',
		period: 'Q4 2026',
		title: 'Am Law 200 Scale',
		details: ['SOC 2 certified', 'Managed service', '500+ patterns', '24/7 SOC option'],
		colorVar: 'primary',
		status: 'planned'
	}
];

export interface TickerItem {
	icon: string;
	text: string;
	action: string;
	source: string;
	time: string;
	critical?: boolean;
}

export const tickerItems: TickerItem[] = [
	{ icon: '⚡', text: 'Departing attorney exfil', action: 'BLOCKED', source: 'Anonymous Am Law 100', time: '2m ago' },
	{ icon: '🔒', text: 'Ethics wall breach', action: 'PREVENTED', source: 'Anonymous firm', time: '8m ago' },
	{ icon: '📧', text: 'BEC wire fraud', action: '$1.2M INTERCEPTED', source: 'Anonymous firm', time: '15m ago', critical: true },
	{ icon: '🔓', text: 'MFA fatigue attack', action: 'NEUTRALIZED', source: 'Anonymous firm', time: '23m ago' },
	{ icon: '💼', text: 'After-hours data access', action: 'FLAGGED', source: 'Anonymous firm', time: '31m ago' },
	{ icon: '⚖️', text: 'Privilege data exposure', action: 'CONTAINED', source: 'Anonymous Am Law 200', time: '47m ago' },
	{ icon: '🤖', text: 'AI model exfil attempt', action: 'BLOCKED', source: 'Anonymous firm', time: '1h ago' }
];

export interface AttackButton {
	id: string;
	icon: string;
	label: string;
	title: string;
}

export const attackButtons: AttackButton[] = [
	{ id: 'departing_attorney', icon: '👤', label: 'Departing Attorney', title: 'Simulate departing attorney data theft' },
	{ id: 'bec_fraud', icon: '📧', label: 'BEC Fraud', title: 'Simulate Business Email Compromise' },
	{ id: 'vpn_hijack', icon: '🔐', label: 'VPN Hijack', title: 'Simulate VPN session hijack' },
	{ id: 'insider_theft', icon: '💼', label: 'Insider Theft', title: 'Simulate physical + cyber attack' },
	{ id: 'mfa_fatigue', icon: '🔓', label: 'MFA Fatigue', title: 'Simulate MFA fatigue attack' }
];

export const fallbackScenarios: Record<string, Array<{ prefix: string; text: string; type: string }>> = {
	departing_attorney: [
		{ prefix: '14:32:01', text: 'vpn_access ← partner_alpha', type: 'event' },
		{ prefix: '14:32:15', text: 'file_access_bulk ← partner_alpha', type: 'event' },
		{ prefix: '█ ALERT', text: 'pre_departure_exfil [CRITICAL]', type: 'alert' }
	],
	bec_fraud: [
		{ prefix: '14:40:11', text: 'email_from_external ← finance_lead', type: 'event' },
		{ prefix: '14:40:22', text: 'wire_transfer_initiated ← finance_lead', type: 'event' },
		{ prefix: '█ ALERT', text: 'bec_wire_fraud [CRITICAL]', type: 'alert' }
	],
	vpn_hijack: [
		{ prefix: '14:35:01', text: 'vpn_login ← user_alpha', type: 'event' },
		{ prefix: '14:35:15', text: 'vpn_session_anomaly ← user_alpha', type: 'event' },
		{ prefix: '█ ALERT', text: 'vpn_session_takeover [CRITICAL]', type: 'alert' }
	],
	insider_theft: [
		{ prefix: '03:00:01', text: 'badge_access ← contractor_x', type: 'event' },
		{ prefix: '03:00:15', text: 'usb_mount ← contractor_x', type: 'event' },
		{ prefix: '█ ALERT', text: 'physical_cyber_exfil [CRITICAL]', type: 'alert' }
	],
	mfa_fatigue: [
		{ prefix: '02:00:01', text: 'mfa_push_sent ← victim_user', type: 'event' },
		{ prefix: '02:00:05', text: 'mfa_push_sent ← victim_user', type: 'event' },
		{ prefix: '02:00:08', text: 'mfa_approved ← victim_user', type: 'event' },
		{ prefix: '█ ALERT', text: 'mfa_fatigue_attack [CRITICAL]', type: 'alert' }
	]
};
