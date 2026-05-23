"""Tests for logdrift.formatter."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from logdrift.detector import AnomalyEvent
from logdrift.formatter import format_anomaly, format_summary, OUTPUT_FORMATS


_TS = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _make_event(
    current_rate: float = 10.0,
    baseline_rate: float = 2.0,
    threshold: float = 3.0,
) -> AnomalyEvent:
    return AnomalyEvent(
        timestamp=_TS,
        current_rate=current_rate,
        baseline_rate=baseline_rate,
        threshold=threshold,
    )


# ---------------------------------------------------------------------------
# format_anomaly — text
# ---------------------------------------------------------------------------

def test_format_anomaly_text_contains_rate():
    out = format_anomaly(_make_event(), fmt="text")
    assert "rate=10.00/s" in out


def test_format_anomaly_text_contains_baseline():
    out = format_anomaly(_make_event(), fmt="text")
    assert "baseline=2.00/s" in out


def test_format_anomaly_text_contains_timestamp():
    out = format_anomaly(_make_event(), fmt="text")
    assert "2024-06-01T12:00:00" in out


def test_format_anomaly_text_contains_anomaly_label():
    out = format_anomaly(_make_event(), fmt="text")
    assert "ANOMALY" in out


# ---------------------------------------------------------------------------
# format_anomaly — json / jsonl
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("fmt", ["json", "jsonl"])
def test_format_anomaly_json_is_valid(fmt):
    out = format_anomaly(_make_event(), fmt=fmt)
    data = json.loads(out)  # must not raise
    assert data["anomaly"] is True


@pytest.mark.parametrize("fmt", ["json", "jsonl"])
def test_format_anomaly_json_fields(fmt):
    event = _make_event(current_rate=5.5, baseline_rate=1.1, threshold=4.0)
    data = json.loads(format_anomaly(event, fmt=fmt))
    assert data["current_rate"] == pytest.approx(5.5, rel=1e-3)
    assert data["baseline_rate"] == pytest.approx(1.1, rel=1e-3)
    assert data["threshold"] == 4.0


def test_format_anomaly_unknown_format_raises():
    with pytest.raises(ValueError, match="Unknown format"):
        format_anomaly(_make_event(), fmt="csv")


# ---------------------------------------------------------------------------
# format_summary
# ---------------------------------------------------------------------------

def test_format_summary_contains_line_count():
    out = format_summary(total_lines=500, anomaly_count=3, elapsed=10.0)
    assert "500" in out


def test_format_summary_contains_anomaly_count():
    out = format_summary(total_lines=100, anomaly_count=7, elapsed=5.0)
    assert "7" in out


def test_format_summary_zero_elapsed_does_not_raise():
    out = format_summary(total_lines=0, anomaly_count=0, elapsed=0.0)
    assert "0" in out


def test_output_formats_constant():
    assert "text" in OUTPUT_FORMATS
    assert "json" in OUTPUT_FORMATS
    assert "jsonl" in OUTPUT_FORMATS
