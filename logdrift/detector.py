"""Anomaly detector that compares current rates against rolling baselines."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

from logdrift.baseline import BaselineWindow


@dataclass
class AnomalyEvent:
    event_key: str
    current_rate: float
    baseline_rate: float
    spike_ratio: float
    timestamp: float

    def __str__(self) -> str:
        return (
            f"[ANOMALY] '{self.event_key}' spike_ratio={self.spike_ratio:.2f}x "
            f"(current={self.current_rate:.3f}/s baseline={self.baseline_rate:.3f}/s)"
        )


class AnomalyDetector:
    """Detects rate spikes by comparing a short window against a longer baseline."""

    def __init__(
        self,
        short_window: int = 10,
        long_window: int = 300,
        spike_threshold: float = 3.0,
    ) -> None:
        self.spike_threshold = spike_threshold
        self._short = BaselineWindow(window_seconds=short_window)
        self._long = BaselineWindow(window_seconds=long_window)

    def observe(self, event_key: str, timestamp: Optional[float] = None) -> Optional[AnomalyEvent]:
        """Record an event and return an AnomalyEvent if a spike is detected."""
        ts = timestamp if timestamp is not None else time.time()
        self._short.record(event_key, ts)
        self._long.record(event_key, ts)

        current_rate = self._short.rate(event_key, ts)
        baseline_rate = self._long.rate(event_key, ts)

        if baseline_rate == 0:
            return None

        ratio = current_rate / baseline_rate
        if ratio >= self.spike_threshold:
            return AnomalyEvent(
                event_key=event_key,
                current_rate=current_rate,
                baseline_rate=baseline_rate,
                spike_ratio=ratio,
                timestamp=ts,
            )
        return None

    def bulk_observe(self, event_key: str, count: int, timestamp: Optional[float] = None) -> List[AnomalyEvent]:
        """Record multiple events and collect any anomalies produced."""
        ts = timestamp if timestamp is not None else time.time()
        anomalies: List[AnomalyEvent] = []
        for _ in range(count):
            result = self.observe(event_key, ts)
            if result:
                anomalies.append(result)
        return anomalies
