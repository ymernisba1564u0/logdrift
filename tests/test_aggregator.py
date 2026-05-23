"""Tests for LogAggregator field-based grouping and anomaly detection."""

import pytest

from logdrift.aggregator import LogAggregator


BASE_TS = 1_700_000_000.0


def _warm_up(aggregator: LogAggregator, key_value: str, n: int, field: str = "service") -> None:
    """Record n events for a given group key to build a baseline."""
    for i in range(n):
        aggregator.observe({field: key_value}, BASE_TS + i)


def test_no_anomaly_on_empty_baseline():
    agg = LogAggregator(group_by="service", window_seconds=60, threshold=2.0, min_baseline=5)
    result = agg.observe({"service": "auth"}, BASE_TS)
    assert result is None


def test_group_keys_tracked_separately():
    agg = LogAggregator(group_by="service", window_seconds=60)
    agg.observe({"service": "auth"}, BASE_TS)
    agg.observe({"service": "payment"}, BASE_TS + 1)
    agg.observe({"service": "auth"}, BASE_TS + 2)
    keys = agg.group_keys()
    assert "auth" in keys
    assert "payment" in keys


def test_group_counts_reflect_observations():
    agg = LogAggregator(group_by="service", window_seconds=60)
    for i in range(3):
        agg.observe({"service": "auth"}, BASE_TS + i)
    for i in range(5):
        agg.observe({"service": "payment"}, BASE_TS + i)
    counts = agg.group_counts()
    assert counts["auth"] == 3
    assert counts["payment"] == 5


def test_missing_field_uses_placeholder():
    agg = LogAggregator(group_by="service", window_seconds=60)
    agg.observe({"level": "error"}, BASE_TS)
    assert "<missing>" in agg.group_keys()


def test_anomaly_detected_for_specific_group():
    agg = LogAggregator(
        group_by="service", window_seconds=120, threshold=2.0, min_baseline=5
    )
    _warm_up(agg, "auth", 20)
    # spike: many events in rapid succession
    spike_ts = BASE_TS + 25
    event = None
    for i in range(15):
        event = agg.observe({"service": "auth"}, spike_ts + i * 0.1)
    assert event is not None


def test_no_cross_group_interference():
    agg = LogAggregator(
        group_by="service", window_seconds=120, threshold=2.0, min_baseline=5
    )
    _warm_up(agg, "auth", 20)
    # payment group has no baseline — should not trigger anomaly from auth spike
    result = agg.observe({"service": "payment"}, BASE_TS + 100)
    assert result is None
