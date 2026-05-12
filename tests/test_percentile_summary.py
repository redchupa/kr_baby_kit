"""Tests for the user-facing percentile helpers.

v0.7.0 split: height/weight follow the school-rank intuition (big raw value
→ small rank number), while head/BMI/weight-for-length are bi-directional
metrics, so their sensor value stays as the KDCA statistical percentile and
50 means "normal".
"""
from __future__ import annotations

from custom_components.kr_baby_kit.growth import (
    format_summary_ko,
    rank_percent,
    top_percent,
)


def test_top_percent_still_inverts_statistical_percentile():
    # Kept as a backward-compat attribute even when the sensor value diverges
    # for bi-directional metrics.
    assert top_percent(94.7) == 5.3
    assert top_percent(50.0) == 50.0
    assert top_percent(0.1) == 99.9


def test_top_percent_clamps_negative_to_zero():
    assert top_percent(100.0) == 0.0
    assert top_percent(110.0) == 0.0


def test_top_percent_returns_none_when_input_missing():
    assert top_percent(None) is None


def test_rank_percent_inverts_for_favors_high_metrics():
    # height / weight: bigger raw value should map to a smaller rank number.
    assert rank_percent("height", 94.7) == 5.3
    assert rank_percent("weight", 12.5) == 87.5


def test_rank_percent_passthrough_for_bidirectional_metrics():
    # head / bmi / weight_for_length: sensor value stays as the statistical
    # percentile so 50 means normal and both ends are clinical signals.
    assert rank_percent("head", 50.0) == 50.0
    assert rank_percent("head", 3.0) == 3.0
    assert rank_percent("head", 97.0) == 97.0
    assert rank_percent("bmi", 80.0) == 80.0
    assert rank_percent("weight_for_length", 33.1) == 33.1


def test_rank_percent_none_when_input_missing():
    assert rank_percent("height", None) is None
    assert rank_percent("head", None) is None


def test_summary_favors_high_metrics_use_rank_phrasing():
    assert format_summary_ko("height", 94.7) == "키: 또래 상위 5.3% (큰 편)"
    assert format_summary_ko("height", 12.5) == "키: 또래 상위 87.5% (작은 편)"
    assert format_summary_ko("height", 50.0) == "키: 또래 평균 수준"
    assert format_summary_ko("weight", 80.0) == "몸무게: 또래 상위 20.0% (많이 나가는 편)"


def test_summary_head_uses_bidirectional_phrasing_with_normal_band():
    # 50 → normal band; both ends carry a 진료 참고 nudge below 5 / above 95.
    assert format_summary_ko("head", 50.0) == "머리둘레: 또래 평균 수준 (정상 범위)"
    assert format_summary_ko("head", 97.0) == "머리둘레: 또래 상위 3.0% (큰 편, 진료 참고)"
    assert format_summary_ko("head", 3.0) == "머리둘레: 또래 하위 3.0% (작은 편, 진료 참고)"
    # Inside the normal band but off-center → adjective without the nudge.
    assert format_summary_ko("head", 80.0) == "머리둘레: 또래 상위 20.0% (큰 편)"
    assert format_summary_ko("head", 20.0) == "머리둘레: 또래 하위 20.0% (작은 편)"


def test_summary_bmi_and_weight_for_length_use_bidirectional_phrasing():
    assert format_summary_ko("bmi", 96.0) == "BMI: 또래 상위 4.0% (큰 편, 진료 참고)"
    assert format_summary_ko("bmi", 4.0) == "BMI: 또래 하위 4.0% (작은 편, 진료 참고)"
    assert format_summary_ko("bmi", 50.0) == "BMI: 또래 평균 수준 (정상 범위)"
    assert format_summary_ko("weight_for_length", 33.1) == (
        "신장별 몸무게: 또래 하위 33.1% (적게 나가는 편)"
    )


def test_summary_none_when_no_percentile():
    assert format_summary_ko("height", None) is None
    assert format_summary_ko("head", None) is None
