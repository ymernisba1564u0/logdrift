"""Export anomaly reports to JSON or plain-text formats."""

from __future__ import annotations

import json
from typing import IO, Literal

from logdrift.report import AggregatorReport
from logdrift.formatter import format_anomaly, format_summary

OutputFormat = Literal["json", "text"]


def export_report(
    report: AggregatorReport,
    dest: IO[str],
    fmt: OutputFormat = "text",
) -> None:
    """Write *report* to *dest* in the requested format."""
    if fmt == "json":
        _export_json(report, dest)
    else:
        _export_text(report, dest)


def _export_text(report: AggregatorReport, dest: IO[str]) -> None:
    for group in report.groups:
        dest.write(f"=== group: {group.group_by_field}={group.group_key} ===\n")
        dest.write(format_summary(group.total_events, group.total_anomalies))
        dest.write("\n")
        for event in group.anomalies:
            dest.write(format_anomaly(event))
            dest.write("\n")


def _export_json(report: AggregatorReport, dest: IO[str]) -> None:
    payload = {
        "groups": [
            {
                "group_by_field": g.group_by_field,
                "group_key": g.group_key,
                "total_events": g.total_events,
                "total_anomalies": g.total_anomalies,
                "anomalies": [
                    {
                        "timestamp": e.timestamp,
                        "rate": e.rate,
                        "baseline": e.baseline,
                        "threshold": e.threshold,
                        "label": e.label,
                    }
                    for e in g.anomalies
                ],
            }
            for g in report.groups
        ]
    }
    json.dump(payload, dest, indent=2)
    dest.write("\n")
