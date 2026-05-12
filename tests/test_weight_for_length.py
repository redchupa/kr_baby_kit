"""Unit tests for weight-for-length percentile lookup."""
from __future__ import annotations

import pytest

from custom_components.kr_baby_kit.growth import GrowthChart, _wfl_band


@pytest.fixture(scope="module")
def chart() -> GrowthChart:
    return GrowthChart.from_default()


@pytest.mark.parametrize(
    "age_m,expected",
    [
        (0, "under_2y"),
        (12, "under_2y"),
        (23.9, "under_2y"),
        (24, "age_2_to_3"),
        (30, "age_2_to_3"),
        (36, "age_3_plus"),
        (96, "age_3_plus"),
    ],
)
def test_wfl_band_selection(age_m: float, expected: str) -> None:
    assert _wfl_band(age_m) == expected


def test_data_includes_weight_for_length(chart: GrowthChart) -> None:
    assert chart.has_weight_for_length("male", 12)
    assert chart.has_weight_for_length("female", 30)
    assert chart.has_weight_for_length("male", 60)


def test_weight_at_median_is_50th_percentile(chart: GrowthChart) -> None:
    # For each band, evaluate at the median M and confirm ≈ 50th pct.
    samples = [
        ("male", 12, 75.0),     # under_2y
        ("female", 30, 90.0),   # age_2_to_3
        ("male", 60, 110.0),    # age_3_plus
    ]
    for sex, age_m, length in samples:
        z, pct, band = chart.weight_for_length_percentile(sex, age_m, length, 1.0)
        # Run a second pass with weight = median M from the same lookup.
        # We do not have direct M access here, so we bisect roughly:
        # pick a weight that yields ≈ 50% by trial.
        # Easier: re-derive M from a known point via internal API.
        from custom_components.kr_baby_kit.growth import _lookup
        points = chart._wfl[(sex, band)]
        # Find the LMS point exactly at this length (interpolating).
        p = _lookup(points, length)
        z2, pct2 = chart.weight_for_length_percentile(sex, age_m, length, p.M)[:2]
        assert pct2 == pytest.approx(50.0, abs=0.5)


def test_higher_weight_means_higher_percentile(chart: GrowthChart) -> None:
    _, low, _ = chart.weight_for_length_percentile("male", 12, 75.0, 8.0)
    _, mid, _ = chart.weight_for_length_percentile("male", 12, 75.0, 10.0)
    _, high, _ = chart.weight_for_length_percentile("male", 12, 75.0, 13.0)
    assert low < mid < high


def test_unsupported_age_returns_none(chart: GrowthChart) -> None:
    z, pct, band = chart.weight_for_length_percentile("male", -1, 50.0, 3.0)
    assert (z, pct, band) == (None, None, None)
