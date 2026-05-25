export interface ComparisonRow {
	feature: string;
	aion: { text: string; status: 'win' | 'lose' | 'partial' };
	crowdstrike: { text: string; status: 'win' | 'lose' | 'partial' };
	sentinel: { text: string; status: 'win' | 'lose' | 'partial' };
	siem: { text: string; status: 'win' | 'lose' | 'partial' };
}

export const comparisonData: ComparisonRow[] = [
	{
		feature: 'Data stays on-premise',
		aion: { text: '100% local', status: 'win' },
		crowdstrike: { text: 'Cloud-only', status: 'lose' },
		sentinel: { text: 'Azure cloud', status: 'lose' },
		siem: { text: 'Depends', status: 'partial' }
	},
	{
		feature: 'Attorney-privilege aware',
		aion: { text: 'Built-in', status: 'win' },
		crowdstrike: { text: 'No', status: 'lose' },
		sentinel: { text: 'No', status: 'lose' },
		siem: { text: 'No', status: 'lose' }
	},
	{
		feature: 'Departing attorney detection',
		aion: { text: 'Multi-stage', status: 'win' },
		crowdstrike: { text: 'Basic UBA', status: 'partial' },
		sentinel: { text: 'Manual rules', status: 'partial' },
		siem: { text: 'No', status: 'lose' }
	},
	{
		feature: 'Ethics wall monitoring',
		aion: { text: 'Native', status: 'win' },
		crowdstrike: { text: 'No', status: 'lose' },
		sentinel: { text: 'No', status: 'lose' },
		siem: { text: 'No', status: 'lose' }
	},
	{
		feature: 'Trust account fraud',
		aion: { text: 'Native', status: 'win' },
		crowdstrike: { text: 'No', status: 'lose' },
		sentinel: { text: 'No', status: 'lose' },
		siem: { text: 'No', status: 'lose' }
	},
	{
		feature: 'AI forensic reports',
		aion: { text: 'Sovereign LLM', status: 'win' },
		crowdstrike: { text: 'Charlotte AI', status: 'partial' },
		sentinel: { text: 'Copilot', status: 'partial' },
		siem: { text: 'No', status: 'lose' }
	},
	{
		feature: 'Deployment time',
		aion: { text: '< 1 hour', status: 'win' },
		crowdstrike: { text: 'Weeks', status: 'lose' },
		sentinel: { text: 'Weeks', status: 'lose' },
		siem: { text: 'Months', status: 'lose' }
	},
	{
		feature: 'Annual cost (50-seat firm)',
		aion: { text: '~$15K', status: 'win' },
		crowdstrike: { text: '$75-150K', status: 'lose' },
		sentinel: { text: '$50-100K', status: 'lose' },
		siem: { text: '$80-200K', status: 'lose' }
	},
	{
		feature: 'Law firm threat library',
		aion: { text: '66 patterns', status: 'win' },
		crowdstrike: { text: 'Generic', status: 'partial' },
		sentinel: { text: 'Generic', status: 'partial' },
		siem: { text: 'DIY', status: 'lose' }
	}
];
