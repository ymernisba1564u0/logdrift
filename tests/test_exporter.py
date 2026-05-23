"""Tests for logdrift.exporter."""

from __future__ import annotations

import io
import json

import pytest

from logdrift.detector import AnomalyEvent
from logdrift.report import AggregatorReport, ReportBuilder
from logdrift.exporter import export_report


def _make_event(rate: float = 5.0, baseline: float = 1.0) -> AnomalyEvent:
    return AnomalyEvent(
        timestamp=1_700_000_000.0,
        rate=rate,
        baseline=baseline,
        threshold=3.0,
        label="status",
    )


def _build_report() -> AggregatorReport:
    builder = ReportBuilder(group_by_field="status")
    builder.record_event(group_key="500", event_count=10)
    builder.record_anomaly(group_key="500", event=_make_event())
    return builder.build()


# ---------------------------------------------------------------------------
# text format
# ---------------------------------------------------------------------------

def test_text_export_contains_group_header():
    buf = io.StringIO()
    export_report(_build_report(), buf, fmt="text")
    assert "status=500" in buf.getvalue()


def test_text_export_contains_summary():
    buf = io.StringIO()
    export_report(_build_report(), buf, fmt="text")
    output = buf.getvalue()
    assert "10" in output  # total events
    assert "1" in output   # total anomalies


def test_text_export_contains_anomaly_rate():
    buf = io.StringIO()
    export_report(_build_report(), buf, fmt="text")
    assert "5.0" in buf.getvalue() or "5" in buf.getvalue()


# ---------------------------------------------------------------------------
# json format
# ---------------------------------------------------------------------------

def test_json_export_is_valid_json():
    buf = io.StringIO()
    export_report(_build_report(), buf, fmt="json")
    data = json.loads(buf.getvalue())  # must not raise
    assert "groups" in data


def test_json_export_group_fields():
    buf = io.StringIO()
    export_report(_build_report(), buf, fmt="json")
    group = json.loads(buf.getvalue())["groups"][0]
    assert group["group_by_field"] == "status"
    assert group["group_key"] == "500"
    assert group["total_events"] == 10
    assert group["total_anomalies"] == 1


def test_json_export_anomaly_fields():
    buf = io.StringIO()
    export_report(_build_report(), buf, fmt="json")
    anomaly = json.loads(buf.getvalue())["groups"][0]["anomalies"][0]
    assert anomaly["rate"] == pytest.approx(5.0)
    assert anomaly["baseline"] == pytest.approx(1.0)
    assert anomaly["threshold"] == pytest.approx(3.0)
    assert anomaly["label"] == "status"


def test_empty_report_json_has_empty_groups():
    builder = ReportBuilder(group_by_field="level")
    report = builder.build()
    buf = io.StringIO()
    export_report(report, buf, fmt="json")
    data = json.loads(buf.getvalue())
    assert data["groups"] == []
