"""Unit tests for measurement-input validation.

Three input paths share validation.validate_measurement(): the
record_measurement service, the dashboard number entity, and the storage
layer. These tests pin down the contract so a regression in any of the
three would surface here.
"""
from __future__ import annotations

import math

import pytest

from custom_components.kr_baby_kit.validation import (
    measurement_range,
    validate_measurement,
)


@pytest.mark.parametrize(
    ("kind", "value", "expected"),
    [
        ("height", 75.4, 75.4),
        ("height", "75.4", 75.4),  # service-call YAML may send strings
        ("height", 30.0, 30.0),    # lower bound inclusive
        ("height", 200.0, 200.0),  # upper bound inclusive
        ("weight", 9.2, 9.2),
        ("weight", 1.0, 1.0),
        ("weight", 100.0, 100.0),
        ("head", 46.0, 46.0),
        ("head", 25.0, 25.0),
        ("head", 65.0, 65.0),
    ],
)
def test_valid_values_pass_through(kind: str, value: object, expected: float) -> None:
    assert validate_measurement(kind, value) == expected


@pytest.mark.parametrize("bad", ["abc", "!!", "1.2.3", "1,2", ""])
def test_non_numeric_strings_rejected(bad: str) -> None:
    with pytest.raises(ValueError, match="숫자로 읽지 못했습니다"):
        validate_measurement("height", bad)


def test_none_rejected_with_korean_message() -> None:
    with pytest.raises(ValueError, match="비어 있습니다"):
        validate_measurement("height", None)


@pytest.mark.parametrize("bad", [True, False])
def test_booleans_rejected(bad: bool) -> None:
    # True / False would otherwise coerce silently to 1.0 / 0.0.
    with pytest.raises(ValueError, match="참/거짓 X"):
        validate_measurement("height", bad)


def test_nan_rejected() -> None:
    with pytest.raises(ValueError, match="NaN"):
        validate_measurement("weight", float("nan"))


def test_positive_infinity_rejected() -> None:
    with pytest.raises(ValueError, match="무한대"):
        validate_measurement("weight", math.inf)


def test_negative_infinity_rejected() -> None:
    with pytest.raises(ValueError, match="무한대"):
        validate_measurement("weight", -math.inf)


@pytest.mark.parametrize(
    ("kind", "bad"),
    [
        ("height", 29.9),    # below 30
        ("height", 200.01),  # above 200
        ("height", -5.0),    # negative
        ("height", 0.0),     # zero — outside the 30–200 band anyway
        ("weight", 0.5),     # below 1
        ("weight", 150.0),   # above 100
        ("weight", -2.0),
        ("head", 24.9),
        ("head", 65.5),
        ("head", -1.0),
    ],
)
def test_out_of_range_rejected(kind: str, bad: float) -> None:
    with pytest.raises(ValueError, match="허용 범위"):
        validate_measurement(kind, bad)


def test_unknown_kind_rejected() -> None:
    with pytest.raises(ValueError, match="알 수 없는 측정 항목"):
        validate_measurement("temperature", 36.5)


def test_measurement_range_exposed_for_schema_reuse() -> None:
    # The service-call schema in services.py reuses these bounds; pin them
    # down so a future widening / tightening forces an explicit test update.
    assert measurement_range("height") == (30.0, 200.0)
    assert measurement_range("weight") == (1.0, 100.0)
    assert measurement_range("head") == (25.0, 65.0)
