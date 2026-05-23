"""Rolling baseline tracker for log event frequencies."""

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional
import time


@dataclass
class BaselineWindow:
    """Tracks event counts within a rolling time window."""

    window_seconds: int = 60
    _buckets: Deque[Dict[str, int]] = field(default_factory=deque)
    _timestamps: Deque[float] = field(default_factory=deque)

    def record(self, event_key: str, timestamp: Optional[float] = None) -> None:
        """Record an occurrence of event_key at the given timestamp."""
        ts = timestamp if timestamp is not None else time.time()
        self._evict_old(ts)

        if not self._buckets or self._timestamps[-1] != int(ts):
            self._buckets.append({event_key: 1})
            self._timestamps.append(int(ts))
        else:
            bucket = self._buckets[-1]
            bucket[event_key] = bucket.get(event_key, 0) + 1

    def count(self, event_key: str, timestamp: Optional[float] = None) -> int:
        """Return total count of event_key within the rolling window."""
        ts = timestamp if timestamp is not None else time.time()
        self._evict_old(ts)
        return sum(b.get(event_key, 0) for b in self._buckets)

    def rate(self, event_key: str, timestamp: Optional[float] = None) -> float:
        """Return events-per-second rate for event_key within the window."""
        return self.count(event_key, timestamp) / self.window_seconds

    def _evict_old(self, current_ts: float) -> None:
        cutoff = int(current_ts) - self.window_seconds
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()
            self._buckets.popleft()
