"""
AION OS — License Tier Feature Gate
=====================================

Controls which engine layers, modules, and API endpoints are available
based on the deployment's license tier.

Tiers:
  BASELINE    ($45K)  — Temporal + Baseline engines, 40 generic patterns
  INTELLIGENCE ($90K) — + Hybrid engine, all 69 patterns, feedback/triage
  SENTINEL   ($150K)  — + RSI engine, adversarial red team, quantum, legal intel

The codebase is universal (67 core files). Tier gating is config-level —
a single env var (AION_LICENSE_TIER) toggles which features are active.
No code forks, no separate builds.
"""

import os
import logging
from enum import Enum
from typing import Dict, Set, Optional, Any
from dataclasses import dataclass, field

logger = logging.getLogger("aionos.licensing")


# =============================================================================
# TIER DEFINITIONS
# =============================================================================

class LicenseTier(str, Enum):
    """Product tiers for EchoWorks / AION OS deployment."""
    BASELINE = "baseline"           # Core Baseline — $45K
    INTELLIGENCE = "intelligence"   # Intelligence Hybrid — $90K
    SENTINEL = "sentinel"           # Enterprise Sentinel — $150K


# =============================================================================
# ENGINE LAYERS PER TIER
# =============================================================================

# Layer 1: Temporal Correlation Engine  (temporal_engine.py)
# Layer 2: Behavioral Baseline Engine   (baseline_engine.py)
# Layer 3: Hybrid Detection Engine      (hybrid_engine.py)
# Layer 4: Recursive Self-Improvement   (improvement_engine.py)
# Layer 5: Adversarial Red Team         (adversarial_engine.py, security_redteam.py)

TIER_ENGINE_LAYERS: Dict[LicenseTier, Set[str]] = {
    LicenseTier.BASELINE: {
        "temporal_engine",
        "baseline_engine",
        "pattern_matcher",
        "severity_triage",
        "intent_classifier",
        "persistence",
    },
    LicenseTier.INTELLIGENCE: {
        # Everything in BASELINE, plus:
        "temporal_engine",
        "baseline_engine",
        "pattern_matcher",
        "severity_triage",
        "intent_classifier",
        "persistence",
        "hybrid_engine",
        "reasoning_engine",
        "timeline_analyzer",
        "soc_ingestion",
        "attorney_departure",
        "attorney_departure_gem",
        "lateral_hire_gem",
        "feedback_collector",
    },
    LicenseTier.SENTINEL: {
        # Everything in INTELLIGENCE, plus:
        "temporal_engine",
        "baseline_engine",
        "pattern_matcher",
        "severity_triage",
        "intent_classifier",
        "persistence",
        "hybrid_engine",
        "reasoning_engine",
        "timeline_analyzer",
        "soc_ingestion",
        "attorney_departure",
        "attorney_departure_gem",
        "lateral_hire_gem",
        "feedback_collector",
        "improvement_engine",
        "candidate_generator",
        "evaluation_engine",
        "shadow_runner",
        "policy_store",
        "adversarial_engine",
        "security_redteam",
        "quantum_adversarial",
        "document_intelligence",
        "legal_analyzer",
        "report_generator",
        "heist_planner",
        "roi_calculator",
    },
}


# =============================================================================
# ATTACK PATTERN GATING
# =============================================================================

# Baseline: 40 generic insider-threat patterns (non-legal-specific)
# Intelligence: all 69 patterns including law-firm-specific sequences
# Sentinel: all 69 + adversarial red-team pattern generation

