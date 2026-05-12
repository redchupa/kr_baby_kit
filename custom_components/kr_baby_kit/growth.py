"""LMS-based growth percentile calculation.

Implements the WHO/KDCA LMS reference method:
  Z = ((X / M) ^ L - 1) / (L * S)         when L != 0
  Z = ln(X / M) / S                       when L == 0

Then percentile = Φ(Z) where Φ is the standard normal CDF.

Data table layout (see data/growth_chart_kr.json):
  samples.{sex}.{kind}: list of {age_months, L, M, S}, sorted by age.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "growth_chart_kr.json"


@dataclass(frozen=True)
class LMSPoint:
    """LMS triple keyed by an arbitrary x-axis (age_months or length_cm)."""

    x: float
    L: float
    M: float
    S: float


# Weight-for-length bands keyed by age_months range [min, max).
_WFL_BANDS: tuple[tuple[str, float, float], ...] = (
    ("under_2y", 0.0, 24.0),
    ("age_2_to_3", 24.0, 36.0),
    ("age_3_plus", 36.0, float("inf")),
)


class GrowthChart:
    """LMS lookup with linear interpolation.

    - `lookup(sex, kind, age_months)` / `percentile(...)`: age-indexed LMS
      for height, weight, head, bmi.
    - `weight_for_length_percentile(sex, age_months, length_cm, weight_kg)`:
      length-indexed weight LMS, selecting the band by age.
    """

    def __init__(self, raw: dict) -> None:
        self._raw = raw
        self._table: dict[tuple[str, str], list[LMSPoint]] = {}
        for sex, kinds in (raw.get("samples") or {}).items():
            for kind, rows in kinds.items():
                self._table[(sex, kind)] = sorted(
                    (
                        LMSPoint(
                            x=float(r["age_months"]),
                            L=float(r["L"]),
                            M=float(r["M"]),
                            S=float(r["S"]),
                        )
                        for r in rows
                    ),
                    key=lambda p: p.x,
                )
        self._wfl: dict[tuple[str, str], list[LMSPoint]] = {}
        for sex, bands in (raw.get("weight_for_length") or {}).items():
            for band, rows in bands.items():
                self._wfl[(sex, band)] = sorted(
                    (
                        LMSPoint(
                            x=float(r["length_cm"]),
                            L=float(r["L"]),
                            M=float(r["M"]),
                            S=float(r["S"]),
                        )
                        for r in rows
                    ),
                    key=lambda p: p.x,
                )

    @classmethod
    def from_default(cls) -> "GrowthChart":
        with _DATA_PATH.open(encoding="utf-8") as fh:
            return cls(json.load(fh))

    def has(self, sex: str, kind: str) -> bool:
        return (sex, kind) in self._table and bool(self._table[(sex, kind)])

    def has_weight_for_length(self, sex: str, age_months: float) -> bool:
        band = _wfl_band(age_months)
        return band is not None and bool(self._wfl.get((sex, band)))

    def lookup(self, sex: str, kind: str, age_months: float) -> LMSPoint | None:
        return _lookup(self._table.get((sex, kind)), age_months)

    def percentile(
        self, sex: str, kind: str, age_months: float, value: float
    ) -> tuple[float | None, float | None]:
        """Return (z_score, percentile_0_100) for an age-indexed measurement."""
        return _percentile_from(self._table.get((sex, kind)), age_months, value)

    def weight_for_length_percentile(
        self,
        sex: str,
        age_months: float,
        length_cm: float,
        weight_kg: float,
    ) -> tuple[float | None, float | None, str | None]:
        """Return (z_score, percentile, band_name).

        Selects the age-appropriate band (recumbent length <2y, standing height
        2y+) and interpolates the LMS curve on the length axis.
        """
        band = _wfl_band(age_months)
        if band is None:
            return None, None, None
        points = self._wfl.get((sex, band))
        z, pct = _percentile_from(points, length_cm, weight_kg)
        return z, pct, band


def _wfl_band(age_months: float) -> str | None:
    for name, lo, hi in _WFL_BANDS:
        if lo <= age_months < hi:
            return name
    return None


def _lookup(points: list[LMSPoint] | None, x: float) -> LMSPoint | None:
    if not points:
        return None
    if x <= points[0].x:
        return points[0]
    if x >= points[-1].x:
        return points[-1]
    for prev, nxt in zip(points, points[1:]):
        if prev.x <= x <= nxt.x:
            return _interpolate(prev, nxt, x)
    return points[-1]


def _percentile_from(
    points: list[LMSPoint] | None, x: float, value: float
) -> tuple[float | None, float | None]:
    point = _lookup(points, x)
    if point is None:
        return None, None
    z = _lms_z(value, point.L, point.M, point.S)
    if z is None:
        return None, None
    return z, _normal_cdf(z) * 100.0


def _interpolate(a: LMSPoint, b: LMSPoint, x: float) -> LMSPoint:
    span = b.x - a.x
    if span <= 0:
        return a
    t = (x - a.x) / span
    return LMSPoint(
        x=x,
        L=a.L + (b.L - a.L) * t,
        M=a.M + (b.M - a.M) * t,
        S=a.S + (b.S - a.S) * t,
    )


def _lms_z(value: float, L: float, M: float, S: float) -> float | None:
    if value <= 0 or M <= 0 or S <= 0:
        return None
    if L == 0:
        return math.log(value / M) / S
    return ((value / M) ** L - 1.0) / (L * S)


def _normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def age_months(birthdate_iso: str, on_iso: str) -> float:
    """Return age in months (float) between two ISO dates."""
    from datetime import date

    bd = date.fromisoformat(birthdate_iso)
    on = date.fromisoformat(on_iso)
    days = (on - bd).days
    return days / 30.4375


_KIND_LABEL_KO: dict[str, str] = {
    "height": "키",
    "weight": "몸무게",
    "head": "머리둘레",
    "bmi": "BMI",
    "weight_for_length": "신장별 몸무게",
}


def top_percent(percentile: float | None) -> float | None:
    """Convert a statistical percentile to a user-facing "top N%" figure.

    A statistical 95th percentile means the child is at or above 95% of the
    reference population - i.e. top 5%. We round to one decimal so dashboards
    can format it as a stable string.

    Edge cases that are easy to misread:
      - percentile == 50 (median) → top 50% (the dashboard label still reads
        meaningfully as "around average")
      - percentile == 100 → top 0% (cap on the small side; the original 100
        only ever appears for synthetic test inputs)
    """
    if percentile is None:
        return None
    return round(max(0.0, 100.0 - float(percentile)), 1)


def format_summary_ko(kind: str, percentile: float | None) -> str | None:
    """One-line Korean summary suitable for a Lovelace card's secondary_info.

    Examples:
        format_summary_ko("height", 94.7) == "또래 평균 상위 5.3%"
        format_summary_ko("weight", 50.0) == "또래 평균 (상위 50.0%)"
        format_summary_ko("bmi", None) == None
    """
    if percentile is None:
        return None
    label = _KIND_LABEL_KO.get(kind, kind)
    top = top_percent(percentile) or 0.0
    if 45.0 <= percentile <= 55.0:
        return f"{label}: 또래 평균 (상위 {top}%)"
    if percentile > 55.0:
        return f"{label}: 또래 평균 상위 {top}%"
    # percentile < 45 → 하위에 위치
    bottom = round(float(percentile), 1)
    return f"{label}: 또래 평균 하위 {bottom}%"
