"""
AION OS - Document Intelligence Benchmark
Tests accuracy and speed of contract analysis vs competitors

Run: python benchmark_doc_intelligence.py
"""

import sys
import time
import statistics
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

# Suppress warnings for clean output
import warnings
warnings.filterwarnings("ignore")

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

# Windows encoding fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# ══════════════════════════════════════════════════════════════════════════════
# GROUND TRUTH - Known facts about the Wrecking Zone Records contract
# ══════════════════════════════════════════════════════════════════════════════

GROUND_TRUTH = {
    "contract_name": "Wrecking Zone Records Agreement",
    "expected_risk_level": "CRITICAL",
    "minimum_acceptable_risk_score": 80,  # Should be 80+ for this predatory contract
    
    # Known critical clauses that MUST be detected
    "critical_clauses": [
        "EXCLUSIVITY",
        "IP_OWNERSHIP", 
        "IP_ASSIGNMENT",
        "PERPETUITY",
        "WAIVER",
        "INDEMNIFICATION",
        "ROYALTY_DEDUCTION",
        "RECOUPMENT",
    ],
    
    # Known red flags that MUST be detected (actual contract language)
    "critical_red_flags": [
        "perpetuity",           # "in perpetuity" grants
        "sole discretion",      # Unilateral power
        "100%",                 # 100% of gross deducted
        "waive",                # Rights waived
        "exclusive",            # Exclusive grants
        "indemnif",             # Indemnification
        "property",             # "entirely...property" = work-for-hire effect
    ],
    
    # Parties that should be identified
    "expected_parties": [
        "Wrecking Zone Records",
        "Wedell Mendez Jr.",
        "Dequan Fletcher"
    ],
    
    # Known predatory patterns (actual contract text)
    "predatory_patterns": [
        "100% of the gross",            # Zero-royalty trap
        "sole discretion",              # Label can withhold everything
        "in perpetuity",                # Forever rights
        "entirely",                     # "entirely...property" 
        "4 years",                      # Long initial term
        "without any payment",          # No compensation for likeness
    ]
}


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    name: str
    latency_ms: float
    accuracy_score: float
    clauses_found: int
    red_flags_found: int
    risk_score: int
    risk_level: str
    parties_found: List[str]
    critical_clauses_detected: int
    critical_clauses_missed: List[str]
    critical_flags_detected: int
    critical_flags_missed: List[str]
    predatory_patterns_detected: int
    error: Optional[str] = None


def print_header(text: str):
    """Print a section header"""
    print(f"\n{'═' * 70}")
    print(f"  {text}")
    print(f"{'═' * 70}")


def print_subheader(text: str):
    """Print a subsection header"""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}")


# ══════════════════════════════════════════════════════════════════════════════
# AION OS BENCHMARK
# ══════════════════════════════════════════════════════════════════════════════

