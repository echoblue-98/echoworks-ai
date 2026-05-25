// ═══════════════════════════════════════════════════════════
// AION OS — REST API Client
// Centralized fetch wrapper for all 22 REST endpoints
// ═══════════════════════════════════════════════════════════

import type {
	ApiResult,
	HealthResponse,
	LegalAnalysisRequest,
	SecurityAnalysisRequest,
	AnalysisResponse,
	StatsResponse,
	SOCStatusResponse,
	SOCAlert,
	SOCIngestResponse,
	UserRiskProfile,
	ImprovementStatus,
	FeedbackRequest,
	DetectionMetrics,
	PolicyProposal,
	PolicyVersion,
	PolicyDiff,
	ProposalAction,
	Nudge,
	MetricsJsonResponse,
	AuditLogsResponse,
} from './types';

// ── Configuration ───────────────────────────────────────
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';
let _apiKey: string | null = null;

export function setApiKey(key: string) {
	_apiKey = key;
}

export function getApiKey(): string | null {
	return _apiKey;
}

// ── Core fetch wrapper ──────────────────────────────────
async function api<T>(
	path: string,
	options: RequestInit = {}
): Promise<ApiResult<T>> {
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...(options.headers as Record<string, string> ?? {}),
	};

	if (_apiKey) {
		headers['X-API-Key'] = _apiKey;
	}

	try {
		const res = await fetch(`${BASE_URL}${path}`, {
			...options,
			headers,
		});

		if (!res.ok) {
			const body = await res.json().catch(() => ({}));
			return {
				ok: false,
				error: {
					status: res.status,
					message: body.detail ?? res.statusText,
					detail: body.detail,
				},
			};
		}

		const data = await res.json();
		return { ok: true, data: data as T };
	} catch (err) {
		return {
			ok: false,
			error: {
				status: 0,
				message: err instanceof Error ? err.message : 'Network error',
			},
		};
	}
}

// ═══════════════════════════════════════════════════════════
// ENDPOINT METHODS
// ═══════════════════════════════════════════════════════════

// ── Health ──────────────────────────────────────────────
export function getHealth() {
	return api<HealthResponse>('/health');
}

export function getRoot() {
	return api<Record<string, unknown>>('/');
}

// ── Analysis ────────────────────────────────────────────
export function analyzeLegal(req: LegalAnalysisRequest) {
	return api<AnalysisResponse>('/api/v1/analyze/legal', {
		method: 'POST',
		body: JSON.stringify(req),
	});
}

export function analyzeSecurity(req: SecurityAnalysisRequest) {
	return api<AnalysisResponse>('/api/v1/analyze/security', {
		method: 'POST',
		body: JSON.stringify(req),
	});
}

// ── Stats ───────────────────────────────────────────────
export function getStats() {
	return api<StatsResponse>('/api/v1/stats');
}

// ── Audit Logs ──────────────────────────────────────────
export function getAuditLogs(params?: {
	user_id?: string;
	event_type?: string;
	limit?: number;
}) {
	const qs = new URLSearchParams();
	if (params?.user_id) qs.set('user_id', params.user_id);
	if (params?.event_type) qs.set('event_type', params.event_type);
	if (params?.limit) qs.set('limit', String(params.limit));
	const q = qs.toString();
	return api<AuditLogsResponse>(`/api/v1/audit/logs${q ? '?' + q : ''}`);
}

// ── Sovereign Inference (local LLM, no frontier-lab egress) ─
export interface ReasonResponse {
	success: boolean;
	provider: string;
	model: string;
	response: string;
	tokens: number;
	latency_ms: number;
	tokens_per_sec: number;
	sovereign: boolean;
	frontier_lab_egress: boolean;
	timestamp: string;
}

export function sovereignReason(prompt: string, maxTokens = 256, temperature = 0.2) {
	return api<ReasonResponse>('/api/v1/reason', {
		method: 'POST',
		body: JSON.stringify({ prompt, max_tokens: maxTokens, temperature }),
	});
}

// ── SOC ─────────────────────────────────────────────────
export function getSOCStatus() {
	return api<SOCStatusResponse>('/api/soc/status');
}

export function ingestSOCAlert(alert: SOCAlert, source = 'generic') {
	return api<SOCIngestResponse>(`/api/soc/ingest?source=${encodeURIComponent(source)}`, {
		method: 'POST',
		body: JSON.stringify(alert),
	});
}

export function getUserRisk(userId: string) {
	return api<UserRiskProfile>(`/api/soc/user/${encodeURIComponent(userId)}`);
}

// ── Improvement Engine ──────────────────────────────────
export function getImprovementStatus() {
	return api<ImprovementStatus>('/api/v1/improvement/status');
}

export function submitFeedback(req: FeedbackRequest) {
	return api<{ success: boolean; feedback_id: string }>('/api/v1/improvement/feedback', {
		method: 'POST',
		body: JSON.stringify(req),
	});
}

export function getImprovementMetrics(windowDays = 30) {
	return api<DetectionMetrics>(`/api/v1/improvement/metrics?window_days=${windowDays}`);
}

export function runImprovementCycle() {
	return api<{ success: boolean; [key: string]: unknown }>('/api/v1/improvement/cycle', {
		method: 'POST',
	});
}

export function getProposals() {
	return api<{ success: boolean; proposals: PolicyProposal[] }>('/api/v1/improvement/proposals');
}

export function listPolicies() {
	return api<{ success: boolean; versions: PolicyVersion[] }>('/api/v1/improvement/policies');
}

export function getPolicy(version: number) {
	return api<{ success: boolean; policy: Record<string, unknown> }>(`/api/v1/improvement/policy/${version}`);
}

export function getPolicyDiff(fromVersion: number, toVersion: number) {
	return api<PolicyDiff>(`/api/v1/improvement/diff/${fromVersion}/${toVersion}`);
}

export function approveProposal(version: number, action: ProposalAction) {
	return api<{ success: boolean; [key: string]: unknown }>(`/api/v1/improvement/approve/${version}`, {
		method: 'POST',
		body: JSON.stringify(action),
	});
}

export function rejectProposal(version: number, action: ProposalAction) {
	return api<{ success: boolean; [key: string]: unknown }>(`/api/v1/improvement/reject/${version}`, {
		method: 'POST',
		body: JSON.stringify(action),
	});
}

export function rollbackPolicy(version: number, action: ProposalAction) {
	return api<{ success: boolean; [key: string]: unknown }>(`/api/v1/improvement/rollback/${version}`, {
		method: 'POST',
		body: JSON.stringify(action),
	});
}

export function getNudges() {
	return api<{ success: boolean; nudges: Nudge[] }>('/api/v1/improvement/nudges');
}

// ── Observability / Metrics ─────────────────────────────
export function getMetricsJson() {
	return api<MetricsJsonResponse>('/metrics/json');
}

export async function getMetricsPrometheus(): Promise<ApiResult<string>> {
	const headers: Record<string, string> = {};
	if (_apiKey) headers['X-API-Key'] = _apiKey;

	try {
		const res = await fetch(`${BASE_URL}/metrics`, { headers });
		if (!res.ok) {
			return { ok: false, error: { status: res.status, message: res.statusText } };
		}
		return { ok: true, data: await res.text() };
	} catch (err) {
		return { ok: false, error: { status: 0, message: err instanceof Error ? err.message : 'Network error' } };
	}
}
