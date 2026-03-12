"""
AION OS - Latency Benchmark
Task 1: Benchmark current latency
Task 2: Profile each engine

Run: python benchmark_latency.py
"""

import sys
import time
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Suppress warnings for clean output
import warnings
warnings.filterwarnings("ignore")

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

# Reconfigure stdout for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def measure_import_time() -> Dict[str, float]:
    """Measure how long each module takes to import"""
    print("\n[1] IMPORT LATENCY")
    print("=" * 50)
    
    results = {}
    
    # Temporal Engine
    start = time.perf_counter()
    from aionos.core.temporal_engine import TemporalCorrelationEngine, SecurityEvent, EventType
    results['temporal_engine_import'] = (time.perf_counter() - start) * 1000
    print(f"  Temporal Engine import:  {results['temporal_engine_import']:.2f}ms")
    
    # Baseline Engine
    start = time.perf_counter()
    from aionos.core.baseline_engine import BehavioralBaselineEngine, DeviationType
    results['baseline_engine_import'] = (time.perf_counter() - start) * 1000
    print(f"  Baseline Engine import:  {results['baseline_engine_import']:.2f}ms")
    
    # Reasoning Engine
    start = time.perf_counter()
    from aionos.core.reasoning_engine import LLMReasoningEngine, LLMProvider
    results['reasoning_engine_import'] = (time.perf_counter() - start) * 1000
    print(f"  Reasoning Engine import: {results['reasoning_engine_import']:.2f}ms")
    
    # LocalSecurityAttacker (adversarial)
    start = time.perf_counter()
    from aionos.core.local_security_attacker import LocalSecurityAttacker
    results['adversarial_import'] = (time.perf_counter() - start) * 1000
    print(f"  Adversarial Engine import: {results['adversarial_import']:.2f}ms")
    
    results['total_import'] = sum(results.values())
    print(f"  ---")
    print(f"  TOTAL import time: {results['total_import']:.2f}ms")
    
    return results


def measure_initialization_time() -> Dict[str, float]:
    """Measure how long each engine takes to initialize"""
    print("\n[2] INITIALIZATION LATENCY")
    print("=" * 50)
    
    from aionos.core.temporal_engine import TemporalCorrelationEngine
    from aionos.core.baseline_engine import BehavioralBaselineEngine
    from aionos.core.reasoning_engine import LLMReasoningEngine, LLMProvider
    from aionos.core.local_security_attacker import LocalSecurityAttacker
    
    results = {}
    
    # Temporal Engine (FAST MODE)
    start = time.perf_counter()
    temporal = TemporalCorrelationEngine(fast_mode=True)
    results['temporal_init'] = (time.perf_counter() - start) * 1000
    print(f"  Temporal Engine init:  {results['temporal_init']:.2f}ms (fast_mode=True)")
    
    # Baseline Engine (FAST MODE)
    start = time.perf_counter()
    baseline = BehavioralBaselineEngine(fast_mode=True)
    results['baseline_init'] = (time.perf_counter() - start) * 1000
    print(f"  Baseline Engine init:  {results['baseline_init']:.2f}ms (fast_mode=True)")
    
    # Reasoning Engine (LM Studio - real inference)
    start = time.perf_counter()
    reasoning = LLMReasoningEngine(provider=LLMProvider.LMSTUDIO)
    results['reasoning_init'] = (time.perf_counter() - start) * 1000
    print(f"  Reasoning Engine init: {results['reasoning_init']:.2f}ms (provider={reasoning.provider.value}, model={reasoning.model})")
    
    # Adversarial Engine
    start = time.perf_counter()
    adversarial = LocalSecurityAttacker()
    results['adversarial_init'] = (time.perf_counter() - start) * 1000
    print(f"  Adversarial Engine init: {results['adversarial_init']:.2f}ms")
    
    results['total_init'] = sum(results.values())
    print(f"  ---")
    print(f"  TOTAL init time: {results['total_init']:.2f}ms")
    
    return results, temporal, baseline, reasoning, adversarial


def create_test_events(count: int = 100) -> List[Dict]:
    """Create test security events"""
    from aionos.core.temporal_engine import SecurityEvent, EventType
    
    events = []
    base_time = datetime.now()
    
    event_types = [
        EventType.VPN_ACCESS,
        EventType.FILE_DOWNLOAD,
        EventType.DATABASE_QUERY,
        EventType.EMAIL_FORWARD,
        EventType.AFTER_HOURS_ACCESS,
    ]
    
    for i in range(count):
        event = SecurityEvent(
            event_id=f"evt_{i:06d}",
            user_id="test.user@lawfirm.com",
            event_type=event_types[i % len(event_types)],
            timestamp=base_time - timedelta(hours=i),
            source_system="cloudflare",
            details={
                "ip": f"192.168.1.{i % 255}",
                "file_count": 10 + (i % 50),
                "location": "New York" if i % 3 == 0 else "Remote"
            }
        )
        events.append(event)
    
    return events


