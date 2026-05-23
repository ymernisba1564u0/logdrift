"""Tests for the anomaly detector."""

import pytest
from logdrift.detector import AnomalyDetector, AnomalyEvent


def _warm_up(detector: AnomalyDetector, event_key: str, base_ts: float, count: int = 30) -> None:
    """Populate the long baseline without triggering the short window."""
    step = detector._long.window_seconds / count
    for i in range(count):
        detector.observe(event_key, timestamp=base_ts + i * step)


def test_no_anomaly_on_empty_baseline():
    det = AnomalyDetector(short_window=5, long_window=60, spike_threshold=3.0)
    result = det.observe("error", timestamp=1000.0)
    assert result is None


def test_no_anomaly_below_threshold():
    det = AnomalyDetector(short_window=5, long_window=60, spike_threshold=3.0)
    _warm_up(det, "error", base_ts=900.0)
    # Observe at a normal rate — should not trigger
    result = det.observe("error", timestamp=1200.0)
    assert result is None


def test_anomaly_detected_on_spike():
    det = AnomalyDetector(short_window=5, long_window=300, spike_threshold=3.0)
    _warm_up(det, "error", base_ts=500.0, count=50)
    # Flood the short window well past the threshold
    anomalies = det.bulk_observe("error", count=200, timestamp=1000.0)
    assert len(anomalies) > 0
    first = anomalies[0]
    assert isinstance(first, AnomalyEvent)
    assert first.spike_ratio >= 3.0
    assert first.event_key == "error"


def test_anomaly_event_str():
    evt = AnomalyEvent(
        event_key="timeout",
        current_rate=9.0,
        baseline_rate=3.0,
        spike_ratio=3.0,
        timestamp=1000.0,
    )
    text = str(evt)
    assert "ANOMALY" in text
    assert "timeout" in text
    assert "3.00x" in text


def test_independent_keys_no_cross_contamination():
    det = AnomalyDetector(short_window=5, long_window=300, spike_threshold=3.0)
    _warm_up(det, "error", base_ts=500.0, count=50)
    # Spike only "error", "warn" should stay quiet
    det.bulk_observe("error", count=200, timestamp=1000.0)
    result = det.observe("warn", timestamp=1000.0)
    assert result is None
