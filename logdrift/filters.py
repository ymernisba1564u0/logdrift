"""Log line filtering support for logdrift.

Allows users to restrict anomaly detection to log lines that match
specific field/value criteria (e.g. only watch lines where level=ERROR).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FieldFilter:
    """A single key=value filter applied to a parsed log record."""

    key: str
    value: str

    def matches(self, record: Dict[str, Any]) -> bool:
        """Return True when *record* contains key with the expected value."""
        return str(record.get(self.key, "")) == self.value


@dataclass
class FilterSet:
    """An ordered collection of :class:`FieldFilter` objects.

    A record must satisfy **all** filters to be considered a match
    (logical AND).
    """

    filters: List[FieldFilter] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_strings(cls, specs: List[str]) -> "FilterSet":
        """Build a :class:`FilterSet` from a list of ``"key=value"`` strings.

        Raises :class:`ValueError` for malformed specs.
        """
        filters: List[FieldFilter] = []
        for spec in specs:
            if "=" not in spec:
                raise ValueError(
                    f"Invalid filter spec {spec!r}: expected 'key=value' format"
                )
            key, _, value = spec.partition("=")
            if not key:
                raise ValueError(
                    f"Invalid filter spec {spec!r}: key must not be empty"
                )
            filters.append(FieldFilter(key=key, value=value))
        return cls(filters=filters)

    # ------------------------------------------------------------------
    # Runtime
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Return True when no filters are registered."""
        return len(self.filters) == 0

    def matches(self, record: Dict[str, Any]) -> bool:
        """Return True when *record* satisfies every registered filter."""
        return all(f.matches(record) for f in self.filters)

    def __repr__(self) -> str:  # pragma: no cover
        parts = ", ".join(f"{f.key}={f.value}" for f in self.filters)
        return f"FilterSet([{parts}])"