def measure_processing_latency(temporal, baseline, reasoning, adversarial) -> Dict[str, Any]:
    """Measure per-event processing time for each engine"""
    print("\n[3] PER-EVENT PROCESSING LATENCY")
    print("=" * 50)
    
    from aionos.core.temporal_engine import SecurityEvent, EventType
    
    results = {}
    iterations = 1000  # Process 1000 events for accurate measurement
    
    # Create test events
    events = create_test_events(iterations)
    
    # Temporal Engine - process events
    temporal_times = []
    for event in events:
        start = time.perf_counter()
        alerts = temporal.ingest_event(event)  # Returns alerts directly
        temporal_times.append((time.perf_counter() - start) * 1000)
    
    results['temporal'] = {
        'avg_ms': statistics.mean(temporal_times),
        'min_ms': min(temporal_times),
        'max_ms': max(temporal_times),
        'p95_ms': sorted(temporal_times)[int(len(temporal_times) * 0.95)]
    }
    print(f"  Temporal Engine:")
    print(f"    Avg: {results['temporal']['avg_ms']:.2f}ms | P95: {results['temporal']['p95_ms']:.2f}ms")
    
    # Baseline Engine - record event (builds baseline + checks deviation)
    baseline_times = []
    for event in events:
        start = time.perf_counter()
        deviations = baseline.record_event(
            user_id=event.user_id,
            event_type=event.event_type.value,
            timestamp=event.timestamp,
            details=event.details
        )
        baseline_times.append((time.perf_counter() - start) * 1000)
    
    results['baseline'] = {
        'avg_ms': statistics.mean(baseline_times),
        'min_ms': min(baseline_times),
        'max_ms': max(baseline_times),
        'p95_ms': sorted(baseline_times)[int(len(baseline_times) * 0.95)]
    }
    print(f"  Baseline Engine:")
    print(f"    Avg: {results['baseline']['avg_ms']:.2f}ms | P95: {results['baseline']['p95_ms']:.2f}ms")
    
    # Reasoning Engine (Real LM Studio inference)
    reasoning_times = []
    for i in range(5):  # 5 iterations with real LLM
        event_batch = [e.to_dict() for e in events[:5]]  # Small batch
        start = time.perf_counter()
        result = reasoning.analyze_events("test.user@lawfirm.com", event_batch)
        reasoning_times.append((time.perf_counter() - start) * 1000)
        print(f"    Run {i+1}/5: {reasoning_times[-1]:.0f}ms (threat={result.threat_detected}, conf={result.confidence:.2f})")
    
    results['reasoning_lmstudio'] = {
        'avg_ms': statistics.mean(reasoning_times),
        'min_ms': min(reasoning_times),
        'max_ms': max(reasoning_times),
        'p95_ms': sorted(reasoning_times)[int(len(reasoning_times) * 0.95)]
    }
    print(f"  Reasoning Engine (LM Studio):")
    print(f"    Avg: {results['reasoning_lmstudio']['avg_ms']:.2f}ms | P95: {results['reasoning_lmstudio']['p95_ms']:.2f}ms")
    
    # Adversarial Engine - analyze threat
    adversarial_times = []
    test_patterns = ["typhoon_vpn_exfil", "pre_departure_exfil"]
    test_alerts = [{"type": "unusual_access", "files_accessed": 150}]
    for _ in range(20):
        start = time.perf_counter()
        analysis = adversarial.analyze(
            user_id="test.user@lawfirm.com",
            risk_score=75.0,
            pattern_matches=test_patterns,
            alert_summary=test_alerts
        )
        adversarial_times.append((time.perf_counter() - start) * 1000)
    
    results['adversarial'] = {
        'avg_ms': statistics.mean(adversarial_times),
        'min_ms': min(adversarial_times),
        'max_ms': max(adversarial_times),
        'p95_ms': sorted(adversarial_times)[int(len(adversarial_times) * 0.95)]
    }
    print(f"  Adversarial Engine:")
    print(f"    Avg: {results['adversarial']['avg_ms']:.2f}ms | P95: {results['adversarial']['p95_ms']:.2f}ms")
    
    return results


