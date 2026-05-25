import { writable, derived } from 'svelte/store';

// ── Types ──────────────────────────────────────────────
export interface TerminalLine {
	id: number;
	prefix: string;
	text: string;
	type: 'event' | 'alert' | 'success' | 'scenario' | 'info' | 'error' | 'divider' | 'analysis';
}

export interface ForensicReport {
	vulnerabilities: Array<{
		title: string;
		severity: string;
		description?: string;
		attack_vector?: string;
		countermeasures?: string[];
	}>;
	risk_score: number;
	immediate_actions: string[];
	latency_ms: number;
	model: string;
}

export interface AionStats {
	detectionRate: string;
	patterns: number;
	categories: number;
	latencyMs: number;
	eventsProcessed: number;
	alertsGenerated: number;
}

// ── Connection State ───────────────────────────────────
export type ConnectionStatus = 'connecting' | 'connected' | 'offline';
export const connectionStatus = writable<ConnectionStatus>('connecting');

// ── Stats ──────────────────────────────────────────────
export const stats = writable<AionStats>({
	detectionRate: '0',
	patterns: 0,
	categories: 0,
	latencyMs: 0,
	eventsProcessed: 0,
	alertsGenerated: 0
});

// ── Terminal Lines ─────────────────────────────────────
let lineCounter = 0;
export const terminalLines = writable<TerminalLine[]>([]);

export function addLine(prefix: string, text: string, type: TerminalLine['type'] = 'event') {
	terminalLines.update((lines) => {
		const next = [...lines, { id: ++lineCounter, prefix, text, type }];
		return next.length > 100 ? next.slice(-100) : next;
	});
}

export function clearTerminal() {
	terminalLines.set([]);
	addLine('SYSTEM', 'Terminal cleared', 'info');
}

// ── Forensic Report ────────────────────────────────────
export const currentReport = writable<ForensicReport | null>(null);
export const reportLoading = writable(false);

// ── Document Analysis ──────────────────────────────────
export interface DocumentClause {
	clause_type: string;
	summary: string;
	risk_level: string;
	risk_reason: string;
	parties_affected: string[];
	recommendations: string[];
}

export interface DocumentAnalysisResult {
	document_id: string;
	title: string;
	document_type: string;
	parties: string[];
	risk_score: number;
	overall_risk: string;
	summary: string;
	red_flags: string[];
	recommendations: string[];
	clauses: DocumentClause[];
	key_obligations: Record<string, string[]>;
	metadata: Record<string, unknown>;
}

export const currentDocAnalysis = writable<DocumentAnalysisResult | null>(null);
export const docAnalysisLoading = writable(false);

// ── Active Attack ──────────────────────────────────────
export const activeAttack = writable<string | null>(null);

// ── Screen Shake Trigger ───────────────────────────────
export const shakeCount = writable(0);
export function triggerShake() {
	shakeCount.update((n) => n + 1);
}

// ── Boot State ─────────────────────────────────────────
export const bootComplete = writable(false);
export const tickerVisible = writable(false);

// ── Voice State ────────────────────────────────────────
export const voiceEnabled = writable(false);

// ── Derived ────────────────────────────────────────────
export const buttonsDisabled = derived(activeAttack, ($a) => $a !== null);
