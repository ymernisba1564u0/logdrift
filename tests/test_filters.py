"""Tests for logdrift.filters."""

import pytest

from logdrift.filters import FieldFilter, FilterSet


# ---------------------------------------------------------------------------
# FieldFilter
# ---------------------------------------------------------------------------


def test_field_filter_matches_exact_value():
    f = FieldFilter(key="level", value="ERROR")
    assert f.matches({"level": "ERROR", "msg": "boom"})


def test_field_filter_no_match_wrong_value():
    f = FieldFilter(key="level", value="ERROR")
    assert not f.matches({"level": "INFO", "msg": "ok"})


def test_field_filter_no_match_missing_key():
    f = FieldFilter(key="level", value="ERROR")
    assert not f.matches({"msg": "no level here"})


def test_field_filter_coerces_value_to_str():
    """Numeric JSON values should still match when compared as strings."""
    f = FieldFilter(key="code", value="404")
    assert f.matches({"code": 404})


# ---------------------------------------------------------------------------
# FilterSet.from_strings
# ---------------------------------------------------------------------------


def test_from_strings_single():
    fs = FilterSet.from_strings(["level=ERROR"])
    assert len(fs.filters) == 1
    assert fs.filters[0].key == "level"
    assert fs.filters[0].value == "ERROR"


def test_from_strings_multiple():
    fs = FilterSet.from_strings(["level=ERROR", "service=auth"])
    assert len(fs.filters) == 2


def test_from_strings_empty_list():
    fs = FilterSet.from_strings([])
    assert fs.is_empty()


def test_from_strings_invalid_spec_raises():
    with pytest.raises(ValueError, match="key=value"):
        FilterSet.from_strings(["no-equals-sign"])


def test_from_strings_empty_key_raises():
    with pytest.raises(ValueError, match="key must not be empty"):
        FilterSet.from_strings(["=value"])


# ---------------------------------------------------------------------------
# FilterSet.matches
# ---------------------------------------------------------------------------


def test_filterset_empty_matches_everything():
    fs = FilterSet.from_strings([])
    assert fs.matches({})
    assert fs.matches({"level": "DEBUG"})


def test_filterset_all_conditions_must_match():
    fs = FilterSet.from_strings(["level=ERROR", "service=auth"])
    assert fs.matches({"level": "ERROR", "service": "auth"})
    assert not fs.matches({"level": "ERROR", "service": "web"})
    assert not fs.matches({"level": "INFO", "service": "auth"})


def test_filterset_value_with_equals_sign():
    """Values that themselves contain '=' should be handled correctly."""
    fs = FilterSet.from_strings(["msg=a=b"])
    assert fs.matches({"msg": "a=b"})
    assert not fs.matches({"msg": "a"})
