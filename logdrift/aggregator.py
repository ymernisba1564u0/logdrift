"""Field-based log aggregation for grouping anomaly detection by key."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Optional

from logdrift.baseline import BaselineWindow
from logdrift.detector import AnomalyDetector, AnomalyEvent


class AggregatorGroup:
    """Holds a baseline window and detector for a single group key."""

    def __init__(self, window_seconds: int, threshold: float, min_baseline: int) -> None:
        self.window = BaselineWindow(window_seconds)
        self.detector = AnomalyDetector(
            self.window, threshold=threshold, min_baseline=min_baseline
        )

    def observe(self, timestamp: float) -> Optional[AnomalyEvent]:
        self.window.record(timestamp)
        return self.detector.observe(timestamp)


class LogAggregator:
    """Aggregates log events by a field value and detects anomalies per group."""

    def __init__(
        self,
        group_by: str,
        window_seconds: int = 60,
        threshold: float = 2.0,
        min_baseline: int = 10,
    ) -> None:
        self.group_by = group_by
        self.window_seconds = window_seconds
        self.threshold = threshold
        self.min_baseline = min_baseline
        self._groups: Dict[str, AggregatorGroup] = defaultdict(
            lambda: AggregatorGroup(window_seconds, threshold, min_baseline)
        )

    def observe(self, record: dict, timestamp: float) -> Optional[AnomalyEvent]:
        """Record an event for the group derived from record[group_by]."""
        key = str(record.get(self.group_by, "<missing>"))
        return self._groups[key].observe(timestamp)

    def group_keys(self) -> List[str]:
        return list(self._groups.keys())

    def group_counts(self) -> Dict[str, int]:
        return {k: g.window.count() for k, g in self._groups.items()}