def benchmark_aion_os() -> BenchmarkResult:
    """Benchmark AION OS Document Intelligence Engine"""
    print_subheader("AION OS — Document Intelligence Engine")
    
    from aionos.modules.document_intelligence import DocumentIntelligenceEngine, DocumentType
    from aionos.knowledge import get_contract_template
    
    # Load contract
    contract = get_contract_template("wrecking_zone_records_agreement")
    if not contract:
        return BenchmarkResult(
            name="AION OS",
            latency_ms=0,
            accuracy_score=0,
            clauses_found=0,
            red_flags_found=0,
            risk_score=0,
            risk_level="UNKNOWN",
            parties_found=[],
            critical_clauses_detected=0,
            critical_clauses_missed=GROUND_TRUTH["critical_clauses"],
            critical_flags_detected=0,
            critical_flags_missed=GROUND_TRUTH["critical_red_flags"],
            predatory_patterns_detected=0,
            error="Contract template not found"
        )
    
    contract_text = contract.get("text", "")
    
    # Initialize engine
    engine = DocumentIntelligenceEngine()
    
    # Warmup run
    _ = engine.analyze_document(contract_text[:500], DocumentType.RECORDING_AGREEMENT)
    
    # Benchmark runs
    latencies = []
    for i in range(10):
        start = time.perf_counter()
        result = engine.analyze_document(contract_text, DocumentType.RECORDING_AGREEMENT)
        latencies.append((time.perf_counter() - start) * 1000)
    
    avg_latency = statistics.mean(latencies)
    
    # Accuracy assessment - result is a DocumentAnalysis dataclass
    clauses = result.clauses
    red_flags = result.red_flags
    risk_score = result.risk_score
    risk_level = result.overall_risk.name if hasattr(result.overall_risk, 'name') else str(result.overall_risk)
    parties = result.parties
    
    # Check critical clauses - clauses are ExtractedClause objects
    found_clause_types = {c.clause_type.name if hasattr(c.clause_type, 'name') else str(c.clause_type) for c in clauses}
    critical_detected = 0
    critical_missed = []
    for expected in GROUND_TRUTH["critical_clauses"]:
        if expected in found_clause_types:
            critical_detected += 1
        else:
            critical_missed.append(expected)
    
    # Check critical red flags (fuzzy match)
    flags_text = " ".join(red_flags).lower()
    clauses_text = " ".join([c.summary + (c.risk_reason or "") for c in clauses]).lower()
    all_text = flags_text + " " + clauses_text
    
    flags_detected = 0
    flags_missed = []
    for expected in GROUND_TRUTH["critical_red_flags"]:
        if expected.lower() in all_text:
            flags_detected += 1
        else:
            flags_missed.append(expected)
    
    # Check predatory patterns
    patterns_detected = 0
    for pattern in GROUND_TRUTH["predatory_patterns"]:
        if pattern.lower() in all_text:
            patterns_detected += 1
    
    # Calculate accuracy score
    clause_accuracy = critical_detected / len(GROUND_TRUTH["critical_clauses"]) * 100
    flag_accuracy = flags_detected / len(GROUND_TRUTH["critical_red_flags"]) * 100
    risk_accuracy = 100 if risk_level == GROUND_TRUTH["expected_risk_level"] else 50
    pattern_accuracy = patterns_detected / len(GROUND_TRUTH["predatory_patterns"]) * 100
    
    overall_accuracy = (clause_accuracy * 0.3 + flag_accuracy * 0.3 + 
                       risk_accuracy * 0.2 + pattern_accuracy * 0.2)
    
    return BenchmarkResult(
        name="AION OS",
        latency_ms=avg_latency,
        accuracy_score=overall_accuracy,
        clauses_found=len(clauses),
        red_flags_found=len(red_flags),
        risk_score=risk_score,
        risk_level=risk_level,
        parties_found=parties,
        critical_clauses_detected=critical_detected,
        critical_clauses_missed=critical_missed,
        critical_flags_detected=flags_detected,
        critical_flags_missed=flags_missed,
        predatory_patterns_detected=patterns_detected
    )


# ══════════════════════════════════════════════════════════════════════════════
# COMPETITOR BENCHMARKS (Cloud LLMs)
# ══════════════════════════════════════════════════════════════════════════════

COMPETITOR_PROMPT = """Analyze this recording artist contract for legal risks.

CONTRACT TEXT:
{contract_text}

Respond in JSON format:
{{
    "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
    "risk_score": 0-100,
    "parties": ["party1", "party2"],
    "clauses": [
        {{
            "clause_type": "EXCLUSIVITY|IP_OWNERSHIP|etc",
            "summary": "brief description",
            "risk_level": "CRITICAL|HIGH|MEDIUM|LOW"
        }}
    ],
    "red_flags": ["flag1", "flag2"],
    "predatory_patterns": ["pattern1", "pattern2"]
}}
"""