BASELINE_PATTERN_IDS = frozenset([
    # --- VPN / Network anomalies (8) ---
    "vpn_off_hours_access",
    "vpn_geographic_anomaly",
    "vpn_concurrent_sessions",
    "vpn_brute_force",
    "vpn_unusual_duration",
    "vpn_tor_exit_node",
    "vpn_protocol_downgrade",
    "vpn_split_tunnel_abuse",
    # --- Credential threats (6) ---
    "credential_stuffing",
    "credential_sharing",
    "credential_privilege_escalation",
    "credential_service_account_abuse",
    "credential_mfa_fatigue",
    "credential_password_spray",
    # --- File / Data exfiltration (8) ---
    "file_bulk_download",
    "file_usb_copy",
    "file_cloud_sync_unauthorized",
    "file_email_attachment_spike",
    "file_print_spike",
    "file_archive_creation",
    "file_sensitive_rename",
    "file_encryption_before_transfer",
    # --- Database / System (6) ---
    "database_bulk_query",
    "database_schema_export",
    "database_privilege_escalation",
    "system_log_deletion",
    "system_security_tool_disable",
    "system_scheduled_task_creation",
    # --- Email / Communication (6) ---
    "email_forwarding_rule",
    "email_external_auto_forward",
    "email_bcc_to_personal",
    "email_large_attachment_external",
    "email_contact_export",
    "email_distribution_list_abuse",
    # --- Behavioral (6) ---
    "behavior_after_hours_spike",
    "behavior_access_pattern_change",
    "behavior_resignation_indicator",
    "behavior_peer_deviation",
    "behavior_new_resource_access",
    "behavior_volume_anomaly",
])

# Intelligence+ only: Law-firm-specific sequences (29 additional)
LEGAL_SPECIFIC_PATTERN_IDS = frozenset([
    # --- Attorney departure sequences (8) ---
    "attorney_departure_client_list_export",
    "attorney_departure_matter_bulk_access",
    "attorney_departure_billing_data_export",
    "attorney_departure_work_product_download",
    "attorney_departure_conflict_check_mining",
    "attorney_departure_relationship_mapping",
    "attorney_departure_document_staging",
    "attorney_departure_slow_burn_exfil",
    # --- Lateral hire risk (5) ---
    "lateral_hire_prior_firm_data_upload",
    "lateral_hire_conflict_boundary_test",
    "lateral_hire_client_contact_import",
    "lateral_hire_competitive_intel_access",
    "lateral_hire_matter_reassignment_pattern",
    # --- Privilege-aware threats (6) ---
    "privilege_client_file_mass_access",
    "privilege_work_product_exfil",
    "privilege_matter_boundary_crossing",
    "privilege_engagement_letter_export",
    "privilege_retainer_data_mining",
    "privilege_case_strategy_access",
    # --- Practice-specific (5) ---
    "practice_merger_data_leak",
    "practice_ipo_quiet_period_breach",
    "practice_litigation_hold_violation",
    "practice_regulatory_filing_tampering",
    "practice_trust_account_anomaly",
    # --- Multi-stage law-firm sequences (5) ---
    "sequence_departure_to_competitor",
    "sequence_internal_poaching",
    "sequence_client_book_theft",
    "sequence_partner_defection",
    "sequence_practice_group_exodus",
])

ALL_PATTERN_IDS = BASELINE_PATTERN_IDS | LEGAL_SPECIFIC_PATTERN_IDS


def get_tier_patterns(tier: LicenseTier) -> frozenset:
    """Return the set of pattern IDs enabled for a given tier."""
    if tier == LicenseTier.BASELINE:
        return BASELINE_PATTERN_IDS
    return ALL_PATTERN_IDS  # Intelligence and Sentinel get all 69


# =============================================================================
# API ENDPOINT GATING
# =============================================================================

