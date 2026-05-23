"""Tests for logdrift.tailer and its integration with AnomalyDetector."""

import io
import json
from unittest.mock import MagicMock, patch

import pytest

from logdrift.detector import AnomalyDetector
from logdrift.tailer import LogTailer, parse_log_line


# ---------------------------------------------------------------------------
# parse_log_line
# ---------------------------------------------------------------------------

def test_parse_valid_json():
    result = parse_log_line('{"event": "login", "user": "alice"}')
    assert result == {"event": "login", "user": "alice"}


def test_parse_invalid_json_returns_none():
    assert parse_log_line("not json at all") is None


def test_parse_empty_string_returns_none():
    assert parse_log_line("") is None


def test_parse_whitespace_only_returns_none():
    """Whitespace-only input should be treated the same as an empty string."""
    assert parse_log_line("   ") is None


# ---------------------------------------------------------------------------
# LogTailer.process_line
# ---------------------------------------------------------------------------

def _make_tailer(window=60, threshold=3.0, key_field="event"):
    detector = AnomalyDetector(window_seconds=window, threshold=threshold)
    on_anomaly = MagicMock()
    tailer = LogTailer(detector, on_anomaly=on_anomaly, key_field=key_field)
    return tailer, on_anomaly


def test_process_valid_line_increments_counter():
    tailer, _ = _make_tailer()
    tailer.process_line(json.dumps({"event": "login"}))
    assert tailer.stats["lines_read"] == 1
    assert tailer.stats["parse_errors"] == 0


def test_process_invalid_line_increments_parse_errors():
    tailer, _ = _make_tailer()
    tailer.process_line("garbage")
    assert tailer.stats["parse_errors"] == 1
    assert tailer.stats["lines_read"] == 0


def test_missing_key_field_uses_unknown():
    tailer, on_anomaly = _make_tailer()
    # Should not raise even when key_field is absent
    tailer.process_line(json.dumps({"level": "info"}))
    assert tailer.stats["lines_read"] == 1


def test_anomaly_callback_called_on_spike():
    tailer, on_anomaly = _make_tailer(window=60, threshold=2.0)
    # Warm up baseline
    for _ in range(20):
        tailer.process_line(json.dumps({"event": "login"}))
    on_anomaly.reset_mock()

    # Simulate a spike by patching detector.observe to return a fake anomaly
    from logdrift.detector import AnomalyEvent
    fake_event = AnomalyEvent(key="login", current_rate=50.0, baseline_rate=5.0, threshold=2.0)
    with patch.object(tailer.detector, "observe", return_value=fake_event):
        tailer.process_line(json.dumps({"event": "login"}))

    on_anomaly.assert_called_once_with(fake_event)


def test_no_anomaly_callback_not_called_without_spike():
    """on_anomaly should not be invoked when detector.observe returns None."""
    tailer, on_anomaly = _make_tailer()
    with patch.object(tailer.detector, "observe", return_value=None):
        tailer.process_line(json.dumps({"event": "login"}))
    on_anomaly.assert_not_called()


def test_custom_key_field():
    tailer, _ = _make_tailer(key_field="action")
    tailer.process_line(json.dumps({"action": "logout", "user": "bob"}))
    assert tailer.stats["lines_read"] == 1
