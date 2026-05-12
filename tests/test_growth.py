"""Unit tests for LMS growth percentile calculation.

Synthetic fixtures only — no real child data.
"""
from __future__ import annotations


import pytest

from custom_components.kr_baby_kit.growth import (
    GrowthChart,
    _lms_z,
    _normal_cdf,
    age_months,
)


@pytest.fixture(scope="module")
def chart() -> GrowthChart:
    return GrowthChart.from_default()


def test_chart_loads_male_height(chart: GrowthChart) -> None:
    assert chart.has("male", "height")
    point = chart.lookup("male", "height", 12)
    assert point is not None
    assert point.M > 0


def test_chart_loads_female_weight(chart: GrowthChart) -> None:
    assert chart.has("female", "weight")
    point = chart.lookup("female", "weight", 6)
    assert point.M == pytest.approx(7.297, rel=1e-3)


def test_interpolation_between_age_points() -> None:
    # Sparse synthetic table to exercise the linear interpolation branch.
    sparse = GrowthChart(
        {
            "samples": {
                "male": {
                    "height": [
                        {"age_months": 0, "L": 1.0, "M": 50.0, "S": 0.04},
                        {"age_months": 12, "L": 1.0, "M": 75.0, "S": 0.04},
                    ]
                }
            }
        }
    )
    p = sparse.lookup("male", "height", 6)
    assert p.M == pytest.approx((50.0 + 75.0) / 2, rel=1e-9)


def test_z_score_at_median_is_zero(chart: GrowthChart) -> None:
    point = chart.lookup("male", "height", 24)
    z = _lms_z(point.M, point.L, point.M, point.S)
    assert z == pytest.approx(0.0, abs=1e-9)


def test_percentile_at_median_is_50(chart: GrowthChart) -> None:
    point = chart.lookup("male", "weight", 12)
    z, pct = chart.percentile("male", "weight", 12, point.M)
    assert pct == pytest.approx(50.0, abs=0.5)


def test_percentile_higher_value_means_higher_percentile(chart: GrowthChart) -> None:
    _, low = chart.percentile("male", "weight", 12, 7.5)
    _, mid = chart.percentile("male", "weight", 12, 9.6)
    _, high = chart.percentile("male", "weight", 12, 12.0)
    assert low < mid < high


def test_normal_cdf_known_values() -> None:
    assert _normal_cdf(0.0) == pytest.approx(0.5)
    assert _normal_cdf(1.0) == pytest.approx(0.8413, abs=1e-3)
    assert _normal_cdf(-1.0) == pytest.approx(0.1587, abs=1e-3)


def test_age_months_basic() -> None:
    assert age_months("2020-01-01", "2021-01-01") == pytest.approx(12.0, abs=0.1)
    assert age_months("2020-01-01", "2020-07-01") == pytest.approx(6.0, abs=0.1)


def test_lookup_below_table_returns_first(chart: GrowthChart) -> None:
    p_neg = chart.lookup("male", "height", -5)
    p_zero = chart.lookup("male", "height", 0)
    assert p_neg.M == p_zero.M


def test_lookup_above_table_returns_last(chart: GrowthChart) -> None:
    # Table extends to ~228 months (19y). Anything past that should clamp to last.
    last = chart.lookup("male", "height", 228)
    way_above = chart.lookup("male", "height", 600)
    assert last.M == way_above.M


def test_unknown_sex_returns_none(chart: GrowthChart) -> None:
    assert chart.lookup("other", "height", 12) is None
    z, pct = chart.percentile("other", "height", 12, 75.0)
    assert z is None and pct is None


def test_bmi_table_starts_at_24_months(chart: GrowthChart) -> None:
    """KDCA only defines BMI from 24 months onward — under 2y must use
    weight-for-length instead. The lookup clamps below the table; the
    coordinator is responsible for skipping BMI under 24 months."""
    assert chart.has("male", "bmi")
    point = chart.lookup("male", "bmi", 24)
    assert point is not None
    assert point.M == pytest.approx(16.0189, rel=1e-4)


def test_bmi_percentile_at_median_is_50(chart: GrowthChart) -> None:
    point = chart.lookup("female", "bmi", 36)
    z, pct = chart.percentile("female", "bmi", 36, point.M)
    assert pct == pytest.approx(50.0, abs=0.5)
