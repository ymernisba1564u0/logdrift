"""Formatting utilities for anomaly events and log summaries."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from logdrift.detector import AnomalyEvent


OUTPUT_FORMATS = ("text", "json", "jsonl")


def _ts(dt: datetime) -> str:
    """Return an ISO-8601 UTC timestamp string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat(timespec="seconds")


def format_anomaly(event: AnomalyEvent, fmt: str = "text") -> str:
    """Render an AnomalyEvent as a string in the requested format.

    Parameters
    ----------
    event:
        The anomaly event to format.
    fmt:
        One of ``'text'``, ``'json'``, or ``'jsonl'``.

    Returns
    -------
    str
        Formatted representation of *event*.
    """
    if fmt not in OUTPUT_FORMATS:
        raise ValueError(f"Unknown format {fmt!r}. Choose from {OUTPUT_FORMATS}.")

    if fmt == "text":
        return (
            f"[ANOMALY {_ts(event.timestamp)}] "
            f"rate={event.current_rate:.2f}/s  "
            f"baseline={event.baseline_rate:.2f}/s  "
            f"threshold={event.threshold:.2f}x"
        )

    payload: dict[str, Any] = {
        "anomaly": True,
        "timestamp": _ts(event.timestamp),
        "current_rate": round(event.current_rate, 4),
        "baseline_rate": round(event.baseline_rate, 4),
        "threshold": event.threshold,
    }
    return json.dumps(payload)


def format_summary(total_lines: int, anomaly_count: int, elapsed: float) -> str:
    """Return a human-readable summary line for end-of-session output."""
    rate = total_lines / elapsed if elapsed > 0 else 0.0
    return (
        f"Processed {total_lines} lines in {elapsed:.1f}s "
        f"({rate:.1f} lines/s) — {anomaly_count} anomaly/anomalies detected."
    )
