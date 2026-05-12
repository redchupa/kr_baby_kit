"""Childcare tuition lookup against the bundled 보건복지부 표준보육료 table.

The table groups children into age classes (`만 N세반`) by completed years of
age. Each tier records the standard tuition (표준보육료), the government
subsidy (정부지원금), and the parent's out-of-pocket share (본인부담금).

Numeric values ship as placeholders (`0`) and `data_year: 0`. Replace them
with the latest 보건복지부 고시 before publishing — schema is stable.

Public API:
    load_tuition_table(path=None) -> dict
    tuition_for_age_months(age_months, table=None) -> TuitionTier | None
    is_placeholder(table) -> bool
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_DATA_PATH = Path(__file__).parent / "data" / "care_tuition_kr.json"


@dataclass(frozen=True)
class TuitionTier:
    age_class: int
    label_ko: str
    label_en: str
    age_months_min: int
    age_months_max: int
    standard_tuition: int        # KRW
    government_subsidy: int      # KRW
    parent_share: int            # KRW
    data_year: int               # e.g. 2025; 0 indicates placeholder data
    source_url: str
    is_placeholder: bool


def load_tuition_table(path: Path | None = None) -> dict[str, Any]:
    """Load the bundled tuition JSON. Callers can override `path` for tests."""
    with (path or _DATA_PATH).open(encoding="utf-8") as fh:
        return json.load(fh)


def is_placeholder(table: dict[str, Any]) -> bool:
    """True when the table still holds the shipped zero-values."""
    meta = table.get("_meta") or {}
    if int(meta.get("data_year") or 0) == 0:
        return True
    # All-zero tiers also count as placeholder regardless of data_year.
    return all(
        (tier.get("standard_tuition") or 0) == 0
        and (tier.get("government_subsidy") or 0) == 0
        and (tier.get("parent_share") or 0) == 0
        for tier in table.get("tiers") or []
    )


def tuition_for_age_months(
    age_months: float,
    table: dict[str, Any] | None = None,
) -> TuitionTier | None:
    """Return the tier matching the given age in months, or None if out of range.

    Tiers are inclusive on both ends. The bundled table covers 0–83 months
    (만 0세 ~ 만 6세 미취학); children older than that fall through to None
    because elementary-school tuition is not part of the 보육료 system.

    Accepts a float age (the coordinator computes age in fractional months)
    and floors it to an integer month before tier matching, so an
    11.97-month-old still resolves to 만 0세반.
    """
    if age_months < 0:
        return None
    age_int = int(age_months)
    src = table if table is not None else load_tuition_table()
    meta = src.get("_meta") or {}
    data_year = int(meta.get("data_year") or 0)
    source_url = str(meta.get("source_url") or "")
    placeholder = is_placeholder(src)
    for tier in src.get("tiers") or []:
        amin = int(tier.get("age_months_min", 0))
        amax = int(tier.get("age_months_max", -1))
        if amin <= age_int <= amax:
            return TuitionTier(
                age_class=int(tier.get("age_class", 0)),
                label_ko=str(tier.get("label_ko", "")),
                label_en=str(tier.get("label_en", "")),
                age_months_min=amin,
                age_months_max=amax,
                standard_tuition=int(tier.get("standard_tuition") or 0),
                government_subsidy=int(tier.get("government_subsidy") or 0),
                parent_share=int(tier.get("parent_share") or 0),
                data_year=data_year,
                source_url=source_url,
                is_placeholder=placeholder,
            )
    return None


__all__ = [
    "TuitionTier",
    "load_tuition_table",
    "is_placeholder",
    "tuition_for_age_months",
]
