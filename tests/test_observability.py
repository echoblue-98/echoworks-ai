"""
Tests for the observability / metrics export module.
"""

import pytest


class TestMetricsRegistry:
    """Tests for the MetricsRegistry."""

    def test_registry_has_core_metrics(self):
        from aionos.observability.metrics_exporter import MetricsRegistry
        registry = MetricsRegistry()
        all_m = registry.all_metrics()
        names = list(all_m.keys())
        assert "aion_events_ingested_total" in names
        assert "aion_alerts_fired_total" in names
        assert "aion_event_latency_seconds" in names

    def test_counter_increment(self):
        from aionos.observability.metrics_exporter import MetricsRegistry
        reg = MetricsRegistry()
        c = reg.counter("test_counter", "A test counter")
        c.inc()
        c.inc(5)
        assert c._values[()] == 6

    def test_gauge_set(self):
        from aionos.observability.metrics_exporter import MetricsRegistry
        reg = MetricsRegistry()
        g = reg.gauge("test_gauge", "A test gauge")
        g.set(42)
        assert g._values[()] == 42

    def test_histogram_observe(self):
        from aionos.observability.metrics_exporter import MetricsRegistry
        reg = MetricsRegistry()
        h = reg.histogram("test_hist", "A test histogram")
        h.observe(0.1)
        h.observe(0.5)
        assert h._totals[()] == 2


class TestMetricsExporter:
    """Tests for Prometheus and JSON export."""

    def test_prometheus_format(self):
        from aionos.observability.metrics_exporter import get_metrics_exporter
        exporter = get_metrics_exporter()
        output = exporter.to_prometheus()
        assert isinstance(output, str)
        assert "# HELP" in output
        assert "# TYPE" in output

    def test_json_format(self):
        from aionos.observability.metrics_exporter import get_metrics_exporter
        exporter = get_metrics_exporter()
        data = exporter.to_json()
        assert isinstance(data, dict)
        assert "metrics" in data or len(data) > 0
