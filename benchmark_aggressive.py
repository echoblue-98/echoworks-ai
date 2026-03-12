"""
AION OS - AGGRESSIVE BENCHMARK
================================

Full-spectrum stress test of every engine in AION OS:
  - Temporal Correlation Engine (66+ patterns, 50K-500K events)
  - Behavioral Baseline Engine (anomaly detection under load)
  - Improvement Engine (policy store, evaluation, shadow mode)
  - Hybrid Detection Engine (local pattern matching)
  - Full pipeline throughput (all engines chained)

Metrics collected:
  - Latency: avg, min, max, P50, P95, P99
  - Throughput: events/sec sustained
  - Memory: RSS before/after
  - Accuracy: detection rate on known scenarios
  - Policy ops: version create/diff/rollback speed
  - Improvement cycle: end-to-end overhead

Run: python benchmark_aggressive.py
"""

import gc
import os
import sys
import time
import random
import statistics
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

# Windows encoding fix
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

import warnings
warnings.filterwarnings("ignore")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

WARMUP_EVENTS = 1000
STRESS_EVENTS = 100_000      # Main stress test
BURST_EVENTS = 10_000        # Burst within 1 second
CONCURRENT_USERS = 5000      # Simulated users
POLICY_ITERATIONS = 200      # Policy store ops
IMPROVEMENT_CYCLES = 10      # Full improvement cycles
ATTACK_REPLAY_SCENARIOS = 50 # Shadow replay depth
MEMORY_PRESSURE_EVENTS = 200_000  # Memory stress test


def get_memory_mb():
    """Get current RSS in MB."""
    try:
        import psutil
        return psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
    except ImportError:
        return 0.0


def percentile(data, p):
    """Compute percentile."""
    if not data:
        return 0.0
    k = (len(data) - 1) * (p / 100)
    f = int(k)
    c = f + 1 if f + 1 < len(data) else f
    d = k - f
    return data[f] + d * (data[c] - data[f])


def fmt_rate(label, value, unit="events/sec", width=35):
    bar_len = min(int(value / 500), 40)
    bar = chr(9608) * bar_len
    return f"  {label:<{width}} {value:>10,.0f} {unit}  {bar}"


def fmt_latency(label, value, unit="ms", width=35):
    return f"  {label:<{width}} {value:>10.3f} {unit}"


def section(title):
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"{'=' * 72}")


def subsection(title):
    print(f"\n  --- {title} ---")


# ═══════════════════════════════════════════════════════════════════════════════
# 1. IMPORT & INIT BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

def bench_imports():
    section("1. IMPORT LATENCY")
    results = {}

    modules = [
        ("TemporalCorrelationEngine", "aionos.core.temporal_engine",
         "TemporalCorrelationEngine, SecurityEvent, EventType, AttackSequence, CorrelationAlert"),
        ("BehavioralBaselineEngine", "aionos.core.baseline_engine",
         "BehavioralBaselineEngine"),
        ("HybridDetectionEngine", "aionos.core.hybrid_engine",
         "HybridDetectionEngine"),
        ("LocalSecurityAttacker", "aionos.core.local_security_attacker",
         "LocalSecurityAttacker"),
        ("ImprovementEngine", "aionos.improvement",
         "ImprovementEngine, PolicyStore, EvaluationEngine, CandidateGenerator, ShadowRunner, FeedbackCollector"),
        ("SOCIngestionEngine", "aionos.modules.soc_ingestion",
         "SOCIngestionEngine"),
        ("AuditLogger", "aionos.safety.audit_logger",
         "AuditLogger"),
    ]

    for name, mod_path, _ in modules:
        start = time.perf_counter()
        __import__(mod_path)
        elapsed = (time.perf_counter() - start) * 1000
        results[name] = elapsed
        print(fmt_latency(name, elapsed))

    total = sum(results.values())
    print(f"\n  {'TOTAL':<35} {total:>10.3f} ms")
    return results


