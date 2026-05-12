"""Tests for the user-facing percentile helpers.

v0.6.0: the user-facing number is the *rank* (``100 - statistical_percentile``),
so a tall child reads a small number and a small child reads a large number,
matching the user's school-ranking intuition. The KDCA statistical percentile
remains available as a separate attribute (`statistical_percentile`).
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
    assert format_summary_ko("height", 50.0) == "키: 또래 평균 수준"
    assert format_summary_ko("weight", 47.0) == "몸무게: 또래 평균 수준"


def test_summary_above_median_uses_high_adjective_with_small_rank_number():
    # Tall child → 94.7th statistical percentile → rank 5.3% → small number.
    assert format_summary_ko("height", 94.7) == "키: 또래 상위 5.3% (큰 편)"
    assert format_summary_ko("weight", 80.0) == "몸무게: 또래 상위 20.0% (많이 나가는 편)"
    assert format_summary_ko("head", 88.0) == "머리둘레: 또래 상위 12.0% (큰 편)"
    assert format_summary_ko("bmi", 70.0) == "BMI: 또래 상위 30.0% (큰 편)"


def test_summary_below_median_uses_low_adjective_with_large_rank_number():
    # Small child → 12.5th statistical percentile → rank 87.5% → large number,
    # signalling "ranked low among peers".
    assert format_summary_ko("weight", 12.5) == "몸무게: 또래 상위 87.5% (적게 나가는 편)"
    assert format_summary_ko("height", 5.0) == "키: 또래 상위 95.0% (작은 편)"
    assert format_summary_ko("weight_for_length", 33.1) == (
        "신장별 몸무게: 또래 상위 66.9% (적게 나가는 편)"
    )


def test_summary_for_bmi_and_weight_for_length_labels():
    assert format_summary_ko("bmi", 80.0).startswith("BMI:")
    assert format_summary_ko("weight_for_length", 33.1).startswith("신장별 몸무게:")


def test_summary_none_when_no_percentile():
    assert format_summary_ko("height", None) is None


def test_summary_number_matches_rank_percent():
    # Regression guard: the number in the summary must always be (100 - pct),
    # so the dashboard text agrees with the sensor's native value.
    for stat_pct in (5.0, 12.5, 80.0, 94.7):
        summary = format_summary_ko("height", stat_pct)
        expected_rank = round(100.0 - stat_pct, 1)
        assert f"또래 상위 {expected_rank}%" in summary, summary