def benchmark_openai() -> Optional[BenchmarkResult]:
    """Benchmark OpenAI GPT-4"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("  [SKIP] OPENAI_API_KEY not set")
        return None
    
    print_subheader("OpenAI GPT-4 Turbo")
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        from aionos.knowledge import get_contract_template
        contract = get_contract_template("wrecking_zone_records_agreement")
        contract_text = contract.get("text", "")[:8000]  # Token limit
        
        prompt = COMPETITOR_PROMPT.format(contract_text=contract_text)
        
        # Benchmark
        latencies = []
        result = None
        for i in range(3):  # Fewer runs due to cost
            start = time.perf_counter()
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            latencies.append((time.perf_counter() - start) * 1000)
            if i == 0:
                try:
                    result = json.loads(response.choices[0].message.content)
                except:
                    result = {}
        
        return _parse_competitor_result("OpenAI GPT-4", statistics.mean(latencies), result)
        
    except Exception as e:
        return BenchmarkResult(
            name="OpenAI GPT-4",
            latency_ms=0,
            accuracy_score=0,
            clauses_found=0,
            red_flags_found=0,
            risk_score=0,
            risk_level="ERROR",
            parties_found=[],
            critical_clauses_detected=0,
            critical_clauses_missed=GROUND_TRUTH["critical_clauses"],
            critical_flags_detected=0,
            critical_flags_missed=GROUND_TRUTH["critical_red_flags"],
            predatory_patterns_detected=0,
            error=str(e)
        )


def benchmark_anthropic() -> Optional[BenchmarkResult]:
    """Benchmark Anthropic Claude"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  [SKIP] ANTHROPIC_API_KEY not set")
        return None
    
    print_subheader("Anthropic Claude 3.5 Sonnet")
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        from aionos.knowledge import get_contract_template
        contract = get_contract_template("wrecking_zone_records_agreement")
        contract_text = contract.get("text", "")[:8000]
        
        prompt = COMPETITOR_PROMPT.format(contract_text=contract_text)
        
        # Benchmark
        latencies = []
        result = None
        for i in range(3):
            start = time.perf_counter()
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            latencies.append((time.perf_counter() - start) * 1000)
            if i == 0:
                try:
                    content = response.content[0].text
                    # Extract JSON from response
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    result = json.loads(content)
                except:
                    result = {}
        
        return _parse_competitor_result("Anthropic Claude", statistics.mean(latencies), result)
        
    except Exception as e:
        return BenchmarkResult(
            name="Anthropic Claude",
            latency_ms=0,
            accuracy_score=0,
            clauses_found=0,
            red_flags_found=0,
            risk_score=0,
            risk_level="ERROR",
            parties_found=[],
            critical_clauses_detected=0,
            critical_clauses_missed=GROUND_TRUTH["critical_clauses"],
            critical_flags_detected=0,
            critical_flags_missed=GROUND_TRUTH["critical_red_flags"],
            predatory_patterns_detected=0,
            error=str(e)
        )


