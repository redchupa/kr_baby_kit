"""Tests for the user-facing percentile helpers added in v0.4.1.

Verifies the "top N%" inversion and the Korean one-line summary used by the
sensor's `top_percent` / `summary_ko` attributes.
"""
from __future__ import annotations

from custom_components.kr_baby_kit.growth import format_summary_ko, top_percent


def test_top_percent_inverts_statistical_percentile():
    # 94.7th percentile == top 5.3%
    assert top_percent(94.7) == 5.3
    assert top_percent(50.0) == 50.0
    assert top_percent(0.1) == 99.9


def test_top_percent_clamps_negative_to_zero():
    # 100th percentile is degenerate but must not produce a negative "top %".
    assert top_percent(100.0) == 0.0
    assert top_percent(110.0) == 0.0


def test_top_percent_returns_none_when_input_missing():
    assert top_percent(None) is None


def test_summary_uses_average_phrasing_around_median():
    assert format_summary_ko("height", 50.0) == "키: 또래 평균 (상위 50.0%)"
    assert format_summary_ko("weight", 47.0) == "몸무게: 또래 평균 (상위 53.0%)"


def test_summary_uses_top_phrasing_above_median():
    # 94.7th statistical percentile → top 5.3% phrasing
    assert format_summary_ko("height", 94.7) == "키: 또래 평균 상위 5.3%"


def test_summary_uses_bottom_phrasing_when_low():
    assert format_summary_ko("weight", 12.5) == "몸무게: 또래 평균 하위 12.5%"


def test_summary_for_bmi_and_weight_for_length_labels():
    assert format_summary_ko("bmi", 80.0).startswith("BMI:")
    assert format_summary_ko("weight_for_length", 33.1).startswith("신장별 몸무게:")


def test_summary_none_when_no_percentile():
    assert format_summary_ko("height", None) is None
