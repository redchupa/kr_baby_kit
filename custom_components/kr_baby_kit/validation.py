"""Measurement input validation.

A single source of truth for what counts as a plausible 키/몸무게/머리둘레
reading. Every entry point (service call, dashboard number entity, storage
layer) routes through these helpers so a bad number can't sneak in via one
path and trash the percentile calculations downstream.

Error messages are Korean — they surface in the HA UI when a service call
fails, so they need to read naturally for the dashboard user.
"""
from __future__ import annotations

import math
from typing import Final


# Plausible measurement ranges. Chosen wider than the KDCA 0–228 month chart
# itself (45–180 cm height, 3–80 kg weight, 33–58 cm head circumference) so
# a one-off entry slightly outside the chart still gets stored — percentile
# computation gracefully degrades to None outside the LMS table — but
# clearly-mistyped values (e.g. weight in grams, height in inches) are
# rejected up front.
_MEASUREMENT_RANGES: Final[dict[str, tuple[float, float]]] = {
    "height": (30.0, 200.0),   # cm
    "weight": (1.0, 100.0),    # kg
    "head": (25.0, 65.0),      # cm
}

_LABELS_KO: Final[dict[str, str]] = {
    "height": "키",
    "weight": "몸무게",
    "head": "머리둘레",
}

_UNITS: Final[dict[str, str]] = {
    "height": "cm",
    "weight": "kg",
    "head": "cm",
}


def _label(kind: str) -> str:
    return _LABELS_KO.get(kind, kind)


def _unit(kind: str) -> str:
    return _UNITS.get(kind, "")


def measurement_range(kind: str) -> tuple[float, float]:
    """Public accessor so schema builders can share the same bounds."""
    return _MEASUREMENT_RANGES[kind]


def validate_measurement(kind: str, value: object) -> float:
    """Coerce ``value`` to a plausible measurement float or raise ``ValueError``.

    The Korean error message is intentionally user-facing — it shows up in
    the HA notifications panel when a service call fails. Callers should let
    the exception propagate (or wrap with ``HomeAssistantError``) rather
    than catching it.
    """
    if kind not in _MEASUREMENT_RANGES:
        raise ValueError(f"알 수 없는 측정 항목: {kind!r}")

    if value is None:
        raise ValueError(f"{_label(kind)} 값이 비어 있습니다.")

    # bool is a subtype of int; explicitly reject it to avoid True being
    # silently coerced to 1.0.
    if isinstance(value, bool):
        raise ValueError(f"{_label(kind)} 값은 숫자여야 합니다 (참/거짓 X).")

    try:
        v = float(value)
    except (TypeError, ValueError) as err:
        raise ValueError(
            f"{_label(kind)} 값을 숫자로 읽지 못했습니다: {value!r}"
        ) from err

    if math.isnan(v):
        raise ValueError(f"{_label(kind)} 값이 NaN 입니다.")
    if math.isinf(v):
        raise ValueError(f"{_label(kind)} 값이 무한대입니다.")

    lo, hi = _MEASUREMENT_RANGES[kind]
    if v < lo or v > hi:
        raise ValueError(
            f"{_label(kind)} 값이 허용 범위를 벗어났습니다: "
            f"{v} {_unit(kind)} (허용: {lo}–{hi} {_unit(kind)})."
        )

    return v
