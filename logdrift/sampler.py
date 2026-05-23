"""Rate-based log sampler that probabilistically drops events to reduce noise."""

import random
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class SamplerStats:
    seen: int = 0
    passed: int = 0

    @property
    def drop_rate(self) -> float:
        if self.seen == 0:
            return 0.0
        return 1.0 - (self.passed / self.seen)


class LogSampler:
    """Samples log lines at a given rate (0.0 = drop all, 1.0 = keep all).

    Supports per-field-value sampling rates so high-volume keys can be
    sampled more aggressively than low-volume ones.
    """

    def __init__(self, default_rate: float = 1.0) -> None:
        if not (0.0 <= default_rate <= 1.0):
            raise ValueError(f"default_rate must be in [0, 1], got {default_rate}")
        self._default_rate = default_rate
        self._field_rates: Dict[str, Dict[str, float]] = {}
        self._stats: Dict[str, SamplerStats] = {}

    def set_field_rate(self, field: str, value: str, rate: float) -> None:
        """Override sampling rate for a specific field=value pair."""
        if not (0.0 <= rate <= 1.0):
            raise ValueError(f"rate must be in [0, 1], got {rate}")
        self._field_rates.setdefault(field, {})[value] = rate

    def _resolve_rate(self, record: dict) -> float:
        for field, value_map in self._field_rates.items():
            val = str(record.get(field, ""))
            if val in value_map:
                return value_map[val]
        return self._default_rate

    def should_keep(self, record: dict) -> bool:
        """Return True if the record should be forwarded downstream."""
        key = self._stat_key(record)
        stats = self._stats.setdefault(key, SamplerStats())
        stats.seen += 1
        rate = self._resolve_rate(record)
        keep = random.random() < rate
        if keep:
            stats.passed += 1
        return keep

    def _stat_key(self, record: dict) -> str:
        for field in self._field_rates:
            val = record.get(field)
            if val is not None:
                return f"{field}={val}"
        return "__default__"

    def stats(self) -> Dict[str, SamplerStats]:
        return dict(self._stats)