# Maps REST API action names (from require_role) to minimum tier required
TIER_ENDPOINT_GATES: Dict[str, LicenseTier] = {
    # === Always available (all tiers) ===
    "health": LicenseTier.BASELINE,
    "root": LicenseTier.BASELINE,
    "stats": LicenseTier.BASELINE,
    "soc_status": LicenseTier.BASELINE,
    "soc_ingest": LicenseTier.BASELINE,
    "soc_user_risk": LicenseTier.BASELINE,

    # === Intelligence tier and above ===
    "legal_analysis": LicenseTier.INTELLIGENCE,
    "improvement_status": LicenseTier.INTELLIGENCE,
    "improvement_feedback": LicenseTier.INTELLIGENCE,
    "improvement_metrics": LicenseTier.INTELLIGENCE,
    "improvement_nudges": LicenseTier.INTELLIGENCE,

    # === Sentinel tier only ===
    "security_analysis": LicenseTier.SENTINEL,
    "audit_logs": LicenseTier.SENTINEL,
    "improvement_cycle": LicenseTier.SENTINEL,
    "improvement_proposals": LicenseTier.SENTINEL,
    "improvement_approve": LicenseTier.SENTINEL,
    "improvement_reject": LicenseTier.SENTINEL,
    "improvement_policies": LicenseTier.SENTINEL,
    "improvement_policy": LicenseTier.SENTINEL,
    "improvement_diff": LicenseTier.SENTINEL,
    "improvement_rollback": LicenseTier.SENTINEL,
}


# =============================================================================
# TIER FEATURE METADATA (for comparison table / sales)
# =============================================================================

TIER_FEATURES: Dict[LicenseTier, Dict[str, Any]] = {
    LicenseTier.BASELINE: {
        "name": "Core Baseline",
        "price": "$45,000",
        "engine_layers": ["Temporal Correlation", "Behavioral Baseline"],
        "pattern_count": len(BASELINE_PATTERN_IDS),
        "event_types": 240,
        "modules": [
            "Pattern Matcher",
            "Severity Triage (P0–P4)",
            "Intent Classifier",
            "SOC Alert Ingestion",
            "Encrypted Persistence",
        ],
        "analyst_tools": ["SOC Dashboard", "Alert Queue", "Risk Scores"],
        "automation": "Manual — analyst-driven triage",
        "detection_latency": "< 500µs P95",
        "support": "Email + documentation",
        "ideal_for": "Insurance compliance, basic insider threat monitoring",
    },
    LicenseTier.INTELLIGENCE: {
        "name": "Intelligence Hybrid",
        "price": "$90,000",
        "engine_layers": [
            "Temporal Correlation",
            "Behavioral Baseline",
            "Hybrid Cross-Correlation",
        ],
        "pattern_count": len(ALL_PATTERN_IDS),
        "event_types": 240,
        "modules": [
            "Everything in Baseline, plus:",
            "Hybrid Detection Engine",
            "Attorney Departure Risk Module",
            "Lateral Hire Due Diligence",
            "Timeline Analyzer",
            "Feedback Collector",
            "Severity Triage + Analyst Workflows",
        ],
        "analyst_tools": [
            "SOC Dashboard",
            "Alert Queue + Feedback Loop",
            "Risk Scores + Behavioral Deviations",
            "Departure Risk Profiles",
            "Investigation Timelines",
        ],
        "automation": "Semi-automated — analyst feedback improves detection",
        "detection_latency": "< 200µs P95",
        "support": "Dedicated channel + monthly reviews",
        "ideal_for": "Am Law 200 firms, proactive departure risk management",
    },
    LicenseTier.SENTINEL: {
        "name": "Enterprise Sentinel",
        "price": "$150,000",
        "engine_layers": [
            "Temporal Correlation",
            "Behavioral Baseline",
            "Hybrid Cross-Correlation",
            "Recursive Self-Improvement (RSI)",
            "Adversarial Red Team",
        ],
        "pattern_count": f"{len(ALL_PATTERN_IDS)}+ (self-generating)",
        "event_types": 240,
        "modules": [
            "Everything in Intelligence, plus:",
            "Self-Improvement Engine (8-step cycle)",
            "Adversarial Red Team Simulation",
            "Quantum-Inspired Attack Path Analysis",
            "Document Intelligence (deep clause analysis)",
            "Legal Analyzer (opposing counsel simulation)",
            "Shadow Mode Policy Evaluation",
            "Enterprise PDF Report Generator",
            "ROI Calculator (financial impact)",
        ],
        "analyst_tools": [
            "Everything in Intelligence, plus:",
            "Policy Version Control + Diff Viewer",
            "Proposal Review + Approve/Reject",
            "Shadow Run Before/After Comparison",
            "Improvement Nudges",
            "Full Audit Trail",
        ],
        "automation": (
            "Autonomous — RSI tunes detection policies within "
            "9 immutable safety invariants. Human approves final changes."
        ),
        "detection_latency": "< 85µs P95",
        "support": "Dedicated engineering + quarterly red team exercises",
        "ideal_for": "Am Law 100 firms, hands-off self-tuning defense",
    },
}


