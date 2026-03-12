"""
Profile Document Intelligence Engine to find latency bottlenecks
"""

import sys
import time
import cProfile
import pstats
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from aionos.modules.document_intelligence import DocumentIntelligenceEngine, DocumentType
from aionos.knowledge import get_contract_template


def profile_analysis():
    """Profile a single analysis run"""
    contract = get_contract_template("wrecking_zone_records_agreement")
    contract_text = contract.get("text", "")
    
    engine = DocumentIntelligenceEngine()
    
    # Warmup
    _ = engine.analyze_document(contract_text[:500], DocumentType.RECORDING_AGREEMENT)
    
    # Profile
    profiler = cProfile.Profile()
    profiler.enable()
    
    for _ in range(10):
        result = engine.analyze_document(contract_text, DocumentType.RECORDING_AGREEMENT)
    
    profiler.disable()
    
    print("=" * 70)
    print("  DOCUMENT INTELLIGENCE PROFILING")
    print("=" * 70)
    
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    print("\nTop 20 by cumulative time:")
    stats.print_stats(20)
    
    print("\nTop 20 by total time:")
    stats.sort_stats('tottime')
    stats.print_stats(20)


def measure_components():
    """Measure each component separately"""
    contract = get_contract_template("wrecking_zone_records_agreement")
    contract_text = contract.get("text", "")
    
    engine = DocumentIntelligenceEngine()
    
    print("\n" + "=" * 70)
    print("  COMPONENT BREAKDOWN (10 runs avg)")
    print("=" * 70)
    
    # Import internals for testing
    from aionos.modules.document_intelligence import CLAUSE_PATTERNS
    
    times = {
        'extract_parties': [],
        'extract_clauses': [],
        'calculate_risk': [],
        'identify_red_flags': [],
        'map_obligations': [],
        'generate_recommendations': [],
        'total': []
    }
    
    for _ in range(10):
        total_start = time.perf_counter()
        
        # Extract parties
        start = time.perf_counter()
        parties = engine._extract_parties(contract_text)
        times['extract_parties'].append((time.perf_counter() - start) * 1000)
        
        # Extract clauses
        start = time.perf_counter()
        clauses = engine._extract_clauses(contract_text, parties)
        times['extract_clauses'].append((time.perf_counter() - start) * 1000)
        
        # Calculate risk
        start = time.perf_counter()
        risk_level, risk_score = engine._calculate_risk(clauses)
        times['calculate_risk'].append((time.perf_counter() - start) * 1000)
        
        # Identify red flags
        start = time.perf_counter()
        red_flags = engine._identify_red_flags(clauses)
        times['identify_red_flags'].append((time.perf_counter() - start) * 1000)
        
        # Map obligations
        start = time.perf_counter()
        obligations = engine._map_obligations(clauses, parties)
        times['map_obligations'].append((time.perf_counter() - start) * 1000)
        
        # Generate recommendations
        start = time.perf_counter()
        recommendations = engine._generate_recommendations(clauses, red_flags)
        times['generate_recommendations'].append((time.perf_counter() - start) * 1000)
        
        times['total'].append((time.perf_counter() - total_start) * 1000)
    
    # Print results
    print(f"\n  {'Component':<30} {'Avg (ms)':>10} {'% of Total':>12}")
    print(f"  {'-' * 30} {'-' * 10} {'-' * 12}")
    
    total_avg = sum(times['total']) / len(times['total'])
    
    for component, values in times.items():
        if component != 'total':
            avg = sum(values) / len(values)
            pct = (avg / total_avg) * 100
            bar = '#' * int(pct / 2)
            print(f"  {component:<30} {avg:>10.2f} {pct:>10.1f}%  {bar}")
    
    print(f"  {'-' * 30} {'-' * 10}")
    print(f"  {'TOTAL':<30} {total_avg:>10.2f}")
    
    return times


if __name__ == "__main__":
    measure_components()
    print("\n")
    profile_analysis()