def bench_init():
    section("2. INITIALIZATION LATENCY")
    from aionos.core.temporal_engine import TemporalCorrelationEngine
    from aionos.core.baseline_engine import BehavioralBaselineEngine
    from aionos.core.local_security_attacker import LocalSecurityAttacker
    from aionos.improvement import ImprovementEngine, PolicyStore, EvaluationEngine

    results = {}

    # Temporal Engine
    start = time.perf_counter()
    temporal = TemporalCorrelationEngine(fast_mode=True)
    results["TemporalEngine"] = (time.perf_counter() - start) * 1000
    print(fmt_latency("TemporalEngine (fast_mode)", results["TemporalEngine"]))
    print(f"    Patterns loaded: {len(temporal.attack_sequences)}")

    # Baseline Engine
    start = time.perf_counter()
    baseline = BehavioralBaselineEngine(fast_mode=True)
    results["BaselineEngine"] = (time.perf_counter() - start) * 1000
    print(fmt_latency("BaselineEngine (fast_mode)", results["BaselineEngine"]))

    # LocalSecurityAttacker
    start = time.perf_counter()
    attacker = LocalSecurityAttacker()
    results["LocalSecurityAttacker"] = (time.perf_counter() - start) * 1000
    print(fmt_latency("LocalSecurityAttacker", results["LocalSecurityAttacker"]))

    # PolicyStore
    start = time.perf_counter()
    policy_store = PolicyStore()
    results["PolicyStore"] = (time.perf_counter() - start) * 1000
    print(fmt_latency("PolicyStore", results["PolicyStore"]))

    # EvaluationEngine
    start = time.perf_counter()
    eval_engine = EvaluationEngine()
    results["EvaluationEngine"] = (time.perf_counter() - start) * 1000
    print(fmt_latency("EvaluationEngine", results["EvaluationEngine"]))

    # ImprovementEngine (full init)
    start = time.perf_counter()
    improvement = ImprovementEngine(llm_provider="mock")
    improvement.initialize()
    results["ImprovementEngine"] = (time.perf_counter() - start) * 1000
    print(fmt_latency("ImprovementEngine (full)", results["ImprovementEngine"]))

    total = sum(results.values())
    print(f"\n  {'TOTAL':<35} {total:>10.3f} ms")

    return results, temporal, baseline, attacker, improvement


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TEMPORAL ENGINE STRESS TEST
# ═══════════════════════════════════════════════════════════════════════════════

def bench_temporal(temporal):
    section("3. TEMPORAL CORRELATION ENGINE — STRESS TEST")
    from aionos.core.temporal_engine import SecurityEvent, EventType

    event_types = list(EventType)
    results = {}

    # --- Warmup ---
    subsection(f"Warmup ({WARMUP_EVENTS:,} events)")
    for i in range(WARMUP_EVENTS):
        event = SecurityEvent(
            event_id=f"warmup_{i}",
            user_id=f"warmup_user_{i % 100}",
            event_type=random.choice(event_types),
            timestamp=datetime.utcnow(),
            source_system="benchmark",
            details={"bench": True},
        )
        temporal.ingest_event(event)
    print(f"  Warmup complete")

    # --- Sustained throughput ---
    subsection(f"Sustained throughput ({STRESS_EVENTS:,} events)")
    gc.disable()
    latencies = []
    alerts_generated = 0
    start_wall = time.perf_counter()

    for i in range(STRESS_EVENTS):
        user = f"user_{i % CONCURRENT_USERS}@lawfirm.com"
        event = SecurityEvent(
            event_id=f"stress_{i}",
            user_id=user,
            event_type=random.choice(event_types),
            timestamp=datetime.utcnow() - timedelta(seconds=random.randint(0, 86400)),
            source_system="siem_benchmark",
            details={"file_count": random.randint(1, 100), "bench": True},
        )
        t0 = time.perf_counter()
        alerts = temporal.ingest_event(event)
        latencies.append((time.perf_counter() - t0) * 1_000_000)  # microseconds
        alerts_generated += len(alerts)

    wall_time = time.perf_counter() - start_wall
    gc.enable()

    latencies.sort()
    results["sustained"] = {
        "total_events": STRESS_EVENTS,
        "wall_time_s": wall_time,
        "throughput": STRESS_EVENTS / wall_time,
        "avg_us": statistics.mean(latencies),
        "min_us": min(latencies),
        "max_us": max(latencies),
        "p50_us": percentile(latencies, 50),
        "p95_us": percentile(latencies, 95),
        "p99_us": percentile(latencies, 99),
        "alerts": alerts_generated,
    }

    r = results["sustained"]
    print(fmt_rate("Throughput", r["throughput"]))
    print(fmt_latency("Avg latency", r["avg_us"], "us"))
    print(fmt_latency("P50 latency", r["p50_us"], "us"))
    print(fmt_latency("P95 latency", r["p95_us"], "us"))
    print(fmt_latency("P99 latency", r["p99_us"], "us"))
    print(fmt_latency("Max latency", r["max_us"], "us"))
    print(f"  {'Alerts generated':<35} {r['alerts']:>10,}")
    print(f"  {'Unique users':<35} {CONCURRENT_USERS:>10,}")
    print(f"  {'Wall time':<35} {r['wall_time_s']:>10.2f} s")

    # --- Burst test ---
    subsection(f"Burst test ({BURST_EVENTS:,} events, single user)")
    burst_user = "burst_target@lawfirm.com"
    burst_latencies = []
    burst_start = time.perf_counter()

    for i in range(BURST_EVENTS):
        event = SecurityEvent(
            event_id=f"burst_{i}",
            user_id=burst_user,
            event_type=random.choice(event_types),
            timestamp=datetime.utcnow(),
            source_system="burst_test",
            details={"burst": True},
        )
        t0 = time.perf_counter()
        temporal.ingest_event(event)
        burst_latencies.append((time.perf_counter() - t0) * 1_000_000)

    burst_wall = time.perf_counter() - burst_start
    burst_latencies.sort()
    results["burst"] = {
        "throughput": BURST_EVENTS / burst_wall,
        "avg_us": statistics.mean(burst_latencies),
        "p99_us": percentile(burst_latencies, 99),
        "wall_time_s": burst_wall,
    }
    print(fmt_rate("Burst throughput", results["burst"]["throughput"]))
    print(fmt_latency("Burst avg latency", results["burst"]["avg_us"], "us"))
    print(fmt_latency("Burst P99 latency", results["burst"]["p99_us"], "us"))

    # --- Multi-stage attack detection accuracy ---
    subsection("Attack detection accuracy (known patterns)")
    # Inject a known Typhoon-style insider threat sequence
    attack_events = [
        (EventType.VPN_ACCESS, 0),
        (EventType.DATABASE_QUERY, 3),
        (EventType.BULK_OPERATION, 7),
        (EventType.FILE_DOWNLOAD, 10),
        (EventType.USB_ACTIVITY, 11),
    ]

    # Use fresh engine for clean detection
    fresh_temporal = type(temporal)(fast_mode=True)
    attack_alerts = []
    for etype, day_offset in attack_events:
        event = SecurityEvent(
            event_id=f"attack_{etype.value}",
            user_id="knowles_test_target",
            event_type=etype,
            timestamp=datetime.utcnow() - timedelta(days=14 - day_offset),
            source_system="test_harness",
            details={"attack_sim": True},
        )
        alerts = fresh_temporal.ingest_event(event)
        attack_alerts.extend(alerts)

    detected = len(attack_alerts) > 0
    results["detection_accuracy"] = {
        "typhoon_detected": detected,
        "alerts_count": len(attack_alerts),
        "patterns_matched": [a.pattern_name for a in attack_alerts] if attack_alerts else [],
    }
    status = "DETECTED" if detected else "MISSED"
    print(f"  {'Typhoon insider theft':<35} {status}")
    if attack_alerts:
        for a in attack_alerts[:3]:
            print(f"    Pattern: {a.pattern_name} ({a.completion_percent:.0%} complete)")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 4. BASELINE ENGINE STRESS TEST