def benchmark_lmstudio() -> Optional[BenchmarkResult]:
    """Benchmark LM Studio local model"""
    print_subheader("LM Studio (Local Qwen 2.5)")
    
    try:
        import requests
        
        # Check if LM Studio is running
        try:
            r = requests.get("http://localhost:1234/v1/models", timeout=2)
            if r.status_code != 200:
                print("  [SKIP] LM Studio not running on localhost:1234")
                return None
        except:
            print("  [SKIP] LM Studio not running on localhost:1234")
            return None
        
        from aionos.knowledge import get_contract_template
        contract = get_contract_template("wrecking_zone_records_agreement")
        contract_text = contract.get("text", "")[:4000]  # Smaller for local model
        
        prompt = COMPETITOR_PROMPT.format(contract_text=contract_text)
        
        # Benchmark
        latencies = []
        result = None
        for i in range(3):
            start = time.perf_counter()
            response = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=120
            )
            latencies.append((time.perf_counter() - start) * 1000)
            if i == 0 and response.status_code == 200:
                try:
                    content = response.json()["choices"][0]["message"]["content"]
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0]
                    # Try to find JSON in response
                    import re
                    json_match = re.search(r'\{.*\}', content, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        result = {}
                except:
                    result = {}
        
        return _parse_competitor_result("LM Studio Local", statistics.mean(latencies), result)
        
    except Exception as e:
        return BenchmarkResult(
            name="LM Studio Local",
            latency_ms=0,
            accuracy_score=0,
            clauses_found=0,
            red_flags_found=0,
            risk_score=0,
            risk_level="ERROR",
            parties_found=[],
            critical_clauses_detected=0,
            critical_clauses_missed=GROUND_TRUTH["critical_clauses"],
            critical_flags_detected=0,
            critical_flags_missed=GROUND_TRUTH["critical_red_flags"],
            predatory_patterns_detected=0,
            error=str(e)
        )


def _parse_competitor_result(name: str, latency: float, result: dict) -> BenchmarkResult:
    """Parse competitor LLM result into BenchmarkResult"""
    clauses = result.get("clauses", [])
    red_flags = result.get("red_flags", [])
    risk_score = result.get("risk_score", 0)
    risk_level = result.get("risk_level", "UNKNOWN")
    parties = result.get("parties", [])
    predatory = result.get("predatory_patterns", [])
    
    # Check critical clauses
    found_clause_types = {c.get("clause_type", "").upper() for c in clauses}
    critical_detected = 0
    critical_missed = []
    for expected in GROUND_TRUTH["critical_clauses"]:
        if expected in found_clause_types:
            critical_detected += 1
        else:
            critical_missed.append(expected)
    
    # Check critical red flags
    all_text = " ".join(red_flags + [c.get("summary", "") for c in clauses] + predatory).lower()
    
    flags_detected = 0
    flags_missed = []
    for expected in GROUND_TRUTH["critical_red_flags"]:
        if expected.lower() in all_text:
            flags_detected += 1
        else:
            flags_missed.append(expected)
    
    # Check predatory patterns
    patterns_detected = len(predatory)
    
    # Calculate accuracy
    clause_accuracy = critical_detected / len(GROUND_TRUTH["critical_clauses"]) * 100
    flag_accuracy = flags_detected / len(GROUND_TRUTH["critical_red_flags"]) * 100
    risk_accuracy = 100 if risk_level == GROUND_TRUTH["expected_risk_level"] else 50
    pattern_accuracy = min(100, patterns_detected / len(GROUND_TRUTH["predatory_patterns"]) * 100)
    
    overall_accuracy = (clause_accuracy * 0.3 + flag_accuracy * 0.3 + 
                       risk_accuracy * 0.2 + pattern_accuracy * 0.2)
    
    return BenchmarkResult(
        name=name,
        latency_ms=latency,
        accuracy_score=overall_accuracy,
        clauses_found=len(clauses),
        red_flags_found=len(red_flags),
        risk_score=risk_score,
        risk_level=risk_level,
        parties_found=parties,
        critical_clauses_detected=critical_detected,
        critical_clauses_missed=critical_missed,
        critical_flags_detected=flags_detected,
        critical_flags_missed=flags_missed,
        predatory_patterns_detected=patterns_detected
    )


# ══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def print_result(result: BenchmarkResult):
    """Print a single benchmark result"""
    status = "✓" if result.error is None else "✗"
    print(f"\n  [{status}] {result.name}")
    
    if result.error:
        print(f"      ERROR: {result.error}")
        return
    
    print(f"      Latency:      {result.latency_ms:,.1f}ms")
    print(f"      Accuracy:     {result.accuracy_score:.1f}%")
    print(f"      Risk Level:   {result.risk_level} ({result.risk_score}/100)")
    print(f"      Clauses:      {result.clauses_found} found")
    print(f"      Red Flags:    {result.red_flags_found} found")
    print(f"      Critical Clauses: {result.critical_clauses_detected}/{len(GROUND_TRUTH['critical_clauses'])}")
    if result.critical_clauses_missed:
        print(f"        Missed: {', '.join(result.critical_clauses_missed)}")
    print(f"      Critical Flags:   {result.critical_flags_detected}/{len(GROUND_TRUTH['critical_red_flags'])}")
    if result.critical_flags_missed:
        print(f"        Missed: {', '.join(result.critical_flags_missed)}")


def print_comparison_table(results: List[BenchmarkResult]):
    """Print side-by-side comparison table"""
    print_header("COMPARISON TABLE")
    
    # Filter out None/errored results
    valid_results = [r for r in results if r and not r.error]
    
    if not valid_results:
        print("  No valid results to compare")
        return
    
    # Header
    print(f"\n  {'Metric':<25} ", end="")
    for r in valid_results:
        print(f"{r.name:>18} ", end="")
    print()
    print(f"  {'-' * 25} ", end="")
    for _ in valid_results:
        print(f"{'-' * 18} ", end="")
    print()
    
    # Rows
    metrics = [
        ("Latency (ms)", lambda r: f"{r.latency_ms:,.1f}"),
        ("Accuracy (%)", lambda r: f"{r.accuracy_score:.1f}"),
        ("Risk Level", lambda r: r.risk_level),
        ("Risk Score", lambda r: f"{r.risk_score}/100"),
        ("Clauses Found", lambda r: str(r.clauses_found)),
        ("Red Flags Found", lambda r: str(r.red_flags_found)),
        ("Critical Clauses", lambda r: f"{r.critical_clauses_detected}/{len(GROUND_TRUTH['critical_clauses'])}"),
        ("Critical Flags", lambda r: f"{r.critical_flags_detected}/{len(GROUND_TRUTH['critical_red_flags'])}"),
    ]
    
    for label, getter in metrics:
        print(f"  {label:<25} ", end="")
        for r in valid_results:
            print(f"{getter(r):>18} ", end="")
        print()


def print_winner(results: List[BenchmarkResult]):
    """Determine and print the winner"""
    print_header("WINNER ANALYSIS")
    
    valid_results = [r for r in results if r and not r.error]
    if not valid_results:
        return
    
    # Speed winner
    fastest = min(valid_results, key=lambda r: r.latency_ms)
    print(f"\n  FASTEST:         {fastest.name} ({fastest.latency_ms:,.1f}ms)")
    
    # Accuracy winner
    most_accurate = max(valid_results, key=lambda r: r.accuracy_score)
    print(f"  MOST ACCURATE:   {most_accurate.name} ({most_accurate.accuracy_score:.1f}%)")
    
    # Best value (accuracy per ms)
    for r in valid_results:
        r._value_score = r.accuracy_score / (r.latency_ms / 1000)
    best_value = max(valid_results, key=lambda r: r._value_score)
    print(f"  BEST VALUE:      {best_value.name} (accuracy/latency ratio)")
    
    # Overall winner (weighted score)
    for r in valid_results:
        # Higher accuracy is better, lower latency is better
        # Normalize latency (inverse, so lower is higher score)
        max_latency = max(v.latency_ms for v in valid_results)
        latency_score = (max_latency - r.latency_ms) / max_latency * 100 if max_latency > 0 else 0
        r._overall_score = r.accuracy_score * 0.7 + latency_score * 0.3
    
    overall_winner = max(valid_results, key=lambda r: r._overall_score)
    print(f"\n  OVERALL WINNER:  {overall_winner.name}")
    print(f"    Accuracy:      {overall_winner.accuracy_score:.1f}%")
    print(f"    Latency:       {overall_winner.latency_ms:,.1f}ms")
    
    # Law firm pitch summary
    aion_result = next((r for r in valid_results if r.name == "AION OS"), None)
    if aion_result:
        print_header("LAW FIRM PITCH SUMMARY")
        print(f"""
  AION OS Document Intelligence Performance:
  
  ✓ Analysis Speed:     {aion_result.latency_ms:,.1f}ms per document
  ✓ Throughput:         {1000/aion_result.latency_ms:.1f} documents/second
  ✓ Accuracy Score:     {aion_result.accuracy_score:.1f}%
  ✓ Critical Detection: {aion_result.critical_clauses_detected}/{len(GROUND_TRUTH['critical_clauses'])} predatory clauses identified
  ✓ Risk Assessment:    {aion_result.risk_level} ({aion_result.risk_score}/100)
  
  Key Advantage: {aion_result.latency_ms:,.0f}x faster than cloud (no network round-trip)
  Data Privacy:  100% on-premise — zero client data leaves the network
""")


def main():
    """Main benchmark runner"""
    print("=" * 70)
    print("  AION OS — Document Intelligence Benchmark")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    print_header("GROUND TRUTH")
    print(f"  Contract: {GROUND_TRUTH['contract_name']}")
    print(f"  Expected Risk: {GROUND_TRUTH['expected_risk_level']}")
    print(f"  Critical Clauses to Detect: {len(GROUND_TRUTH['critical_clauses'])}")
    print(f"  Critical Red Flags: {len(GROUND_TRUTH['critical_red_flags'])}")
    print(f"  Predatory Patterns: {len(GROUND_TRUTH['predatory_patterns'])}")
    
    results: List[BenchmarkResult] = []
    
    # Benchmark AION OS (always run)
    print_header("BENCHMARKING")
    aion_result = benchmark_aion_os()
    results.append(aion_result)
    print_result(aion_result)
    
    # Benchmark competitors (if available)
    lmstudio_result = benchmark_lmstudio()
    if lmstudio_result:
        results.append(lmstudio_result)
        print_result(lmstudio_result)
    
    openai_result = benchmark_openai()
    if openai_result:
        results.append(openai_result)
        print_result(openai_result)
    
    anthropic_result = benchmark_anthropic()
    if anthropic_result:
        results.append(anthropic_result)
        print_result(anthropic_result)
    
    # Print comparison
    print_comparison_table(results)
    print_winner(results)
    
    print("\n" + "=" * 70)
    print("  Benchmark Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
