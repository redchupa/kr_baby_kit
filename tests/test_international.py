"""Tests for international (WHO) profile, English summaries, and translation parity."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from custom_components.kr_baby_kit.const import (
    PROFILE_GLOBAL,
    PROFILE_KR,
    attribution_for,
    disclaimer_for,
)
from custom_components.kr_baby_kit.growth import GrowthChart, format_summary_en
from custom_components.kr_baby_kit.schedule import (
    load_checkup_schedule_for_profile,
    load_vaccine_schedule,
    project_checkup_events,
    project_oral_checkup_events,
    project_vaccine_events,
)

_COMP_DIR = (
    Path(__file__).resolve().parent.parent / "custom_components" / "kr_baby_kit"
)


def test_who_growth_chart_loads_and_matches_known_medians():
    chart = GrowthChart.from_profile(PROFILE_GLOBAL)
    for sex in ("male", "female"):
        for kind in ("height", "weight", "head", "bmi"):
            assert chart.has(sex, kind), f"missing WHO {sex}/{kind}"
        assert chart.has_weight_for_length(sex, 12.0)
        assert chart.has_weight_for_length(sex, 30.0)
        assert chart.has_weight_for_length(sex, 48.0)

    # WHO 2006 boys birth medians: length 49.8842 cm, weight 3.3464 kg, head 34.4618 cm
    z_h, pct_h = chart.percentile("male", "height", 0.0, 49.8842)
    assert z_h is not None and abs(z_h) < 0.01
    assert pct_h is not None and 49.5 <= pct_h <= 50.5

    z_w, pct_w = chart.percentile("male", "weight", 0.0, 3.3464)
    assert z_w is not None and abs(z_w) < 0.01
    assert pct_w is not None and 49.5 <= pct_w <= 50.5

    z_hc, pct_hc = chart.percentile("male", "head", 0.0, 34.4618)
    assert z_hc is not None and abs(z_hc) < 0.01
    assert pct_hc is not None and 49.5 <= pct_hc <= 50.5

    # BMI works at 24 months and 120 months
    _, pct_bmi_24 = chart.percentile("female", "bmi", 24.0, 15.4)
    assert pct_bmi_24 is not None and 0.0 < pct_bmi_24 < 100.0
    _, pct_bmi_120 = chart.percentile("male", "bmi", 120.0, 16.5)
    assert pct_bmi_120 is not None and 0.0 < pct_bmi_120 < 100.0


def test_global_schedules_project_cleanly():
    bd = date(2023, 3, 15)
    vac_sched = load_vaccine_schedule(PROFILE_GLOBAL)
    chk_sched = load_checkup_schedule_for_profile(PROFILE_GLOBAL)

    vaccines = project_vaccine_events(bd, vac_sched)
    checkups = project_checkup_events(bd, chk_sched)
    oral = project_oral_checkup_events(bd, chk_sched)

    assert len(vaccines) >= 20
    assert all(e.name_en for e in vaccines)
    assert len(checkups) == 12
    assert all(e.name_en and e.window_note_en and e.items_en for e in checkups)
    assert len(oral) == 5
    assert all(e.name_en and e.window_note_en and e.items_en for e in oral)


@pytest.mark.parametrize(
    ("kind", "pct", "expected"),
    [
        ("height", 94.7, "Height: top 5.3% among peers (tall)"),
        ("weight", 12.5, "Weight: top 87.5% among peers (light)"),
        ("height", 50.0, "Height: around peer average"),
        ("height", 99.98, "Height: top <0.1% among peers (tall)"),
        ("head", 50.0, "Head circumference: around peer average (normal range)"),
        ("head", 97.0, "Head circumference: top 3.0% among peers (large, consult pediatrician)"),
        ("bmi", 3.0, "BMI: bottom 3.0% among peers (low, consult pediatrician)"),
        ("weight_for_length", 80.0, "Weight-for-length: top 20.0% among peers (heavy for length)"),
        ("height", None, None),
    ],
)
def test_format_summary_en(kind, pct, expected):
    assert format_summary_en(kind, pct) == expected


def test_attribution_and_disclaimer_by_profile_and_language():
    assert "질병관리청" in attribution_for(PROFILE_KR, korean=True)
    assert "KDCA" in attribution_for(PROFILE_KR, korean=False)
    assert "WHO" in attribution_for(PROFILE_GLOBAL, korean=True)
    assert "WHO" in attribution_for(PROFILE_GLOBAL, korean=False)
    assert "참고용" in disclaimer_for(korean=True)
    assert "reference only" in disclaimer_for(korean=False)


def _key_tree(obj):
    if isinstance(obj, dict):
        return {k: _key_tree(v) for k, v in obj.items()}
    return None


def test_translation_files_have_identical_key_structure():
    strings = json.loads((_COMP_DIR / "strings.json").read_text(encoding="utf-8"))
    en = json.loads((_COMP_DIR / "translations" / "en.json").read_text(encoding="utf-8"))
    ko = json.loads((_COMP_DIR / "translations" / "ko.json").read_text(encoding="utf-8"))

    assert strings == en
    assert _key_tree(strings) == _key_tree(ko)


def test_number_entity_defaults_to_age_median_when_no_records():
    from types import SimpleNamespace
    from custom_components.kr_baby_kit.number import MeasurementNumber

    for profile in (PROFILE_KR, PROFILE_GLOBAL):
        chart = GrowthChart.from_profile(profile)
        coord = SimpleNamespace(
            hass=None,
            entry=SimpleNamespace(entry_id="e1", data={"child_id": "c1", "child_name": "Child A"}),
            child_id="c1",
            child_sex="male",
            profile=profile,
            chart=chart,
            data={"age_months": 24.0, "records": []},
        )
        for kind in ("height", "weight", "head"):
            ent = MeasurementNumber(coord, coord.entry, kind)
            val = ent.native_value
            expected_m = chart.lookup("male", kind, 24.0).M
            assert val is not None
            assert abs(val - expected_m) <= 0.1
            assert ent.extra_state_attributes["is_default_median"] is True

        # Once a real measurement exists, native_value uses it instead of median.
        coord.data["records"] = [{"date": "2026-11-25", "height": 91.5}]
        ent_h = MeasurementNumber(coord, coord.entry, "height")
        assert ent_h.native_value == 91.5
        assert ent_h.extra_state_attributes["is_default_median"] is False
        assert ent_h.extra_state_attributes["measured_at"] == "2026-11-25"