# ═══════════════════════════════════════════════════════════════════════════════

def bench_baseline(baseline):
    section("4. BEHAVIORAL BASELINE ENGINE — STRESS TEST")

    event_types_str = [
        "vpn_access", "file_download", "database_query", "email_forward",
        "print_job", "usb_activity", "cloud_sync", "bulk_operation",
    ]
    results = {}

    # Build baselines for many users
    subsection(f"Building baselines ({CONCURRENT_USERS:,} users)")
    build_latencies = []
    build_start = time.perf_counter()

    for i in range(CONCURRENT_USERS):
        user = f"baseline_user_{i}@lawfirm.com"
        for _ in range(5):  # 5 events per user to establish baseline
            t0 = time.perf_counter()
            baseline.record_event(
                user_id=user,
                event_type=random.choice(event_types_str),
                timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                details={"file_count": random.randint(1, 10)},
            )
            build_latencies.append((time.perf_counter() - t0) * 1_000_000)

    build_wall = time.perf_counter() - build_start
    build_latencies.sort()
    results["baseline_build"] = {
        "users": CONCURRENT_USERS,
        "events": CONCURRENT_USERS * 5,
        "throughput": (CONCURRENT_USERS * 5) / build_wall,
        "avg_us": statistics.mean(build_latencies),
        "p99_us": percentile(build_latencies, 99),
    }
    print(fmt_rate("Build throughput", results["baseline_build"]["throughput"]))
    print(fmt_latency("Avg latency", results["baseline_build"]["avg_us"], "us"))

    # Anomaly detection under load
    subsection(f"Anomaly detection ({BURST_EVENTS:,} events)")
    anomaly_latencies = []
    deviations_found = 0
    anomaly_start = time.perf_counter()

    for i in range(BURST_EVENTS):
        user = f"baseline_user_{i % CONCURRENT_USERS}@lawfirm.com"
        t0 = time.perf_counter()
        devs = baseline.record_event(
            user_id=user,
            event_type=random.choice(event_types_str),
            timestamp=datetime.utcnow(),
            details={"file_count": random.randint(50, 500)},  # Spike!
        )
        anomaly_latencies.append((time.perf_counter() - t0) * 1_000_000)
        if devs:
            deviations_found += len(devs)

    anomaly_wall = time.perf_counter() - anomaly_start
    anomaly_latencies.sort()
    results["anomaly_detection"] = {
        "throughput": BURST_EVENTS / anomaly_wall,
        "avg_us": statistics.mean(anomaly_latencies),
        "p99_us": percentile(anomaly_latencies, 99),
        "deviations": deviations_found,
    }
    print(fmt_rate("Detection throughput", results["anomaly_detection"]["throughput"]))
    print(fmt_latency("Avg latency", results["anomaly_detection"]["avg_us"], "us"))
    print(f"  {'Deviations detected':<35} {deviations_found:>10,}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 5. IMPROVEMENT ENGINE BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

def bench_improvement(improvement):
    section("5. IMPROVEMENT ENGINE — BENCHMARK")
    from aionos.improvement import PolicyStore, PolicyVersion, EvaluationEngine
    from aionos.improvement.policy_store import DetectionThresholds, PatternWeight
    from aionos.improvement.feedback_collector import AnalystFeedback, FeedbackType
    from aionos.improvement.evaluation_engine import AlertOutcome, TestScenario

    results = {}

    # --- Policy store operations ---
    subsection(f"Policy store operations ({POLICY_ITERATIONS} versions)")
    policy_store = improvement.policy_store

    create_times = []
    diff_times = []
    rollback_times = []

    for i in range(POLICY_ITERATIONS):
        # Create version with random threshold variations
        policy = PolicyVersion(
            version=0,
            created_by="benchmark",
            description=f"Benchmark policy iteration {i}",
            thresholds=DetectionThresholds(
                mfa_fatigue_threshold=random.randint(2, 15),
                volume_spike_multiplier=round(random.uniform(1.5, 10.0), 2),
                baseline_confidence_threshold=round(random.uniform(0.1, 0.9), 2),
                correlation_window_days=random.randint(7, 30),
                min_stages_to_alert=random.randint(2, 5),
            ),
            pattern_weights={
                f"pattern_{j}": PatternWeight(
                    pattern_name=f"pattern_{j}",
                    weight=round(random.uniform(0.1, 2.0), 2),
                    enabled=random.random() > 0.1,  # 90% enabled
                )
                for j in range(20)
            },
        )

        t0 = time.perf_counter()
        try:
            created = policy_store.create_version(policy, validate=True)
            create_times.append((time.perf_counter() - t0) * 1000)
        except ValueError:
            # Invariant violation — expected sometimes
            create_times.append((time.perf_counter() - t0) * 1000)
            continue

    # Diff benchmark
    versions = policy_store.list_versions()
    if len(versions) >= 2:
        for i in range(min(50, len(versions) - 1)):
            v1 = versions[i]["version"]
            v2 = versions[i + 1]["version"]
            t0 = time.perf_counter()
            policy_store.diff(v1, v2)
            diff_times.append((time.perf_counter() - t0) * 1000)

    # Rollback benchmark
    if len(versions) >= 3:
        for i in range(min(20, len(versions) - 2)):
            t0 = time.perf_counter()
            try:
                policy_store.rollback(
                    versions[i]["version"],
                    reason=f"Benchmark rollback {i}",
                )
                rollback_times.append((time.perf_counter() - t0) * 1000)
            except Exception:
                rollback_times.append((time.perf_counter() - t0) * 1000)

    results["policy_create"] = {
        "count": len(create_times),
        "avg_ms": statistics.mean(create_times) if create_times else 0,
        "p99_ms": percentile(sorted(create_times), 99) if create_times else 0,
    }
    results["policy_diff"] = {
        "count": len(diff_times),
        "avg_ms": statistics.mean(diff_times) if diff_times else 0,
    }
    results["policy_rollback"] = {
        "count": len(rollback_times),
        "avg_ms": statistics.mean(rollback_times) if rollback_times else 0,
    }

    print(fmt_latency(f"Create ({len(create_times)} versions)", results["policy_create"]["avg_ms"]))
    print(fmt_latency(f"Diff ({len(diff_times)} diffs)", results["policy_diff"]["avg_ms"]))
    print(fmt_latency(f"Rollback ({len(rollback_times)} rollbacks)", results["policy_rollback"]["avg_ms"]))
    print(f"  {'Total versions stored':<35} {len(policy_store.list_versions()):>10,}")

    # --- Feedback ingestion throughput ---
    subsection("Feedback ingestion throughput")
    feedback_count = 5000
    feedback_times = []
    feedback_types = [
        FeedbackType.ALERT_CORRECT.value,
        FeedbackType.ALERT_NOISY.value,
        FeedbackType.ALERT_MISSED.value,
        FeedbackType.ALERT_MIS_CATEGORIZED.value,
        FeedbackType.ALERT_NEAR_MISS.value,
    ]

    for i in range(feedback_count):
        fb = AnalystFeedback(
            feedback_type=random.choice(feedback_types),
            analyst_id=f"analyst_{i % 10}",
            alert_id=f"alert_{i}",
            notes=f"Benchmark feedback {i}",
            triage_seconds=round(random.uniform(5, 600), 1),
        )
        t0 = time.perf_counter()
        improvement.record_feedback(fb)
        feedback_times.append((time.perf_counter() - t0) * 1000)

    feedback_times.sort()
    results["feedback_ingestion"] = {
        "count": feedback_count,
        "throughput": feedback_count / (sum(feedback_times) / 1000),
        "avg_ms": statistics.mean(feedback_times),
        "p99_ms": percentile(feedback_times, 99),
    }
    print(fmt_rate("Feedback throughput", results["feedback_ingestion"]["throughput"], "fb/sec"))
    print(fmt_latency("Avg latency", results["feedback_ingestion"]["avg_ms"]))

    # --- Metrics computation ---
    subsection("Metrics computation")
    metrics_times = []
    for _ in range(20):
        t0 = time.perf_counter()
        metrics = improvement.evaluation.compute_metrics()
        metrics_times.append((time.perf_counter() - t0) * 1000)

    results["metrics_compute"] = {
        "avg_ms": statistics.mean(metrics_times),
        "p99_ms": percentile(sorted(metrics_times), 99),
        "last_score": metrics.score(),
        "precision": metrics.precision,
        "recall": metrics.recall_approx,
    }
    print(fmt_latency("Avg metrics compute", results["metrics_compute"]["avg_ms"]))
    print(f"  {'Composite score':<35} {results['metrics_compute']['last_score']:>10.1f} / 100")
    print(f"  {'Precision':<35} {results['metrics_compute']['precision']:>10.2%}")
    print(f"  {'Recall':<35} {results['metrics_compute']['recall']:>10.2%}")

    # --- Full improvement cycle ---
    subsection(f"Full improvement cycles ({IMPROVEMENT_CYCLES}x)")
    cycle_times = []
    for i in range(IMPROVEMENT_CYCLES):
        t0 = time.perf_counter()
        result = improvement.run_improvement_cycle()
        cycle_times.append((time.perf_counter() - t0) * 1000)

    results["improvement_cycle"] = {
        "count": IMPROVEMENT_CYCLES,
        "avg_ms": statistics.mean(cycle_times),
        "max_ms": max(cycle_times),
        "p99_ms": percentile(sorted(cycle_times), 99),
    }
    print(fmt_latency(f"Avg cycle time", results["improvement_cycle"]["avg_ms"]))
    print(fmt_latency(f"Max cycle time", results["improvement_cycle"]["max_ms"]))

    # --- Test suite execution ---
    subsection("Test suite execution")
    test_times = []
    for _ in range(10):
        t0 = time.perf_counter()
        test_result = improvement.evaluation.run_test_suite(
            engine_callback=lambda events: [],  # Stub for speed test
        )
        test_times.append((time.perf_counter() - t0) * 1000)

    results["test_suite"] = {
        "avg_ms": statistics.mean(test_times),
        "scenarios": test_result.get("total", 0),
    }
    print(fmt_latency("Avg test suite run", results["test_suite"]["avg_ms"]))
    print(f"  {'Scenarios':<35} {results['test_suite']['scenarios']:>10}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 6. SHADOW MODE BENCHMARK
# ═══════════════════════════════════════════════════════════════════════════════

def bench_shadow():
    section("6. SHADOW MODE — REPLAY BENCHMARK")
    from aionos.improvement.shadow_runner import ShadowRunner
    from aionos.improvement.policy_store import (
        PolicyVersion, DetectionThresholds, PatternWeight,
    )

    shadow = ShadowRunner()
    results = {}

    # Generate historical events for replay
    event_types = [
        "vpn_access", "file_download", "database_query", "email_forward",
        "usb_activity", "cloud_sync", "bulk_operation", "print_job",
    ]
    historical_events = [
        {
            "event_type": random.choice(event_types),
            "user_id": f"user_{i % 500}",
            "timestamp": (datetime.utcnow() - timedelta(days=random.randint(0, 30))).isoformat(),
            "severity": random.choice(["P0", "P1", "P2", "P3", "P4"]),
            "details": {"file_count": random.randint(1, 100)},
        }
        for i in range(ATTACK_REPLAY_SCENARIOS * 100)
    ]

    # Guardrail check benchmark
    subsection("Guardrail enforcement")
    baseline_policy = PolicyVersion(
        version=1,
        thresholds=DetectionThresholds(),
    ).to_dict()

    # Test safe candidate
    safe_candidate = PolicyVersion(
        version=2,
        thresholds=DetectionThresholds(mfa_fatigue_threshold=5),
    ).to_dict()

    # Test unsafe candidate (violates invariants)
    unsafe_candidate = PolicyVersion(
        version=3,
        thresholds=DetectionThresholds(
            min_stages_to_alert=1,  # VIOLATION: min is 2
            event_ttl_days=3,       # VIOLATION: min is 7
        ),
    ).to_dict()

    guardrail_times = []
    violations_caught = 0
    for _ in range(1000):
        candidate = random.choice([safe_candidate, unsafe_candidate])
        t0 = time.perf_counter()
        violations = shadow.check_guardrails(candidate, baseline_policy)
        guardrail_times.append((time.perf_counter() - t0) * 1_000_000)
        if violations:
            violations_caught += 1

    guardrail_times.sort()
    results["guardrails"] = {
        "avg_us": statistics.mean(guardrail_times),
        "p99_us": percentile(guardrail_times, 99),
        "violations_caught": violations_caught,
        "total_checks": 1000,
    }
    print(fmt_latency("Avg guardrail check", results["guardrails"]["avg_us"], "us"))
    print(f"  {'Violations caught':<35} {violations_caught:>10} / 1000")

    # Full shadow evaluation
    subsection("Full shadow evaluation")

    # Mock engine factory — returns a simple object with ingest method
    class MockEngine:
        def __init__(self, policy):
            self.alerts = []
        def ingest(self, event):
            if random.random() < 0.05:
                return [{"alert_type": "mock_alert", "user_id": event.get("user_id", ""), "severity": "P2"}]
            return []

    shadow_times = []
    for i in range(5):
        t0 = time.perf_counter()
        result = shadow.evaluate_candidate(
            proposal_id=f"bench_proposal_{i}",
            candidate_policy=safe_candidate,
            baseline_policy=baseline_policy,
            historical_events=historical_events[:1000],
            engine_factory=lambda p: MockEngine(p),
        )
        shadow_times.append((time.perf_counter() - t0) * 1000)

    results["shadow_eval"] = {
        "avg_ms": statistics.mean(shadow_times),
        "max_ms": max(shadow_times),
        "events_replayed": 1000,
        "last_verdict": result.verdict,
    }
    print(fmt_latency("Avg shadow eval (1K events)", results["shadow_eval"]["avg_ms"]))
    print(f"  {'Last verdict':<35} {results['shadow_eval']['last_verdict']}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 7. FULL PIPELINE THROUGHPUT
# ═══════════════════════════════════════════════════════════════════════════════

def bench_full_pipeline(temporal, baseline, attacker):
    section("7. FULL PIPELINE — END-TO-END THROUGHPUT")
    from aionos.core.temporal_engine import SecurityEvent, EventType

    event_types = list(EventType)
    iterations = 50_000
    results = {}

    subsection(f"Full pipeline ({iterations:,} events through all engines)")
    gc.disable()
    pipeline_latencies = []
    total_alerts = 0
    total_deviations = 0

    start_wall = time.perf_counter()
    for i in range(iterations):
        user = f"pipeline_user_{i % CONCURRENT_USERS}@lawfirm.com"
        etype = random.choice(event_types)
        ts = datetime.utcnow() - timedelta(seconds=random.randint(0, 3600))
        details = {"file_count": random.randint(1, 50), "location": "NYC"}

        t0 = time.perf_counter()

        # Step 1: Create SecurityEvent
        event = SecurityEvent(
            event_id=f"pipe_{i}",
            user_id=user,
            event_type=etype,
            timestamp=ts,
            source_system="pipeline_bench",
            details=details,
        )

        # Step 2: Temporal correlation
        alerts = temporal.ingest_event(event)
        total_alerts += len(alerts)

        # Step 3: Behavioral baseline
        devs = baseline.record_event(
            user_id=user,
            event_type=etype.value,
            timestamp=ts,
            details=details,
        )
        if devs:
            total_deviations += len(devs)

        # Step 4: Adversarial assessment (only on alerts)
        if alerts:
            attacker.analyze(
                attack_type="insider_threat",
                target="file_server",
                context={"user": user, "events": len(alerts)},
            )

        pipeline_latencies.append((time.perf_counter() - t0) * 1_000_000)

    wall_time = time.perf_counter() - start_wall
    gc.enable()

    pipeline_latencies.sort()
    results["full_pipeline"] = {
        "events": iterations,
        "wall_time_s": wall_time,
        "throughput": iterations / wall_time,
        "avg_us": statistics.mean(pipeline_latencies),
        "p50_us": percentile(pipeline_latencies, 50),
        "p95_us": percentile(pipeline_latencies, 95),
        "p99_us": percentile(pipeline_latencies, 99),
        "max_us": max(pipeline_latencies),
        "alerts": total_alerts,
        "deviations": total_deviations,
    }

    r = results["full_pipeline"]
    print(fmt_rate("Throughput", r["throughput"]))
    print(fmt_latency("Avg latency", r["avg_us"], "us"))
    print(fmt_latency("P50 latency", r["p50_us"], "us"))
    print(fmt_latency("P95 latency", r["p95_us"], "us"))
    print(fmt_latency("P99 latency", r["p99_us"], "us"))
    print(fmt_latency("Max latency", r["max_us"], "us"))
    print(f"  {'Alerts generated':<35} {r['alerts']:>10,}")
    print(f"  {'Deviations detected':<35} {r['deviations']:>10,}")
    print(f"  {'Wall time':<35} {r['wall_time_s']:>10.2f} s")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 8. MEMORY STRESS TEST
# ═══════════════════════════════════════════════════════════════════════════════

def bench_memory():
    section("8. MEMORY STRESS TEST")
    from aionos.core.temporal_engine import TemporalCorrelationEngine, SecurityEvent, EventType

    results = {}
    event_types = list(EventType)

    mem_before = get_memory_mb()
    print(f"  {'RSS before':<35} {mem_before:>10.1f} MB")

    engine = TemporalCorrelationEngine(fast_mode=True)

    # Flood with events from many unique users
    subsection(f"Flooding {MEMORY_PRESSURE_EVENTS:,} events / {CONCURRENT_USERS:,} users")
    flood_start = time.perf_counter()

    for i in range(MEMORY_PRESSURE_EVENTS):
        event = SecurityEvent(
            event_id=f"mem_{i}",
            user_id=f"memuser_{i % CONCURRENT_USERS}",
            event_type=random.choice(event_types),
            timestamp=datetime.utcnow(),
            source_system="memory_bench",
            details={"data": "x" * 50},
        )
        engine.ingest_event(event)

    flood_wall = time.perf_counter() - flood_start
    mem_after = get_memory_mb()

    results["memory"] = {
        "rss_before_mb": mem_before,
        "rss_after_mb": mem_after,
        "rss_delta_mb": mem_after - mem_before,
        "events_ingested": MEMORY_PRESSURE_EVENTS,
        "throughput": MEMORY_PRESSURE_EVENTS / flood_wall,
        "wall_time_s": flood_wall,
        "mb_per_100k_events": ((mem_after - mem_before) / MEMORY_PRESSURE_EVENTS) * 100_000 if mem_after > mem_before else 0,
    }
    r = results["memory"]
    print(f"  {'RSS after':<35} {r['rss_after_mb']:>10.1f} MB")
    print(f"  {'Delta':<35} {r['rss_delta_mb']:>10.1f} MB")
    if r["mb_per_100k_events"] > 0:
        print(f"  {'MB per 100K events':<35} {r['mb_per_100k_events']:>10.1f} MB")
    print(fmt_rate("Throughput under pressure", r["throughput"]))

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# FINAL REPORT
# ═══════════════════════════════════════════════════════════════════════════════

def final_report(all_results):
    section("FINAL REPORT")

    targets = {
        "Per-event latency (P95)": {
            "value_us": all_results.get("temporal", {}).get("sustained", {}).get("p95_us", 0),
            "target_us": 500,
            "unit": "us",
        },
        "Per-event latency (P99)": {
            "value_us": all_results.get("temporal", {}).get("sustained", {}).get("p99_us", 0),
            "target_us": 1000,
            "unit": "us",
        },
        "Sustained throughput": {
            "value": all_results.get("temporal", {}).get("sustained", {}).get("throughput", 0),
            "target": 10000,
            "unit": "events/sec",
            "higher_better": True,
        },
        "Burst throughput": {
            "value": all_results.get("temporal", {}).get("burst", {}).get("throughput", 0),
            "target": 5000,
            "unit": "events/sec",
            "higher_better": True,
        },
        "Full pipeline throughput": {
            "value": all_results.get("pipeline", {}).get("full_pipeline", {}).get("throughput", 0),
            "target": 5000,
            "unit": "events/sec",
            "higher_better": True,
        },
        "Policy create (avg)": {
            "value_ms": all_results.get("improvement", {}).get("policy_create", {}).get("avg_ms", 0),
            "target_ms": 50,
            "unit": "ms",
        },
        "Improvement cycle (avg)": {
            "value_ms": all_results.get("improvement", {}).get("improvement_cycle", {}).get("avg_ms", 0),
            "target_ms": 500,
            "unit": "ms",
        },
        "Guardrail check (avg)": {
            "value_us": all_results.get("shadow", {}).get("guardrails", {}).get("avg_us", 0),
            "target_us": 100,
            "unit": "us",
        },
        "Feedback ingestion": {
            "value": all_results.get("improvement", {}).get("feedback_ingestion", {}).get("throughput", 0),
            "target": 500,
            "unit": "fb/sec",
            "higher_better": True,
        },
        "Typhoon attack detected": {
            "value": 1 if all_results.get("temporal", {}).get("detection_accuracy", {}).get("typhoon_detected", False) else 0,
            "target": 1,
            "unit": "bool",
            "higher_better": True,
        },
    }

    passed = 0
    failed = 0

    print()
    for name, t in targets.items():
        if "value_us" in t:
            val = t["value_us"]
            tgt = t["target_us"]
            ok = val <= tgt
            val_str = f"{val:,.0f} us"
            tgt_str = f"<= {tgt:,} us"
        elif "value_ms" in t:
            val = t["value_ms"]
            tgt = t["target_ms"]
            ok = val <= tgt
            val_str = f"{val:,.1f} ms"
            tgt_str = f"<= {tgt:,} ms"
        else:
            val = t["value"]
            tgt = t["target"]
            ok = val >= tgt if t.get("higher_better") else val <= tgt
            val_str = f"{val:,.0f} {t['unit']}"
            tgt_str = f">= {tgt:,} {t['unit']}" if t.get("higher_better") else f"<= {tgt:,} {t['unit']}"

        status = "PASS" if ok else "FAIL"
        icon = chr(9989) if ok else chr(10060)

        if ok:
            passed += 1
        else:
            failed += 1

        print(f"  {icon} {name:<35} {val_str:>20}   target: {tgt_str}")

    total = passed + failed
    pct = (passed / total * 100) if total > 0 else 0

    print(f"\n  {'=' * 66}")
    print(f"  SCORE: {passed}/{total} targets met ({pct:.0f}%)")

    if pct == 100:
        print(f"  STATUS: ALL TARGETS MET — PRODUCTION READY")
    elif pct >= 80:
        print(f"  STATUS: MOSTLY READY — {failed} target(s) need optimization")
    else:
        print(f"  STATUS: OPTIMIZATION NEEDED — {failed} target(s) failing")

    mem = all_results.get("memory", {}).get("memory", {})
    if mem:
        print(f"\n  Memory: {mem.get('rss_before_mb', 0):.0f} MB -> {mem.get('rss_after_mb', 0):.0f} MB "
              f"(+{mem.get('rss_delta_mb', 0):.0f} MB for {MEMORY_PRESSURE_EVENTS:,} events)")

    print(f"  {'=' * 66}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print(chr(9552) * 72)
    print(f"  AION OS — AGGRESSIVE BENCHMARK")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Events: {STRESS_EVENTS:,} sustained + {BURST_EVENTS:,} burst + {MEMORY_PRESSURE_EVENTS:,} memory")
    print(f"  Users: {CONCURRENT_USERS:,} concurrent")
    print(f"  Policies: {POLICY_ITERATIONS} iterations")
    print(f"  Improvement cycles: {IMPROVEMENT_CYCLES}")
    print(chr(9552) * 72)

    all_results = {}

    try:
        all_results["imports"] = bench_imports()
        init_results, temporal, baseline, attacker, improvement = bench_init()
        all_results["init"] = init_results
        all_results["temporal"] = bench_temporal(temporal)
        all_results["baseline"] = bench_baseline(baseline)
        all_results["improvement"] = bench_improvement(improvement)
        all_results["shadow"] = bench_shadow()
        all_results["pipeline"] = bench_full_pipeline(temporal, baseline, attacker)
        all_results["memory"] = bench_memory()
    except Exception as e:
        print(f"\n  ERROR: {e}")
        traceback.print_exc()

    final_report(all_results)

    # Save raw results
    results_path = Path("logs/benchmark_aggressive_results.json")
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n  Raw results saved to: {results_path}")

    print(f"\n  Benchmark completed at {datetime.now().strftime('%H:%M:%S')}")
    print(chr(9552) * 72)


if __name__ == "__main__":
    main()
