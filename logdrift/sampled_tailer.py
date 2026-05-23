"""Combines LogTailer with LogSampler to produce a sampled log stream."""

from typing import Callable, Dict, Optional

from logdrift.sampler import LogSampler
from logdrift.tailer import LogTailer, parse_log_line


class SampledLogTailer:
    """A log tailer that drops records probabilistically before processing."""

    def __init__(
        self,
        tailer: LogTailer,
        sampler: LogSampler,
        on_drop: Optional[Callable[[dict], None]] = None,
    ) -> None:
        self._tailer = tailer
        self._sampler = sampler
        self._on_drop = on_drop
        self._dropped = 0
        self._forwarded = 0

    @property
    def dropped(self) -> int:
        return self._dropped

    @property
    def forwarded(self) -> int:
        return self._forwarded

    def process_line(self, line: str) -> Optional[dict]:
        """Parse *line*, sample it, and forward to the inner tailer if kept."""
        record = parse_log_line(line)
        if record is None:
            return None

        if not self._sampler.should_keep(record):
            self._dropped += 1
            if self._on_drop is not None:
                self._on_drop(record)
            return None

        self._forwarded += 1
        self._tailer.process_line(line)
        return record

    def summary(self) -> Dict[str, int]:
        return {
            "forwarded": self._forwarded,
            "dropped": self._dropped,
            "total": self._forwarded + self._dropped,
        }


def make_sampled_tailer(
    tailer: LogTailer,
    default_rate: float = 1.0,
    field_rates: Optional[Dict[str, Dict[str, float]]] = None,
) -> SampledLogTailer:
    """Factory that wires a LogSampler to a LogTailer."""
    sampler = LogSampler(default_rate=default_rate)
    if field_rates:
        for field, value_map in field_rates.items():
            for value, rate in value_map.items():
                sampler.set_field_rate(field, value, rate)
    return SampledLogTailer(tailer, sampler)