# =============================================================================
# TIER CONFIG — Runtime singleton
# =============================================================================

@dataclass
class TierConfig:
    """Runtime tier configuration. Loaded from AION_LICENSE_TIER env var."""
    tier: LicenseTier = LicenseTier.SENTINEL  # Default to full access for dev
    license_id: str = ""
    licensed_to: str = ""
    max_users: int = 500
    expires: str = ""

    @property
    def engines(self) -> Set[str]:
        return TIER_ENGINE_LAYERS[self.tier]

    @property
    def patterns(self) -> frozenset:
        return get_tier_patterns(self.tier)

    @property
    def pattern_count(self) -> int:
        return len(self.patterns)

    @property
    def features(self) -> Dict[str, Any]:
        return TIER_FEATURES[self.tier]

    def is_engine_enabled(self, engine_name: str) -> bool:
        """Check if a specific engine/module is enabled for this tier."""
        return engine_name in self.engines

    def is_endpoint_allowed(self, action: str) -> bool:
        """Check if an API endpoint action is allowed for this tier."""
        required_tier = TIER_ENDPOINT_GATES.get(action)
        if required_tier is None:
            return True  # Ungated endpoints are allowed
        return _tier_rank(self.tier) >= _tier_rank(required_tier)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tier": self.tier.value,
            "tier_name": self.features["name"],
            "license_id": self.license_id,
            "licensed_to": self.licensed_to,
            "max_users": self.max_users,
            "expires": self.expires,
            "engines_enabled": sorted(self.engines),
            "pattern_count": self.pattern_count,
            "endpoint_gates": {
                action: self.is_endpoint_allowed(action)
                for action in TIER_ENDPOINT_GATES
            },
        }


def _tier_rank(tier: LicenseTier) -> int:
    """Numeric rank for tier comparison."""
    return {
        LicenseTier.BASELINE: 1,
        LicenseTier.INTELLIGENCE: 2,
        LicenseTier.SENTINEL: 3,
    }[tier]


# =============================================================================
# GLOBAL SINGLETON
# =============================================================================

_global_tier_config: Optional[TierConfig] = None


def get_tier_config() -> TierConfig:
    """
    Get the global tier configuration.

    Reads from AION_LICENSE_TIER env var on first call.
    Valid values: 'baseline', 'intelligence', 'sentinel'
    Default: 'sentinel' (full access for development).
    """
    global _global_tier_config
    if _global_tier_config is None:
        tier_str = os.environ.get("AION_LICENSE_TIER", "sentinel").lower()
        try:
            tier = LicenseTier(tier_str)
        except ValueError:
            logger.warning(
                f"Unknown AION_LICENSE_TIER='{tier_str}', defaulting to sentinel"
            )
            tier = LicenseTier.SENTINEL

        _global_tier_config = TierConfig(
            tier=tier,
            license_id=os.environ.get("AION_LICENSE_ID", ""),
            licensed_to=os.environ.get("AION_LICENSED_TO", ""),
            max_users=int(os.environ.get("AION_MAX_USERS", "500")),
            expires=os.environ.get("AION_LICENSE_EXPIRES", ""),
        )
        logger.info(
            f"License tier: {tier.value} ({TIER_FEATURES[tier]['name']}) — "
            f"{_global_tier_config.pattern_count} patterns, "
            f"{len(_global_tier_config.engines)} engines"
        )
    return _global_tier_config


def reset_tier_config():
    """Reset the global config (for testing)."""
    global _global_tier_config
    _global_tier_config = None
