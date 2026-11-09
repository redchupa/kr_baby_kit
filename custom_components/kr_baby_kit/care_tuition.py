"""Childcare tuition lookup against the bundled 보건복지부 표준보육료 table.

The table groups children into age classes (`만 N세반`) by completed years of
age. Each tier records the standard tuition (표준보육료), the government
subsidy (정부지원금), and the parent's out-of-pocket share (본인부담금).

Numeric values ship as placeholders (`0`) and `data_year: 0`. Replace them
with the latest 보건복지부 고시 before publishing — schema is stable.

Public API:
    load_tuition_table(path=None) -> dict
    age_class_for_birthdate(birthdate, on) -> int | None
    tuition_for_birthdate(birthdate, on, table=None) -> TuitionTier | None
    tuition_for_age_months(age_months, table=None) -> TuitionTier | None  (legacy)
    is_placeholder(table) -> bool

Age class rule (v0.9.1): 보육료 지원 연령반 is decided by **birth year**, not by
months of age. In year Y, 만 0세반 covers children born on/after Y-1-01-01
(including babies born in Y), 만 1세반 = born in Y-2, ..., 만 5세반 = born in
Y-6, 만 6세반 (취학유예 only) = born in Y-7. I.e. class = max(0, Y - birth_year - 1).
Source: 「2026년도 보육사업안내」 보육료 지원 기준 연령 산정 기준일자 (찾기쉬운
생활법령정보 「어린이집 보육료 지원」).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
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


async def async_load_tuition_table(
    hass, path: Path | None = None
) -> dict[str, Any]:
    """Async variant safe to call from the HA event loop."""
    return await hass.async_add_executor_job(load_tuition_table, path)


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


def age_class_for_birthdate(birthdate: date, on: date) -> int | None:
    """Daycare age class (만 N세반) in the calendar year of ``on``.

    Returns None before birth or once the child is past 만 6세반 (school age).
    """
    if birthdate > on:
        return None
    age_class = max(0, on.year - birthdate.year - 1)
    if age_class > 6:
        return None
    return age_class


def tuition_for_birthdate(
    birthdate: date,
    on: date,
    table: dict[str, Any] | None = None,
) -> TuitionTier | None:
    """Tier for the child's birth-year based age class in the year of ``on``."""
    age_class = age_class_for_birthdate(birthdate, on)
    if age_class is None:
        return None
    src = table if table is not None else load_tuition_table()
    for tier in src.get("tiers") or []:
        if int(tier.get("age_class", -1)) == age_class:
            return _tier_from(tier, src)
    return None


def _tier_from(tier: dict[str, Any], src: dict[str, Any]) -> TuitionTier:
    meta = src.get("_meta") or {}
    return TuitionTier(
        age_class=int(tier.get("age_class", 0)),
        label_ko=str(tier.get("label_ko", "")),
        label_en=str(tier.get("label_en", "")),
        age_months_min=int(tier.get("age_months_min", 0)),
        age_months_max=int(tier.get("age_months_max", -1)),
        standard_tuition=int(tier.get("standard_tuition") or 0),
        government_subsidy=int(tier.get("government_subsidy") or 0),
        parent_share=int(tier.get("parent_share") or 0),
        data_year=int(meta.get("data_year") or 0),
        source_url=str(meta.get("source_url") or ""),
        is_placeholder=is_placeholder(src),
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
    "age_class_for_birthdate",
    "tuition_for_birthdate",
    "load_tuition_table",
    "async_load_tuition_table",
    "is_placeholder",
    "tuition_for_age_months",
]
