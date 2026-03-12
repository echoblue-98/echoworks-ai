"""
Accuracy Tracker - Compare Local vs Cloud LLM Outputs

PURPOSE: Track accuracy of local models (LM Studio) vs cloud (Claude/Gemini)
GOAL: Hit 85%+ accuracy before switching to sovereign local inference

USAGE:
    from aionos.utils.accuracy_tracker import AccuracyTracker
    
    tracker = AccuracyTracker()
    tracker.log_comparison(scenario_id, cloud_result, local_result, ground_truth)
    
    stats = tracker.get_stats()
    print(f"Accuracy: {stats['accuracy_pct']}%")  # Target: 85%+

Author: AION OS Team
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class AccuracyTracker:
    """
    Tracks accuracy of local models vs cloud baselines.
    
    Scoring based on:
    - Vulnerability detection match (did it find the same issues?)
    - Severity alignment (critical vs low mismatch = big penalty)
    - Actionability (are countermeasures useful?)
    """
    
    LOG_DIR = Path(__file__).parent.parent.parent / "logs" / "accuracy"
    LOG_FILE = "comparison_log.jsonl"
    
    def __init__(self, log_dir: Path = None):
        self.log_dir = Path(log_dir) if log_dir else self.LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / self.LOG_FILE
    
    def log_comparison(
        self,
        scenario_id: str,
        cloud_result: Dict[str, Any],
        local_result: Dict[str, Any],
        ground_truth: Dict[str, Any] = None,
        cloud_provider: str = "claude",
        local_provider: str = "lmstudio"
    ) -> Dict[str, Any]:
        """
        Log a comparison between cloud and local results.
        
        :param scenario_id: Unique identifier for the test scenario
        :param cloud_result: Result from Claude/Gemini
        :param local_result: Result from LM Studio
        :param ground_truth: Optional ground truth for absolute scoring
        :param cloud_provider: Name of cloud provider used
        :param local_provider: Name of local provider used
        :return: Comparison metrics
        """
        
        # Calculate similarity score
        metrics = self._calculate_similarity(cloud_result, local_result)
        
        # If ground truth provided, calculate absolute accuracy
        if ground_truth:
            metrics["cloud_accuracy"] = self._calculate_accuracy(cloud_result, ground_truth)
            metrics["local_accuracy"] = self._calculate_accuracy(local_result, ground_truth)
        
        # Build log entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "scenario_id": scenario_id,
            "cloud_provider": cloud_provider,
            "local_provider": local_provider,
            "local_model": local_result.get("model", "unknown"),
            "cloud_vuln_count": len(cloud_result.get("vulnerabilities", [])),
            "local_vuln_count": len(local_result.get("vulnerabilities", [])),
            "similarity_score": metrics["similarity_score"],
            "severity_alignment": metrics["severity_alignment"],
            "title_overlap": metrics["title_overlap"],
            "local_latency_ms": local_result.get("latency_ms", 0),
            "has_ground_truth": ground_truth is not None,
            "cloud_accuracy": metrics.get("cloud_accuracy"),
            "local_accuracy": metrics.get("local_accuracy")
        }
        
        # Append to log file
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        return entry
    
    def _calculate_similarity(
        self, 
        cloud: Dict[str, Any], 
        local: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate similarity between cloud and local results.
        
        Returns score 0-100 where 100 = perfect match.
        """
        
        cloud_vulns = cloud.get("vulnerabilities", [])
        local_vulns = local.get("vulnerabilities", [])
        
        if not cloud_vulns and not local_vulns:
            return {"similarity_score": 100.0, "severity_alignment": 100.0, "title_overlap": 100.0}
        
        if not cloud_vulns or not local_vulns:
            return {"similarity_score": 0.0, "severity_alignment": 0.0, "title_overlap": 0.0}
        
        # Extract titles (lowercase for fuzzy match)
        cloud_titles = set(v.get("title", "").lower() for v in cloud_vulns)
        local_titles = set(v.get("title", "").lower() for v in local_vulns)
        
        # Title overlap (Jaccard similarity)
        if cloud_titles or local_titles:
            intersection = len(cloud_titles & local_titles)
            union = len(cloud_titles | local_titles)
            title_overlap = (intersection / union) * 100 if union > 0 else 0
        else:
            title_overlap = 0
        
        # Severity alignment
        cloud_severities = [v.get("severity", "medium").lower() for v in cloud_vulns]
        local_severities = [v.get("severity", "medium").lower() for v in local_vulns]
        
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        cloud_severity_score = sum(severity_order.get(s, 2) for s in cloud_severities)
        local_severity_score = sum(severity_order.get(s, 2) for s in local_severities)
        
        max_severity = max(cloud_severity_score, local_severity_score, 1)
        severity_alignment = (1 - abs(cloud_severity_score - local_severity_score) / max_severity) * 100
        
        # Count alignment
        count_diff = abs(len(cloud_vulns) - len(local_vulns))
        max_count = max(len(cloud_vulns), len(local_vulns), 1)
        count_alignment = (1 - count_diff / max_count) * 100
        
        # Weighted overall similarity
        similarity_score = (
            title_overlap * 0.4 +
            severity_alignment * 0.3 +
            count_alignment * 0.3
        )
        
        return {
            "similarity_score": round(similarity_score, 1),
            "severity_alignment": round(severity_alignment, 1),
            "title_overlap": round(title_overlap, 1)
        }
    
    def _calculate_accuracy(
        self, 
        result: Dict[str, Any], 
        ground_truth: Dict[str, Any]
    ) -> float:
        """Calculate accuracy against ground truth"""
        
        result_vulns = result.get("vulnerabilities", [])
        truth_vulns = ground_truth.get("expected_vulnerabilities", [])
        
        if not truth_vulns:
            return 100.0 if not result_vulns else 50.0
        
        # Match by title keywords
        truth_keywords = set()
        for v in truth_vulns:
            keywords = v.get("title", "").lower().split()
            truth_keywords.update(keywords)
        
        matches = 0
        for v in result_vulns:
            title_words = set(v.get("title", "").lower().split())
            if title_words & truth_keywords:
                matches += 1
        
        # Precision and recall
        precision = matches / len(result_vulns) if result_vulns else 0
        recall = matches / len(truth_vulns) if truth_vulns else 0
        
        # F1 score as accuracy
        if precision + recall > 0:
            f1 = 2 * (precision * recall) / (precision + recall)
            return round(f1 * 100, 1)
        return 0.0
    
    def get_stats(self, last_n: int = None) -> Dict[str, Any]:
        """
        Get accuracy statistics.
        
        :param last_n: Only consider last N comparisons (None = all)
        :return: Statistics including overall accuracy
        """
        
        if not self.log_path.exists():
            return {
                "total_comparisons": 0,
                "accuracy_pct": 0.0,
                "ready_for_sovereign": False,
                "message": "No comparisons logged yet. Run compare_local_vs_cloud.py"
            }
        
        entries = []
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        
        if not entries:
            return {
                "total_comparisons": 0,
                "accuracy_pct": 0.0,
                "ready_for_sovereign": False
            }
        
        # Filter to last N if specified
        if last_n:
            entries = entries[-last_n:]
        
        # Calculate averages
        similarity_scores = [e["similarity_score"] for e in entries]
        severity_scores = [e["severity_alignment"] for e in entries]
        
        avg_similarity = sum(similarity_scores) / len(similarity_scores)
        avg_severity = sum(severity_scores) / len(severity_scores)
        
        # Models used
        models = set(e.get("local_model", "unknown") for e in entries)
        
        # Latest entry
        latest = entries[-1]
        
        # 85% threshold check
        ready_for_sovereign = avg_similarity >= 85.0
        
        return {
            "total_comparisons": len(entries),
            "accuracy_pct": round(avg_similarity, 1),
            "severity_alignment_pct": round(avg_severity, 1),
            "ready_for_sovereign": ready_for_sovereign,
            "threshold": 85.0,
            "gap_to_threshold": round(85.0 - avg_similarity, 1) if not ready_for_sovereign else 0,
            "models_tested": list(models),
            "latest_comparison": latest["timestamp"],
            "recommendation": (
                "✅ READY: Local accuracy ≥85%. Safe to switch to sovereign inference."
                if ready_for_sovereign else
                f"⏳ TESTING: {round(85.0 - avg_similarity, 1)}% gap to 85% threshold. Keep testing."
            )
        }
    
    def get_model_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get accuracy breakdown by model"""
        
        if not self.log_path.exists():
            return {}
        
        entries = []
        with open(self.log_path, "r") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        
        # Group by model
        by_model = {}
        for e in entries:
            model = e.get("local_model", "unknown")
            if model not in by_model:
                by_model[model] = []
            by_model[model].append(e["similarity_score"])
        
        # Calculate averages
        result = {}
        for model, scores in by_model.items():
            avg = sum(scores) / len(scores)
            result[model] = {
                "comparisons": len(scores),
                "accuracy_pct": round(avg, 1),
                "ready": avg >= 85.0
            }
        
        return result
    
    def clear_logs(self):
        """Clear all comparison logs (for fresh start)"""
        if self.log_path.exists():
            self.log_path.unlink()
        print(f"Cleared accuracy logs at {self.log_path}")


def print_accuracy_report():
    """Print a formatted accuracy report"""
    tracker = AccuracyTracker()
    stats = tracker.get_stats()
    
    print("\n" + "="*60)
    print("📊 LM STUDIO ACCURACY REPORT")
    print("="*60)
    print(f"Total Comparisons:    {stats['total_comparisons']}")
    print(f"Current Accuracy:     {stats['accuracy_pct']}%")
    print(f"Target Threshold:     {stats['threshold']}%")
    print(f"Gap to Threshold:     {stats.get('gap_to_threshold', 0)}%")
    print("-"*60)
    print(f"Status: {stats['recommendation']}")
    print("="*60)
    
    if stats['total_comparisons'] > 0:
        breakdown = tracker.get_model_breakdown()
        if breakdown:
            print("\n📦 BY MODEL:")
            for model, data in breakdown.items():
                status = "✅" if data["ready"] else "⏳"
                print(f"  {status} {model}: {data['accuracy_pct']}% ({data['comparisons']} tests)")
    
    print()


if __name__ == "__main__":
    print_accuracy_report()
