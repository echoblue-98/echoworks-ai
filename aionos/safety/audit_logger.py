"""
Audit Logger - Tracks all AION OS usage for accountability

Every query, analysis, and result is logged for:
- Security audit trails
- Compliance requirements
- Misuse detection
- Usage analytics
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class AuditLogger:
    """
    Comprehensive audit logging for AION OS.
    
    Logs all interactions for:
    - Accountability
    - Security monitoring
    - Compliance (SOC2, HIPAA, etc.)
    - Misuse detection
    """
    
    def __init__(self, log_path: str = "./logs/audit.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    def log_query(
        self,
        user_id: str,
        query: str,
        context: Dict[str, Any] = None,
        intent_classification: Dict[str, Any] = None
    ) -> str:
        """
        Log user query.
        
        Args:
            user_id: User identifier
            query: The user's query
            context: Query context
            intent_classification: Result from intent classifier
        
        Returns:
            Query log ID for tracking
        """
        log_id = f"query_{datetime.utcnow().timestamp()}"
        
        log_entry = {
            "log_id": log_id,
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "query",
            "user_id": user_id,
            "query": query,
            "context": context or {},
            "intent_classification": intent_classification
        }
        
        self._write_log(log_entry)
        return log_id
    
    def log_analysis(
        self,
        query_id: str,
        user_id: str,
        analysis_type: str,
        perspectives_used: list[str],
        vulnerabilities_found: int,
        critical_count: int,
        blocked: bool = False,
        block_reason: str = None
    ):
        """
        Log analysis results.
        
        Args:
            query_id: Associated query ID
            user_id: User identifier
            analysis_type: Type of analysis performed
            perspectives_used: Which adversarial perspectives were used
            vulnerabilities_found: Total vulnerabilities found
            critical_count: Number of P0/P1 vulnerabilities
            blocked: Whether analysis was blocked
            block_reason: Reason for blocking if applicable
        """
        log_entry = {
            "log_id": f"analysis_{datetime.utcnow().timestamp()}",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "analysis",
            "query_id": query_id,
            "user_id": user_id,
            "analysis_type": analysis_type,
            "perspectives_used": perspectives_used,
            "vulnerabilities_found": vulnerabilities_found,
            "critical_vulnerabilities": critical_count,
            "blocked": blocked,
            "block_reason": block_reason
        }
        
        self._write_log(log_entry)
    
    def log_ethical_violation(
        self,
        user_id: str,
        query: str,
        violation_type: str,
        violation_message: str,
        context: Dict[str, Any] = None
    ):
        """
        Log ethical boundary violation.
        
        Args:
            user_id: User identifier
            query: The violating query
            violation_type: Type of violation
            violation_message: Description of violation
            context: Additional context
        """
        log_entry = {
            "log_id": f"violation_{datetime.utcnow().timestamp()}",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "ethical_violation",
            "severity": "HIGH",
            "user_id": user_id,
            "query": query[:200],  # Limit query length for privacy
            "violation_type": violation_type,
            "violation_message": violation_message,
            "context": context or {}
        }
        
        self._write_log(log_entry)
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        details: Dict[str, Any] = None
    ):
        """
        Log user actions (login, level change, etc.).
        
        Args:
            user_id: User identifier
            action: Action performed
            details: Additional details
        """
        log_entry = {
            "log_id": f"action_{datetime.utcnow().timestamp()}",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "user_action",
            "user_id": user_id,
            "action": action,
            "details": details or {}
        }
        
        self._write_log(log_entry)
    
    def log_system_event(
        self,
        event_type: str,
        message: str,
        severity: str = "INFO",
        details: Dict[str, Any] = None
    ):
        """
        Log system events.
        
        Args:
            event_type: Type of system event
            message: Event message
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
            details: Additional details
        """
        log_entry = {
            "log_id": f"system_{datetime.utcnow().timestamp()}",
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "system_event",
            "severity": severity,
            "message": message,
            "details": details or {}
        }
        
        self._write_log(log_entry)
    
    def _write_log(self, log_entry: Dict[str, Any]):
        """Write log entry to file"""
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            # Fallback: print to console if file logging fails
            print(f"[AUDIT LOG ERROR] Failed to write log: {e}")
            print(json.dumps(log_entry))
    
    def query_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Query audit logs with filters.
        
        Args:
            user_id: Filter by user
            event_type: Filter by event type
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of results
        
        Returns:
            List of matching log entries
        """
        if not self.log_path.exists():
            return []
        
        results = []
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if user_id and entry.get("user_id") != user_id:
                            continue
                        
                        if event_type and entry.get("event_type") != event_type:
                            continue
                        
                        if start_date:
                            entry_time = datetime.fromisoformat(entry["timestamp"])
                            if entry_time < start_date:
                                continue
                        
                        if end_date:
                            entry_time = datetime.fromisoformat(entry["timestamp"])
                            if entry_time > end_date:
                                continue
                        
                        results.append(entry)
                        
                        if len(results) >= limit:
                            break
                    
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            print(f"[AUDIT LOG ERROR] Failed to query logs: {e}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit log statistics"""
        if not self.log_path.exists():
            return {"total_entries": 0}
        
        stats = {
            "total_entries": 0,
            "by_event_type": {},
            "by_severity": {},
            "violations": 0
        }
        
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        stats["total_entries"] += 1
                        
                        event_type = entry.get("event_type", "unknown")
                        stats["by_event_type"][event_type] = stats["by_event_type"].get(event_type, 0) + 1
                        
                        if event_type == "ethical_violation":
                            stats["violations"] += 1
                        
                        severity = entry.get("severity")
                        if severity:
                            stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
                    
                    except json.JSONDecodeError:
                        continue
        
        except Exception as e:
            print(f"[AUDIT LOG ERROR] Failed to get statistics: {e}")
        
        return stats
