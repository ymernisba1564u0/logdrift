"""Tests for LogSampler and SampledLogTailer."""

import json
import pytest
from unittest.mock import MagicMock

from logdrift.sampler import LogSampler, SamplerStats
from logdrift.sampled_tailer import SampledLogTailer, make_sampled_tailer


# ---------------------------------------------------------------------------
# LogSampler unit tests
# ---------------------------------------------------------------------------

def test_default_rate_one_keeps_all():
    sampler = LogSampler(default_rate=1.0)
    record = {"level": "info", "msg": "hello"}
    assert all(sampler.should_keep(record) for _ in range(50))


def test_default_rate_zero_drops_all():
    sampler = LogSampler(default_rate=0.0)
    record = {"level": "info", "msg": "hello"}
    assert not any(sampler.should_keep(record) for _ in range(50))


def test_invalid_rate_raises():
    with pytest.raises(ValueError):
        LogSampler(default_rate=1.5)


def test_set_field_rate_invalid_raises():
    sampler = LogSampler()
    with pytest.raises(ValueError):
        sampler.set_field_rate("level", "debug", -0.1)


def test_field_rate_overrides_default():
    sampler = LogSampler(default_rate=1.0)
    sampler.set_field_rate("level", "debug", 0.0)
    debug_record = {"level": "debug", "msg": "verbose"}
    info_record = {"level": "info", "msg": "important"}
    assert not any(sampler.should_keep(debug_record) for _ in range(30))
    assert all(sampler.should_keep(info_record) for _ in range(30))


def test_stats_track_seen_and_passed():
    sampler = LogSampler(default_rate=1.0)
    record = {"level": "info"}
    for _ in range(10):
        sampler.should_keep(record)
    stats = sampler.stats()
    entry: SamplerStats = stats["__default__"]
    assert entry.seen == 10
    assert entry.passed == 10
    assert entry.drop_rate == 0.0


def test_drop_rate_zero_when_no_events():
    stats = SamplerStats()
    assert stats.drop_rate == 0.0


# ---------------------------------------------------------------------------
# SampledLogTailer integration tests
# ---------------------------------------------------------------------------

def _line(record: dict) -> str:
    return json.dumps(record)


def _make_sampled(rate: float) -> SampledLogTailer:
    tailer = MagicMock()
    tailer.process_line = MagicMock()
    sampler = LogSampler(default_rate=rate)
    return SampledLogTailer(tailer, sampler)


def test_sampled_tailer_keeps_all_at_rate_one():
    st = _make_sampled(1.0)
    for _ in range(10):
        result = st.process_line(_line({"msg": "hi"}))
        assert result is not None
    assert st.forwarded == 10
    assert st.dropped == 0


def test_sampled_tailer_drops_all_at_rate_zero():
    st = _make_sampled(0.0)
    for _ in range(10):
        result = st.process_line(_line({"msg": "hi"}))
        assert result is None
    assert st.dropped == 10
    assert st.forwarded == 0


def test_sampled_tailer_invalid_json_returns_none():
    st = _make_sampled(1.0)
    assert st.process_line("not json") is None


def test_on_drop_callback_called():
    dropped = []
    tailer = MagicMock()
    sampler = LogSampler(default_rate=0.0)
    st = SampledLogTailer(tailer, sampler, on_drop=dropped.append)
    st.process_line(_line({"msg": "bye"}))
    assert len(dropped) == 1


def test_make_sampled_tailer_factory():
    tailer = MagicMock()
    st = make_sampled_tailer(
        tailer,
        default_rate=1.0,
        field_rates={"level": {"debug": 0.0}},
    )
    assert st.process_line(_line({"level": "debug", "msg": "x"})) is None
    assert st.process_line(_line({"level": "info", "msg": "y"})) is not None
