"""
API Usage Tracker

Tracks Claude API usage and costs for pilot phase (first 50-100 use cases).
Critical for ROI analysis and justifying dedicated API key.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class UsageRecord:
    """Single API usage record"""
    timestamp: str
    use_case_id: str
    use_case_type: str  # legal, security, attorney_departure, quantum
    customer_id: Optional[str]
    tokens_input: int
    tokens_output: int
    cost: float
    model: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class UsageTracker:
    """
    Tracks API usage and costs.
    
    Critical for pilot phase: need 50-100 use cases with full metrics
    to justify enterprise API key or fine-tuning investment.
    """
    
    def __init__(self, db_path: str = "logs/api_usage.jsonl"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Budget settings from environment
        self.budget_limit = float(os.getenv("API_BUDGET_LIMIT", "2000.0"))
        self.warning_threshold = 0.8  # Warn at 80% budget
        
        # Pricing (Claude-3.5-Sonnet standard rates)
        self.price_input = 3.0 / 1_000_000  # $3 per million tokens
        self.price_output = 15.0 / 1_000_000  # $15 per million tokens
    
    def log_usage(
        self,
        use_case_id: str,
        use_case_type: str,
        tokens_input: int,
        tokens_output: int,
        model: str = "claude-3-5-sonnet-20241022",
        customer_id: Optional[str] = None
    ):
        """Log an API usage record"""
        
        cost = self.calculate_cost(tokens_input, tokens_output)
        
        record = UsageRecord(
            timestamp=datetime.now().isoformat(),
            use_case_id=use_case_id,
            use_case_type=use_case_type,
            customer_id=customer_id,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost=cost,
            model=model
        )
        
        # Append to JSONL file
        with open(self.db_path, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")
        
        # Check budget warnings
        self._check_budget_warnings()
    
    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost for token usage"""
        cost_input = tokens_input * self.price_input
        cost_output = tokens_output * self.price_output
        return cost_input + cost_output
    
    def get_all_records(self) -> List[UsageRecord]:
        """Load all usage records"""
        records = []
        
        if not self.db_path.exists():
            return records
        
        with open(self.db_path, "r") as f:
            for line in f:
                data = json.loads(line.strip())
                records.append(UsageRecord(**data))
        
        return records
    
    def get_total_cost(self) -> float:
        """Get total API spend"""
        records = self.get_all_records()
        return sum(r.cost for r in records)
    
    def get_total_use_cases(self) -> int:
        """Get total number of use cases"""
        records = self.get_all_records()
        # Count unique use case IDs
        return len(set(r.use_case_id for r in records))
    
    def is_budget_exceeded(self) -> bool:
        """Check if budget limit reached"""
        return self.get_total_cost() >= self.budget_limit
    
    def get_budget_remaining(self) -> float:
        """Get remaining budget"""
        return max(0, self.budget_limit - self.get_total_cost())
    
    def get_budget_percentage(self) -> float:
        """Get percentage of budget used"""
        return (self.get_total_cost() / self.budget_limit) * 100
    
    def _check_budget_warnings(self):
        """Check and log budget warnings"""
        percentage = self.get_budget_percentage()
        
        if percentage >= 100:
            print(f"⚠️  BUDGET EXCEEDED: ${self.get_total_cost():.2f} / ${self.budget_limit:.2f}")
        elif percentage >= self.warning_threshold * 100:
            print(f"⚠️  Budget warning: {percentage:.1f}% used (${self.get_total_cost():.2f} / ${self.budget_limit:.2f})")
    
    def get_metrics(self) -> Dict:
        """Get comprehensive usage metrics for ROI analysis"""
        records = self.get_all_records()
        
        if not records:
            return {
                "total_use_cases": 0,
                "total_cost": 0.0,
                "avg_cost_per_case": 0.0,
                "by_use_case_type": {},
                "by_customer": {},
                "budget_status": {
                    "limit": self.budget_limit,
                    "spent": 0.0,
                    "remaining": self.budget_limit,
                    "percentage": 0.0
                }
            }
        
        # Aggregate by use case type
        by_type = {}
        for record in records:
            if record.use_case_type not in by_type:
                by_type[record.use_case_type] = {
                    "count": 0,
                    "total_cost": 0.0,
                    "avg_cost": 0.0
                }
            by_type[record.use_case_type]["count"] += 1
            by_type[record.use_case_type]["total_cost"] += record.cost
        
        # Calculate averages
        for use_case_type in by_type:
            count = by_type[use_case_type]["count"]
            total = by_type[use_case_type]["total_cost"]
            by_type[use_case_type]["avg_cost"] = total / count if count > 0 else 0.0
        
        # Aggregate by customer
        by_customer = {}
        for record in records:
            if record.customer_id:
                if record.customer_id not in by_customer:
                    by_customer[record.customer_id] = {
                        "count": 0,
                        "total_cost": 0.0
                    }
                by_customer[record.customer_id]["count"] += 1
                by_customer[record.customer_id]["total_cost"] += record.cost
        
        total_cost = sum(r.cost for r in records)
        total_cases = len(set(r.use_case_id for r in records))
        
        return {
            "total_use_cases": total_cases,
            "total_api_calls": len(records),
            "total_cost": total_cost,
            "avg_cost_per_case": total_cost / total_cases if total_cases > 0 else 0.0,
            "by_use_case_type": by_type,
            "by_customer": by_customer,
            "budget_status": {
                "limit": self.budget_limit,
                "spent": total_cost,
                "remaining": self.get_budget_remaining(),
                "percentage": self.get_budget_percentage()
            },
            "pilot_progress": {
                "target": "50-100 use cases",
                "current": total_cases,
                "percentage_to_50": (total_cases / 50) * 100,
                "percentage_to_100": (total_cases / 100) * 100,
                "estimated_cost_to_50": (50 / total_cases * total_cost) if total_cases > 0 else 0,
                "estimated_cost_to_100": (100 / total_cases * total_cost) if total_cases > 0 else 0
            }
        }
    
    def format_metrics(self) -> str:
        """Format metrics for display"""
        metrics = self.get_metrics()
        
        output = []
        output.append("="*70)
        output.append("AION OS API Usage - Pilot Phase")
        output.append("="*70)
        output.append("")
        
        # Overview
        output.append(f"Total Use Cases: {metrics['total_use_cases']}")
        output.append(f"Total API Calls: {metrics['total_api_calls']}")
        output.append(f"Total Cost: ${metrics['total_cost']:.2f}")
        output.append(f"Avg Cost per Case: ${metrics['avg_cost_per_case']:.2f}")
        output.append("")
        
        # Budget status
        budget = metrics['budget_status']
        output.append("Budget Status:")
        output.append(f"  Limit: ${budget['limit']:.2f}")
        output.append(f"  Spent: ${budget['spent']:.2f}")
        output.append(f"  Remaining: ${budget['remaining']:.2f}")
        output.append(f"  Used: {budget['percentage']:.1f}%")
        output.append("")
        
        # Pilot progress
        pilot = metrics['pilot_progress']
        output.append("Pilot Progress (Target: 50-100 use cases):")
        output.append(f"  Current: {pilot['current']} cases")
        output.append(f"  Progress to 50: {pilot['percentage_to_50']:.1f}%")
        output.append(f"  Progress to 100: {pilot['percentage_to_100']:.1f}%")
        if pilot['current'] > 0:
            output.append(f"  Estimated cost to 50: ${pilot['estimated_cost_to_50']:.2f}")
            output.append(f"  Estimated cost to 100: ${pilot['estimated_cost_to_100']:.2f}")
        output.append("")
        
        # By use case type
        if metrics['by_use_case_type']:
            output.append("By Use Case Type:")
            for use_case_type, data in metrics['by_use_case_type'].items():
                output.append(f"  {use_case_type}:")
                output.append(f"    Count: {data['count']}")
                output.append(f"    Total Cost: ${data['total_cost']:.2f}")
                output.append(f"    Avg Cost: ${data['avg_cost']:.2f}")
            output.append("")
        
        # By customer
        if metrics['by_customer']:
            output.append("By Customer:")
            for customer_id, data in metrics['by_customer'].items():
                output.append(f"  {customer_id}:")
                output.append(f"    Cases: {data['count']}")
                output.append(f"    Total Cost: ${data['total_cost']:.2f}")
            output.append("")
        
        output.append("="*70)
        
        return "\n".join(output)


class BudgetExceededError(Exception):
    """Raised when API budget limit is exceeded"""
    pass


# CLI command to check usage
if __name__ == "__main__":
    tracker = UsageTracker()
    print(tracker.format_metrics())
