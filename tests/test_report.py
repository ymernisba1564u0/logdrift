"""Tests for ReportBuilder and AggregatorReport."""

import pytest

from logdrift.aggregator import LogAggregator
from logdrift.detector import AnomalyEvent
from logdrift.report import ReportBuilder, AggregatorReport


BASE_TS = 1_700_000_000.0


def _make_event(group: str = "auth") -> AnomalyEvent:
    return AnomalyEvent(
        timestamp=BASE_TS,
        current_rate=10.0,
        baseline_rate=2.0,
        threshold=2.0,
        label=group,
    )


def test_empty_report_has_no_groups():
    agg = LogAggregator(group_by="service")
    builder = ReportBuilder(agg)
    report = builder.build()
    assert isinstance(report, AggregatorReport)
    assert report.groups == []
    assert report.total_anomalies() == 0
    assert report.total_events() == 0


def test_report_reflects_group_counts():
    agg = LogAggregator(group_by="service", window_seconds=60)
    for i in range(4):
        agg.observe({"service": "auth"}, BASE_TS + i)
    builder = ReportBuilder(agg)
    report = builder.build()
    auth_group = next(g for g in report.groups if g.group_key == "auth")
    assert auth_group.event_count == 4


def test_report_counts_recorded_anomalies():
    agg = LogAggregator(group_by="service")
    agg.observe({"service": "auth"}, BASE_TS)
    builder = ReportBuilder(agg)
    builder.record_anomaly("auth", _make_event("auth"))
    builder.record_anomaly("auth", _make_event("auth"))
    report = builder.build()
    auth_group = next(g for g in report.groups if g.group_key == "auth")
    assert auth_group.anomaly_count == 2
    assert report.total_anomalies() == 2


def test_report_group_by_field_preserved():
    agg = LogAggregator(group_by="endpoint")
    builder = ReportBuilder(agg)
    report = builder.build()
    assert report.group_by == "endpoint"


def test_multiple_groups_in_report():
    agg = LogAggregator(group_by="service", window_seconds=60)
    agg.observe({"service": "auth"}, BASE_TS)
    agg.observe({"service": "payment"}, BASE_TS + 1)
    builder = ReportBuilder(agg)
    builder.record_anomaly("payment", _make_event("payment"))
    report = builder.build()
    assert len(report.groups) == 2
    assert report.total_anomalies() == 1
    assert report.total_events() == 2
