"""Unit tests for UI formatting helpers."""

from app.app_utils import format_count


def test_format_count_integers():
    """Verifies that integer values are formatted with thousands separators."""
    assert format_count(1000) == "1,000"
    assert format_count(101766) == "101,766"
    assert format_count(0) == "0"
    assert format_count(42) == "42"


def test_format_count_none_and_missing():
    """Verifies that None or sentinel missing values return N/A fallback."""
    assert format_count(None) == "N/A"
    assert format_count(None, fallback="Unknown") == "Unknown"


def test_format_count_invalid_types():
    """Verifies that non-numeric types return fallback."""
    assert format_count("invalid_number") == "N/A"
    assert format_count(float("nan")) == "N/A"
