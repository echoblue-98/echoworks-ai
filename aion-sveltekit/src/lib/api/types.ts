// ═══════════════════════════════════════════════════════════
// AION OS — TypeScript Types for REST API
// Maps 1:1 to FastAPI Pydantic models in rest_api.py
// ═══════════════════════════════════════════════════════════

// ── Health ──────────────────────────────────────────────
export interface HealthResponse {
	status: 'operational' | 'degraded' | 'down';
	version: string;
	timestamp: string;
}

// ── Analysis ────────────────────────────────────────────
export interface AnalysisRequest {
	content: string;
	context?: Record<string, unknown>;
	intensity?: number; // 1-5
	user_id?: string;
}

export interface LegalAnalysisRequest extends AnalysisRequest {
	analysis_type?: 'brief' | 'contract' | 'argument';
}

export interface SecurityAnalysisRequest extends AnalysisRequest {
	scan_type?: 'infrastructure' | 'posture' | 'attack_chain';
}

export interface Vulnerability {
	title: string;
	severity: string;
	description?: string;
	confidence?: number;
	attack_vector?: string;
	countermeasures?: string[];
}

export interface AnalysisResponse {
	success: boolean;
	analysis_id: string;
	timestamp: string;
	summary: {
		total_found?: number;
		above_confidence_threshold?: number;
		critical_p0?: number;
		high_p1?: number;
		medium_p2?: number;
		low_p3?: number;
	};
	critical_vulnerabilities: Vulnerability[];
	formatted_output: string;
	perspectives_used: string[];
	intensity_level: number;
	blocked: boolean;
	block_reason?: string;
}

// ── Statistics ──────────────────────────────────────────
export interface StatsResponse {
	success: boolean;
	timestamp: string;
	statistics: {
		total_queries?: number;
		total_analyses?: number;
		total_vulnerabilities?: number;
		total_critical?: number;
		queries_blocked?: number;
		[key: string]: unknown;
	};
}

// ── SOC ─────────────────────────────────────────────────
export interface SOCAlert {
	id?: string;
	timestamp?: string;
	alert_type: string;
	severity: 'low' | 'medium' | 'high' | 'critical';
	user_id: string;
	user_email?: string;
	source_ip?: string;
	source_location?: string;
	destination?: string;
	action: string;
	details: Record<string, unknown>;
}

export interface HighRiskUser {
	user_id: string;
	risk_score: number;
	alert_count: number;
	[key: string]: unknown;
}

export interface SOCStatusResponse {
	status: string;
	total_alerts: number;
	high_risk_users: HighRiskUser[];
	recent_alerts: SOCAlert[];
	pattern_detections: number;
}

export interface SOCIngestResponse {
	success: boolean;
	alert_id: string;
	departure_risk_score: number;
	pattern_matches: string[];
	severity: string;
	user_id: string;
	warning?: string;
	pattern_alert?: string;
	agent_analysis?: unknown;
	escalated?: boolean;
}

export interface UserRiskProfile {
	user_id: string;
	risk_score: number;
	alert_history: SOCAlert[];
	recommendations: string[];
	[key: string]: unknown;
}

// ── Improvement Engine ──────────────────────────────────
export interface ImprovementStatus {
	success: boolean;
	active_policy_version?: number;
	total_feedback?: number;
	pending_proposals?: number;
	cycle_count?: number;
	[key: string]: unknown;
}

export interface FeedbackRequest {
	alert_id?: string;
	feedback_type: 'alert_correct' | 'alert_noisy' | 'alert_missed' | 'mis_categorized' | 'near_miss' | 'duplicate';
	analyst_id: string;
	corrected_severity?: string;
	corrected_category?: string;
	notes?: string;
	triage_start?: string;
	triage_end?: string;
}

export interface DetectionMetrics {
	success: boolean;
	metrics: {
		precision?: number;
		recall?: number;
		f1_score?: number;
		noise_ratio?: number;
		[key: string]: unknown;
	};
	score: number;
}

export interface PolicyProposal {
	version: number;
	status: string;
	changes?: string;
	created_at?: string;
	metrics_before?: Record<string, unknown>;
	metrics_after?: Record<string, unknown>;
	[key: string]: unknown;
}

export interface PolicyVersion {
	version: number;
	active: boolean;
	created_at?: string;
	[key: string]: unknown;
}

export interface PolicyDiff {
	success: boolean;
	diff: {
		from_version: number;
		to_version: number;
		changes: unknown[];
		[key: string]: unknown;
	};
}

export interface ProposalAction {
	analyst_id: string;
	notes?: string;
}

export interface Nudge {
	id: string;
	message: string;
	category: string;
	priority: number;
	[key: string]: unknown;
}

// ── Observability / Metrics ─────────────────────────────
export interface MetricEntry {
	name: string;
	type: 'counter' | 'gauge' | 'histogram';
	value: number;
	labels?: Record<string, string>;
	help?: string;
}

export interface MetricsJsonResponse {
	metrics: MetricEntry[];
	timestamp: string;
	[key: string]: unknown;
}

// ── Audit Logs ──────────────────────────────────────────
export interface AuditLog {
	id: string;
	timestamp: string;
	event_type: string;
	user_id?: string;
	details?: Record<string, unknown>;
	severity?: string;
}

export interface AuditLogsResponse {
	success: boolean;
	count: number;
	logs: AuditLog[];
}

// ── Generic API wrapper ─────────────────────────────────
export interface ApiError {
	status: number;
	message: string;
	detail?: string;
}

export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: ApiError };
