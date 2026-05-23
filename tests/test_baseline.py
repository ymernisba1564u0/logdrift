"""Tests for the rolling baseline window."""

import pytest
from logdrift.baseline import BaselineWindow


def test_count_empty_window():
    bw = BaselineWindow(window_seconds=60)
    assert bw.count("error", timestamp=1000.0) == 0


def test_count_single_event():
    bw = BaselineWindow(window_seconds=60)
    bw.record("error", timestamp=1000.0)
    assert bw.count("error", timestamp=1000.0) == 1


def test_count_multiple_events_same_second():
    bw = BaselineWindow(window_seconds=60)
    for _ in range(5):
        bw.record("error", timestamp=1000.0)
    assert bw.count("error", timestamp=1000.0) == 5


def test_eviction_removes_old_events():
    bw = BaselineWindow(window_seconds=10)
    bw.record("error", timestamp=1000.0)
    bw.record("error", timestamp=1001.0)
    # Query well past the window
    assert bw.count("error", timestamp=1015.0) == 0


def test_partial_eviction_keeps_recent_events():
    bw = BaselineWindow(window_seconds=10)
    bw.record("error", timestamp=1000.0)
    bw.record("error", timestamp=1008.0)
    # At t=1012, only the t=1008 event should remain
    assert bw.count("error", timestamp=1012.0) == 1


def test_rate_calculation():
    bw = BaselineWindow(window_seconds=10)
    for i in range(10):
        bw.record("warn", timestamp=float(1000 + i))
    rate = bw.rate("warn", timestamp=1009.0)
    assert rate == pytest.approx(10 / 10, rel=1e-3)


def test_independent_keys():
    bw = BaselineWindow(window_seconds=60)
    bw.record("error", timestamp=1000.0)
    bw.record("warn", timestamp=1000.0)
    bw.record("warn", timestamp=1001.0)
    assert bw.count("error", timestamp=1001.0) == 1
    assert bw.count("warn", timestamp=1001.0) == 2
