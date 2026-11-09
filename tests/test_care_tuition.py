"""Childcare tuition lookup table behavior."""
from __future__ import annotations

import json


from datetime import date

import pytest

from custom_components.kr_baby_kit.care_tuition import (
    age_class_for_birthdate,
    tuition_for_birthdate,
    is_placeholder,
    load_tuition_table,
    tuition_for_age_months,
)


def _table_with_real_values(tmp_path):
    """Write a non-placeholder table for tests that assert real values."""
    data = {
        "_meta": {
            "data_year": 2025,
            "source_url": "https://example.gov.kr/childcare",
            "currency": "KRW",
        },
        "tiers": [
            {
                "age_class": 0, "label_ko": "만 0세반", "label_en": "Age 0",
                "age_months_min": 0, "age_months_max": 11,
                "standard_tuition": 600000, "government_subsidy": 600000, "parent_share": 0,
            },
            {
                "age_class": 1, "label_ko": "만 1세반", "label_en": "Age 1",
                "age_months_min": 12, "age_months_max": 23,
                "standard_tuition": 530000, "government_subsidy": 530000, "parent_share": 0,
            },
            {
                "age_class": 3, "label_ko": "만 3세반", "label_en": "Age 3",
                "age_months_min": 36, "age_months_max": 47,
                "standard_tuition": 290000, "government_subsidy": 280000, "parent_share": 10000,
            },
        ],
    }
    p = tmp_path / "care_tuition.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return p, data


def test_bundled_table_has_all_seven_age_classes():
    """Schema regression: every 만 N세반 tier from 0 through 6 must exist."""
    table = load_tuition_table()
    classes = sorted(t["age_class"] for t in table["tiers"])
    assert classes == [0, 1, 2, 3, 4, 5, 6]


def test_bundled_table_carries_real_2026_values():
    """The repo bundles the 2026년도 보육사업안내 (교육부) figures.

    Re-running the check after each yearly update would change the
    `data_year` assertion below — that's intentional, this test is the
    canary that someone forgot to bump the metadata when refreshing the
    table.
    """
    table = load_tuition_table()
    assert not is_placeholder(table)
    assert table["_meta"]["data_year"] == 2026
    # Spot-check a value that the bundled table promises: 0세반 = 584,000원.
    tier = tuition_for_age_months(3, table)
    assert tier is not None and tier.standard_tuition == 584000


def test_lookup_picks_correct_tier(tmp_path):
    path, data = _table_with_real_values(tmp_path)
    src = json.loads(path.read_text(encoding="utf-8"))

    tier = tuition_for_age_months(0, src)
    assert tier and tier.age_class == 0
    tier = tuition_for_age_months(11, src)
    assert tier and tier.age_class == 0

    tier = tuition_for_age_months(12, src)
    assert tier and tier.age_class == 1

    tier = tuition_for_age_months(40, src)
    assert tier and tier.age_class == 3
    assert tier.standard_tuition == 290000
    assert tier.government_subsidy == 280000
    assert tier.parent_share == 10000
    assert tier.data_year == 2025
    assert tier.is_placeholder is False


def test_lookup_returns_none_for_unsupported_age(tmp_path):
    path, _ = _table_with_real_values(tmp_path)
    src = json.loads(path.read_text(encoding="utf-8"))
    # Outside the bundled fixture coverage (gap 24-35 + above 47).
    assert tuition_for_age_months(60, src) is None
    assert tuition_for_age_months(30, src) is None


def test_negative_age_returns_none():
    assert tuition_for_age_months(-1) is None


def test_is_placeholder_when_year_is_zero_even_with_real_values(tmp_path):
    data = {
        "_meta": {"data_year": 0},
        "tiers": [{
            "age_class": 0, "age_months_min": 0, "age_months_max": 11,
            "standard_tuition": 100, "government_subsidy": 100, "parent_share": 0,
            "label_ko": "x", "label_en": "x",
        }],
    }
    assert is_placeholder(data)


def test_bundled_tier_is_not_flagged_as_placeholder():
    """With real 2026 figures, the bundled lookup must NOT flag placeholder."""
    tier = tuition_for_age_months(6)
    assert tier is not None
    assert tier.is_placeholder is False
    assert tier.data_year == 2026


def test_float_age_floors_to_month(tmp_path):
    """Coordinator passes a fractional month — must floor, not error."""
    path, _ = _table_with_real_values(tmp_path)
    src = json.loads(path.read_text(encoding="utf-8"))
    # 11.97 months is still 만 0세반.
    tier = tuition_for_age_months(11.97, src)
    assert tier is not None
    assert tier.age_class == 0
    # 12.0 crosses into 만 1세반.
    tier = tuition_for_age_months(12.0, src)
    assert tier is not None
    assert tier.age_class == 1



@pytest.mark.parametrize(
    ("birthdate", "expected"),
    [
        (date(2026, 3, 1), 0),   # born this year -> 만 0세반
        (date(2025, 1, 1), 0),   # 2026: 2025.1.1 이후 출생 = 0세반
        (date(2024, 12, 31), 1),
        (date(2024, 1, 1), 1),
        (date(2023, 12, 1), 2),  # 35 months in Nov 2026, still 만 2세반
        (date(2023, 1, 10), 2),  # 46 months in Nov 2026 -> 만 2세반, not 3
        (date(2022, 6, 1), 3),
        (date(2020, 6, 1), 5),
        (date(2019, 6, 1), 6),   # 취학유예
        (date(2018, 6, 1), None),
    ],
)
def test_age_class_follows_birth_year_2026(birthdate, expected):
    assert age_class_for_birthdate(birthdate, date(2026, 11, 9)) == expected


def test_age_class_none_before_birth():
    assert age_class_for_birthdate(date(2026, 12, 1), date(2026, 11, 9)) is None


def test_tuition_for_birthdate_uses_bundled_2026_rates():
    tier = tuition_for_birthdate(date(2023, 8, 20), date(2026, 11, 9))
    assert tier is not None
    assert tier.age_class == 2
    assert tier.standard_tuition == 426000
    assert tuition_for_birthdate(date(2024, 2, 1), date(2026, 11, 9)).standard_tuition == 515000
