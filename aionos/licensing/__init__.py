"""AION OS — Licensing & Feature Gating"""

from .tier_config import (
    LicenseTier,
    TierConfig,
    get_tier_config,
    reset_tier_config,
    get_tier_patterns,
    TIER_FEATURES,
    TIER_ENGINE_LAYERS,
    TIER_ENDPOINT_GATES,
    BASELINE_PATTERN_IDS,
    LEGAL_SPECIFIC_PATTERN_IDS,
    ALL_PATTERN_IDS,
)

__all__ = [
    "LicenseTier",
    "TierConfig",
    "get_tier_config",
    "reset_tier_config",
    "get_tier_patterns",
    "TIER_FEATURES",
    "TIER_ENGINE_LAYERS",
    "TIER_ENDPOINT_GATES",
    "BASELINE_PATTERN_IDS",
    "LEGAL_SPECIFIC_PATTERN_IDS",
    "ALL_PATTERN_IDS",
]
