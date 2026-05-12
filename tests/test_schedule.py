"""Unit tests for NIP + 영유아 검진 schedule projection."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from custom_components.kr_baby_kit.schedule import (
    project_checkup_events,
    project_vaccine_events,
    upcoming,
)


BD = date(2020, 3, 15)  # synthetic birthdate (avoids real child's 2024 birth year)


def test_vaccines_project_one_event_per_dose() -> None:
    events = project_vaccine_events(BD)
    # BCG (1 dose) + HepB (3) + DTaP (5) + Tdap (1) + IPV (4) + Hib (4)
    # + PCV (4) + RV (3) + MMR (2) + VAR (1) + HepA (2) + IJEV (5) + HPV (2) + IIV (1)
    assert len(events) >= 30
    assert all(e.kind == "vaccine" for e in events)


def test_checkups_have_seven_events() -> None:
    events = project_checkup_events(BD)
    assert len(events) == 7
    orders = [e.dose for e in events]
    assert orders == [1, 2, 3, 4, 5, 6, 7]


def test_bcg_first_dose_is_within_first_month() -> None:
    events = project_vaccine_events(BD)
    bcg = [e for e in events if e.code == "BCG"][0]
    assert bcg.start <= BD + timedelta(days=31)
    assert bcg.end <= BD + timedelta(days=62)


def test_mmr_first_dose_is_around_12_months() -> None:
    events = project_vaccine_events(BD)
    mmr = [e for e in events if e.code == "MMR" and e.dose == 1][0]
    target = BD.replace(year=BD.year + 1)
    assert abs((mmr.start - target).days) <= 31


def test_upcoming_horizon_filters_by_date() -> None:
    events = project_vaccine_events(BD)
    # 1 month after birth: only earliest doses should be in 30-day horizon
    early = upcoming(events, BD + timedelta(days=30), horizon_days=30)
    assert all(e.start <= BD + timedelta(days=60) for e in early)


def test_upcoming_filters_out_past_events() -> None:
    events = project_vaccine_events(BD)
    ref = BD.replace(year=BD.year + 5)  # 5 years later
    soon = upcoming(events, ref, horizon_days=30)
    for e in soon:
        assert e.end >= ref


def test_checkup_third_window_is_18_to_24_months() -> None:
    events = project_checkup_events(BD)
    third = [e for e in events if e.dose == 3][0]
    assert (third.start - BD).days >= int(18 * 30) - 5
    assert (third.end - BD).days <= int(24 * 30.5) + 5


@pytest.mark.parametrize("month", [0, 6, 12, 24, 60])
def test_project_vaccines_deterministic(month: int) -> None:
    events_a = project_vaccine_events(BD)
    events_b = project_vaccine_events(BD)
    codes_a = [(e.code, e.dose, e.start.isoformat()) for e in events_a]
    codes_b = [(e.code, e.dose, e.start.isoformat()) for e in events_b]
    assert codes_a == codes_b
