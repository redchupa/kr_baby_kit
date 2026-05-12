"""Tests for the user-facing percentile helpers.

Verifies the `top_percent` inverter (kept for power users / dashboards) and
the v0.5.0 Korean summary that uses the raw percentile so on-screen numbers
match the sensor's native value.
"""
from __future__ import annotations

from custom_components.kr_baby_kit.growth import format_summary_ko, top_percent


def test_top_percent_inverts_statistical_percentile():
    assert top_percent(94.7) == 5.3
    assert top_percent(50.0) == 50.0
    assert top_percent(0.1) == 99.9


def test_top_percent_clamps_negative_to_zero():
    assert top_percent(100.0) == 0.0
    assert top_percent(110.0) == 0.0


def test_top_percent_returns_none_when_input_missing():
    assert top_percent(None) is None


def test_summary_uses_average_phrasing_around_median():
    assert format_summary_ko("height", 50.0) == "키: 또래 평균 수준 (백분위 50.0)"
    assert format_summary_ko("weight", 47.0) == "몸무게: 또래 평균 수준 (백분위 47.0)"


def test_summary_above_median_uses_label_specific_high_adjective():
    assert format_summary_ko("height", 94.7) == "키: 또래보다 큰 편 (백분위 94.7)"
    assert format_summary_ko("weight", 80.0) == "몸무게: 또래보다 많이 나가는 편 (백분위 80.0)"
    assert format_summary_ko("head", 88.0) == "머리둘레: 또래보다 큰 편 (백분위 88.0)"
    assert format_summary_ko("bmi", 70.0) == "BMI: 또래보다 큰 편 (백분위 70.0)"


def test_summary_below_median_uses_label_specific_low_adjective():
    assert format_summary_ko("weight", 12.5) == "몸무게: 또래보다 적게 나가는 편 (백분위 12.5)"
    assert format_summary_ko("height", 5.0) == "키: 또래보다 작은 편 (백분위 5.0)"
    assert format_summary_ko("weight_for_length", 33.1) == (
        "신장별 몸무게: 또래보다 적게 나가는 편 (백분위 33.1)"
    )


def test_summary_for_bmi_and_weight_for_length_labels():
    assert format_summary_ko("bmi", 80.0).startswith("BMI:")
    assert format_summary_ko("weight_for_length", 33.1).startswith("신장별 몸무게:")


def test_summary_none_when_no_percentile():
    assert format_summary_ko("height", None) is None


def test_summary_number_always_matches_raw_percentile():
    # Regression: prior versions emitted "상위 5.3%" for a 94.7th percentile,
    # which made the summary number diverge from the sensor's native value.
    for pct in (5.0, 12.5, 50.0, 80.0, 94.7):
        summary = format_summary_ko("height", pct)
        assert f"백분위 {pct}" in summary, summary
