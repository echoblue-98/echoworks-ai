export interface DetectionCategory {
	icon: string;
	title: string;
	rate: string;
	scenarios: string;
	animationDelay: number;
}

export const detectionCategories: DetectionCategory[] = [
	{
		icon: '🔐',
		title: 'VPN Attacks',
		rate: '54/54',
		scenarios: '12 scenarios • Session hijack, credential stuffing, MFA fatigue',
		animationDelay: 0
	},
	{
		icon: '👤',
		title: 'Insider Threats',
		rate: '54/54',
		scenarios: '3 scenarios • Departing attorney, after-hours theft, privilege abuse',
		animationDelay: 0.1
	},
	{
		icon: '☁️',
		title: 'Cloud/SaaS',
		rate: '54/54',
		scenarios: '4 scenarios • SharePoint exfil, API key abuse, rogue OAuth apps',
		animationDelay: 0.2
	},
	{
		icon: '📧',
		title: 'Business Email Compromise',
		rate: '54/54',
		scenarios: '4 scenarios • CEO fraud, wire transfer, vendor impersonation',
		animationDelay: 0.3
	},
	{
		icon: '⚖️',
		title: 'Compliance',
		rate: '54/54',
		scenarios: '4 scenarios • Ethics wall breach, privilege theft, trust account fraud',
		animationDelay: 0.4
	},
	{
		icon: '🤖',
		title: 'AI Security',
		rate: '54/54',
		scenarios: '3 scenarios • Model theft, prompt injection, Copilot abuse',
		animationDelay: 0.5
	},
	{
		icon: '🔗',
		title: 'Supply Chain',
		rate: '54/54',
		scenarios: '2 scenarios • Vendor compromise, package backdoor',
		animationDelay: 0.6
	},
	{
		icon: '💰',
		title: 'Financial Fraud',
		rate: '54/54',
		scenarios: '2 scenarios • Billing fraud, payment hijack',
		animationDelay: 0.7
	}
];
