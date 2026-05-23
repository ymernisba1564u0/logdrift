"""Periodic summary report generation for aggregated anomaly stats."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List

from logdrift.aggregator import LogAggregator
from logdrift.detector import AnomalyEvent


@dataclass
class GroupSummary:
    group_key: str
    event_count: int
    anomaly_count: int
    anomalies: List[AnomalyEvent] = field(default_factory=list)


@dataclass
class AggregatorReport:
    generated_at: float
    group_by: str
    groups: List[GroupSummary]

    def total_anomalies(self) -> int:
        return sum(g.anomaly_count for g in self.groups)

    def total_events(self) -> int:
        return sum(g.event_count for g in self.groups)


class ReportBuilder:
    """Collects anomaly events and builds summary reports from an aggregator."""

    def __init__(self, aggregator: LogAggregator) -> None:
        self._aggregator = aggregator
        self._anomalies: Dict[str, List[AnomalyEvent]] = {}

    def record_anomaly(self, group_key: str, event: AnomalyEvent) -> None:
        self._anomalies.setdefault(group_key, []).append(event)

    def build(self) -> AggregatorReport:
        counts = self._aggregator.group_counts()
        summaries = []
        for key in self._aggregator.group_keys():
            anomalies = self._anomalies.get(key, [])
            summaries.append(
                GroupSummary(
                    group_key=key,
                    event_count=counts.get(key, 0),
                    anomaly_count=len(anomalies),
                    anomalies=list(anomalies),
                )
            )
        return AggregatorReport(
            generated_at=time.time(),
            group_by=self._aggregator.group_by,
            groups=summaries,
        )