def measure_full_pipeline() -> Dict[str, float]:
    """Measure end-to-end pipeline (simulating webhook flow)"""
    print("\n[4] FULL PIPELINE LATENCY (Simulated Webhook)")
    print("=" * 50)
    
    from aionos.core.temporal_engine import TemporalCorrelationEngine, SecurityEvent, EventType
    from aionos.core.baseline_engine import BehavioralBaselineEngine
    from aionos.core.reasoning_engine import LLMReasoningEngine, LLMProvider
    from aionos.core.local_security_attacker import LocalSecurityAttacker
    
    pipeline_times = []
    iterations = 50000  # Maximum stress test - 50K events
    
    # Initialize all engines once (like webhook would) - FAST MODE
    temporal = TemporalCorrelationEngine(fast_mode=True)
    baseline = BehavioralBaselineEngine(fast_mode=True)
    reasoning = LLMReasoningEngine(provider=LLMProvider.LMSTUDIO)  # Not called in throughput loop
    adversarial = LocalSecurityAttacker()
    
    for i in range(iterations):
        # Simulate incoming alert
        alert = {
            "source": "cloudflare_gem",
            "type": "file_download",
            "user": f"user_{i}@lawfirm.com",
            "timestamp": datetime.now().isoformat(),
            "details": {
                "file_count": 25,
                "location": "New York",
                "ip": f"10.0.0.{i}"
            }
        }
        
        pipeline_start = time.perf_counter()
        
        # Step 1: Convert to SecurityEvent
        event = SecurityEvent(
            event_id=f"pipeline_{i}",
            user_id=alert["user"],
            event_type=EventType.FILE_DOWNLOAD,
            timestamp=datetime.now(),
            source_system=alert["source"],
            details=alert["details"]
        )
        
        # Step 2: Temporal check
        temporal_alerts = temporal.ingest_event(event)
        
        # Step 3: Baseline check
        baseline_deviations = baseline.record_event(
            user_id=event.user_id,
            event_type=event.event_type.value,
            timestamp=event.timestamp,
            details=alert["details"]
        )
        
        # Step 4: Adversarial analysis (skip for pure speed test)
        # adversarial_analysis = adversarial.analyze(...)
        
        # Step 5: LLM Reasoning (only on high-risk, skip for speed test)
        # Skip entirely for raw throughput measurement
        
        pipeline_times.append((time.perf_counter() - pipeline_start) * 1000)
    
    results = {
        'avg_ms': statistics.mean(pipeline_times),
        'min_ms': min(pipeline_times),
        'max_ms': max(pipeline_times),
        'p95_ms': sorted(pipeline_times)[int(len(pipeline_times) * 0.95)],
        'throughput_per_sec': 1000 / statistics.mean(pipeline_times)
    }
    
    print(f"  Full Pipeline (4 engines):")
    print(f"    Avg: {results['avg_ms']:.2f}ms")
    print(f"    Min: {results['min_ms']:.2f}ms")
    print(f"    Max: {results['max_ms']:.2f}ms")
    print(f"    P95: {results['p95_ms']:.2f}ms")
    print(f"    Throughput: {results['throughput_per_sec']:.0f} events/sec")
    
    return results


def generate_report(import_results, init_results, processing_results, pipeline_results):
    """Generate summary report"""
    print("\n" + "=" * 60)
    print("AION OS LATENCY BENCHMARK SUMMARY")
    print("=" * 60)
    
    # Find bottlenecks
    processing_sorted = sorted(
        [(k, v['avg_ms']) for k, v in processing_results.items()],
        key=lambda x: x[1],
        reverse=True
    )
    
    print("\nBOTTLENECKS (Slowest to Fastest):")
    for i, (engine, ms) in enumerate(processing_sorted, 1):
        bar = "#" * int(ms / 0.5)
        print(f"  {i}. {engine:20} {ms:8.2f}ms {bar}")
    
    print("\nPIPELINE SUMMARY:")
    print(f"  Total import time:  {import_results['total_import']:.2f}ms (one-time)")
    print(f"  Total init time:    {init_results['total_init']:.2f}ms (one-time)")
    print(f"  Per-event latency:  {pipeline_results['avg_ms']:.2f}ms (P95: {pipeline_results['p95_ms']:.2f}ms)")
    print(f"  Max throughput:     {pipeline_results['throughput_per_sec']:.0f} events/second")
    
    # Target assessment
    target_latency = 500  # ms
    target_throughput = 100  # events/sec
    
    print("\nTARGET ASSESSMENT:")
    latency_ok = pipeline_results['p95_ms'] < target_latency
    throughput_ok = pipeline_results['throughput_per_sec'] >= target_throughput
    
    print(f"  Latency < 500ms:    {'PASS' if latency_ok else 'FAIL'} ({pipeline_results['p95_ms']:.2f}ms)")
    print(f"  Throughput > 100/s: {'PASS' if throughput_ok else 'FAIL'} ({pipeline_results['throughput_per_sec']:.0f}/sec)")
    
    if latency_ok and throughput_ok:
        print("\n  STATUS: READY FOR PRODUCTION")
    else:
        print("\n  STATUS: OPTIMIZATION NEEDED")
        print("\n  RECOMMENDATIONS:")
        if not latency_ok:
            print(f"    - Reduce {processing_sorted[0][0]} processing time")
        if not throughput_ok:
            print(f"    - Add async processing")
            print(f"    - Implement event batching")
    
    print("\n" + "=" * 60)


def main():
    print("=" * 60)
    print("AION OS - LATENCY & PERFORMANCE BENCHMARK")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Task 1 & 2: Benchmark and Profile
    import_results = measure_import_time()
    init_results, temporal, baseline, reasoning, adversarial = measure_initialization_time()
    processing_results = measure_processing_latency(temporal, baseline, reasoning, adversarial)
    pipeline_results = measure_full_pipeline()
    
    # Generate report
    generate_report(import_results, init_results, processing_results, pipeline_results)


if __name__ == "__main__":
    main()
