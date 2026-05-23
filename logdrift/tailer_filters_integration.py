"""Integration helpers that wire :class:`FilterSet` into :class:`LogTailer`.

This module provides :func:`make_filtered_tailer`, a convenience factory
that builds a :class:`~logdrift.tailer.LogTailer` whose ``process_line``
method silently skips records that do not satisfy the supplied filters.
"""

from __future__ import annotations

from typing import List, Optional

from logdrift.detector import AnomalyDetector
from logdrift.filters import FilterSet
from logdrift.tailer import LogTailer


class FilteredLogTailer(LogTailer):
    """A :class:`LogTailer` that pre-filters records before detection."""

    def __init__(
        self,
        detector: AnomalyDetector,
        filter_set: FilterSet,
        timestamp_key: str = "timestamp",
    ) -> None:
        super().__init__(detector=detector, timestamp_key=timestamp_key)
        self._filter_set = filter_set

    # ------------------------------------------------------------------
    # Override
    # ------------------------------------------------------------------

    def process_line(self, line: str) -> Optional[object]:
        """Parse *line*, apply filters, then delegate to the detector.

        Returns the :class:`~logdrift.detector.AnomalyEvent` produced by
        the parent implementation, or ``None`` when the line is skipped.
        """
        from logdrift.tailer import parse_log_line

        record = parse_log_line(line)
        if record is None:
            return None

        if not self._filter_set.matches(record):
            return None  # silently skip non-matching records

        # Re-use parent logic by passing the already-parsed record directly
        # through the internal observe path.
        ts = record.get(self._timestamp_key)
        if ts is None:
            return None

        self._line_count += 1
        return self._detector.observe(ts)


def make_filtered_tailer(
    detector: AnomalyDetector,
    filter_specs: List[str],
    timestamp_key: str = "timestamp",
) -> FilteredLogTailer:
    """Factory that builds a :class:`FilteredLogTailer` from CLI-style specs.

    Parameters
    ----------
    detector:
        An already-configured :class:`~logdrift.detector.AnomalyDetector`.
    filter_specs:
        A list of ``"key=value"`` strings (may be empty).
    timestamp_key:
        JSON key used to extract the event timestamp.
    """
    filter_set = FilterSet.from_strings(filter_specs)
    return FilteredLogTailer(
        detector=detector,
        filter_set=filter_set,
        timestamp_key=timestamp_key,
    )
