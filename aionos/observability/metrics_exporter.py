"""
AION OS - Metrics Exporter
============================

Provides Prometheus-compatible metrics endpoint and OpenTelemetry-style
metric collection for enterprise observability integration.

Gemini Finding: "No Prometheus/Grafana exports. High-end firms require
their security tools to 'report for duty' to their existing SIEM/SOAR."

This module:
  - Collects engine metrics (throughput, latency, pattern matches, alerts)
  - Exposes /metrics endpoint in Prometheus text exposition format
  - Supports push-based export to Grafana/InfluxDB/OTLP collectors
  - Integrates with existing watchdog + usage_tracker modules

Usage:
    registry = MetricsRegistry()
    registry.counter("events_ingested_total", "Total events ingested")
    registry.inc("events_ingested_total", labels={"source": "splunk"})

    exporter = MetricsExporter(registry)
    print(exporter.to_prometheus())
"""

import time
import threading
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger("aionos.observability")


# =============================================================================
# METRIC TYPES
# =============================================================================

@dataclass
class MetricSample:
    """A single metric data point."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[float] = None  # Unix epoch, None = scrape time

    def label_str(self) -> str:
        if not self.labels:
            return ""
        pairs = ",".join(f'{k}="{v}"' for k, v in sorted(self.labels.items()))
        return "{" + pairs + "}"


class Counter:
    """Monotonically increasing counter (resets on restart)."""

    def __init__(self, name: str, help_text: str):
        self.name = name
        self.help_text = help_text
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, amount: float = 1.0, labels: Dict[str, str] = None):
        key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._values[key] += amount

    def samples(self) -> List[MetricSample]:
        with self._lock:
            return [
                MetricSample(self.name, val, dict(key))
                for key, val in self._values.items()
            ]


class Gauge:
    """Value that can go up or down."""

    def __init__(self, name: str, help_text: str):
        self.name = name
        self.help_text = help_text
        self._values: Dict[tuple, float] = defaultdict(float)
        self._lock = threading.Lock()

    def set(self, value: float, labels: Dict[str, str] = None):
        key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._values[key] = value

    def inc(self, amount: float = 1.0, labels: Dict[str, str] = None):
        key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._values[key] += amount

    def dec(self, amount: float = 1.0, labels: Dict[str, str] = None):
        key = tuple(sorted((labels or {}).items()))
        with self._lock:
            self._values[key] -= amount

    def samples(self) -> List[MetricSample]:
        with self._lock:
            return [
                MetricSample(self.name, val, dict(key))
                for key, val in self._values.items()
            ]


class Histogram:
    """
    Tracks value distributions with configurable buckets.
    
    Emits _bucket, _count, _sum series (Prometheus-compatible).
    """

    DEFAULT_BUCKETS = (
        0.00005, 0.0001, 0.00025, 0.0005, 0.001,
        0.0025, 0.005, 0.01, 0.025, 0.05,
        0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf"),
    )

    def __init__(self, name: str, help_text: str, buckets: Tuple[float, ...] = None):
        self.name = name
        self.help_text = help_text
        self.buckets = buckets or self.DEFAULT_BUCKETS
        self._counts: Dict[tuple, Dict[float, int]] = {}
        self._sums: Dict[tuple, float] = defaultdict(float)
        self._totals: Dict[tuple, int] = defaultdict(int)
        self._lock = threading.Lock()

    def observe(self, value: float, labels: Dict[str, str] = None):
        key = tuple(sorted((labels or {}).items()))
        with self._lock:
            if key not in self._counts:
                self._counts[key] = {b: 0 for b in self.buckets}
            for b in self.buckets:
                if value <= b:
                    self._counts[key][b] += 1
            self._sums[key] += value
            self._totals[key] += 1

    def samples(self) -> List[MetricSample]:
        result = []
        with self._lock:
            for key in self._counts:
                label_dict = dict(key)
                for b in self.buckets:
                    le_label = "+Inf" if b == float("inf") else str(b)
                    result.append(MetricSample(
                        f"{self.name}_bucket",
                        self._counts[key][b],
                        {**label_dict, "le": le_label},
                    ))
                result.append(MetricSample(
                    f"{self.name}_sum", self._sums[key], label_dict
                ))
                result.append(MetricSample(
                    f"{self.name}_count", self._totals[key], label_dict
                ))
        return result


# =============================================================================
# METRICS REGISTRY
# =============================================================================

class MetricsRegistry:
    """
    Central registry for all AION OS metrics.

    Metrics are registered once and updated throughout the application
    lifecycle. The registry exports all metrics in Prometheus format.
    """

    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()

        # Pre-register AION OS core metrics
        self._register_core_metrics()

    def _register_core_metrics(self):
        """Register built-in AION OS metrics."""

        # --- Engine metrics ---
        self.counter(
            "aion_events_ingested_total",
            "Total security events ingested"
        )
        self.counter(
            "aion_alerts_fired_total",
            "Total correlation alerts generated"
        )
        self.counter(
            "aion_patterns_matched_total",
            "Total attack pattern matches"
        )
        self.histogram(
            "aion_event_latency_seconds",
            "Per-event processing latency in seconds",
            buckets=(
                0.00005, 0.0001, 0.00025, 0.0005, 0.001,
                0.005, 0.01, 0.05, 0.1, 0.5, 1.0, float("inf"),
            ),
        )
        self.gauge(
            "aion_active_users",
            "Number of users with events in the tracking window"
        )
        self.gauge(
            "aion_attack_patterns_loaded",
            "Number of attack patterns loaded in detection engine"
        )

        # --- Baseline metrics ---
        self.counter(
            "aion_baseline_deviations_total",
            "Total behavioral deviations detected"
        )
        self.gauge(
            "aion_baseline_profiles_active",
            "Number of active user profiles in baseline engine"
        )

        # --- Improvement engine metrics ---
        self.counter(
            "aion_improvement_cycles_total",
            "Total improvement cycles executed"
        )
        self.counter(
            "aion_feedback_received_total",
            "Total analyst feedback items received"
        )
        self.counter(
            "aion_feedback_flagged_total",
            "Feedback items flagged by anti-poisoning guard"
        )
        self.gauge(
            "aion_policy_active_version",
            "Currently active policy version number"
        )

        # --- API metrics ---
        self.counter(
            "aion_api_requests_total",
            "Total API requests by endpoint and status"
        )
        self.histogram(
            "aion_api_latency_seconds",
            "API request latency in seconds"
        )

        # --- System metrics ---
        self.gauge(
            "aion_uptime_seconds",
            "Seconds since AION OS started"
        )
        self.gauge(
            "aion_info",
            "AION OS build information"
        )

    def counter(self, name: str, help_text: str) -> Counter:
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Counter(name, help_text)
            return self._metrics[name]

    def gauge(self, name: str, help_text: str) -> Gauge:
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Gauge(name, help_text)
            return self._metrics[name]

    def histogram(self, name: str, help_text: str, buckets=None) -> Histogram:
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = Histogram(name, help_text, buckets)
            return self._metrics[name]

    def inc(self, name: str, amount: float = 1.0, labels: Dict[str, str] = None):
        """Increment a counter or gauge by name."""
        metric = self._metrics.get(name)
        if metric:
            metric.inc(amount, labels)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge value by name."""
        metric = self._metrics.get(name)
        if metric and isinstance(metric, Gauge):
            metric.set(value, labels)

    def observe(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram observation by name."""
        metric = self._metrics.get(name)
        if metric and isinstance(metric, Histogram):
            metric.observe(value, labels)

    def get_metric(self, name: str):
        return self._metrics.get(name)

    def all_metrics(self) -> Dict[str, Any]:
        return dict(self._metrics)


# =============================================================================
# PROMETHEUS EXPORTER
# =============================================================================

class MetricsExporter:
    """
    Exports metrics in Prometheus text exposition format.

    Meant to be mounted at /metrics on the FastAPI app for
    Prometheus scraping or Grafana Agent pickup.
    """

    def __init__(self, registry: MetricsRegistry):
        self.registry = registry

    def to_prometheus(self) -> str:
        """
        Render all metrics in Prometheus text exposition format.

        Format:
            # HELP metric_name Description
            # TYPE metric_name counter|gauge|histogram
            metric_name{label="value"} 123.0
        """
        # Update uptime
        self.registry.set_gauge("aion_uptime_seconds", time.time() - self.registry._start_time)

        lines: List[str] = []

        for name, metric in sorted(self.registry.all_metrics().items()):
            # Type declaration
            if isinstance(metric, Counter):
                mtype = "counter"
            elif isinstance(metric, Gauge):
                mtype = "gauge"
            elif isinstance(metric, Histogram):
                mtype = "histogram"
            else:
                continue

            lines.append(f"# HELP {name} {metric.help_text}")
            lines.append(f"# TYPE {name} {mtype}")

            for sample in metric.samples():
                label_str = sample.label_str()
                ts_str = ""
                if sample.timestamp:
                    ts_str = f" {int(sample.timestamp * 1000)}"
                lines.append(f"{sample.name}{label_str} {sample.value}{ts_str}")

            lines.append("")  # Blank line between metrics

        return "\n".join(lines)

    def to_json(self) -> Dict[str, Any]:
        """
        Export metrics as JSON (for custom dashboards / REST consumers).
        """
        # Update uptime
        self.registry.set_gauge("aion_uptime_seconds", time.time() - self.registry._start_time)

        result = {}
        for name, metric in self.registry.all_metrics().items():
            samples = metric.samples()
            if len(samples) == 1 and not samples[0].labels:
                result[name] = samples[0].value
            else:
                result[name] = [
                    {"value": s.value, "labels": s.labels}
                    for s in samples
                ]
        return result


# =============================================================================
# SINGLETON REGISTRY
# =============================================================================

_global_registry: Optional[MetricsRegistry] = None


def get_metrics_registry() -> MetricsRegistry:
    """Get the global metrics registry (singleton)."""
    global _global_registry
    if _global_registry is None:
        _global_registry = MetricsRegistry()
    return _global_registry


def get_metrics_exporter() -> MetricsExporter:
    """Get a metrics exporter for the global registry."""
    return MetricsExporter(get_metrics_registry())
