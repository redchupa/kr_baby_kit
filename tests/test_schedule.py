"""Unit tests for NIP + 영유아 검진 schedule projection."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from custom_components.kr_baby_kit.schedule import (
    STATUS_DONE,
    STATUS_MISSED,
    STATUS_OPEN,
    STATUS_UPCOMING,
    add_calendar_months,
    event_status,
    event_to_dict,
    project_checkup_events,
    project_oral_checkup_events,
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


def test_checkups_have_eight_events() -> None:
    events = project_checkup_events(BD)
    # v0.8.1: standard checkup count is 8 since the 2021-01-01 inclusion of the
    # 생후 14~35일 (early) checkup at order 1.
    assert len(events) == 8
    orders = [e.dose for e in events]
    assert orders == [1, 2, 3, 4, 5, 6, 7, 8]


def test_checkup_first_window_covers_14_to_35_days() -> None:
    events = project_checkup_events(BD)
    first = [e for e in events if e.dose == 1][0]
    assert (first.start - BD).days == 14
    assert (first.end - BD).days == 35


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


def test_checkup_fourth_window_is_18_to_24_months() -> None:
    # The 18–24 month window was order=3 prior to v0.8.1 and shifted to
    # order=4 when the 생후 14~35일 (early) checkup was added at order=1.
    events = project_checkup_events(BD)
    fourth = [e for e in events if e.dose == 4][0]
    # Inclusive month-of-age: 18개월 되는 날 ~ 25개월 되기 전날.
    assert fourth.start == date(2021, 9, 15)
    assert fourth.end == date(2022, 4, 14)


@pytest.mark.parametrize("month", [0, 6, 12, 24, 60])
def test_project_vaccines_deterministic(month: int) -> None:
    events_a = project_vaccine_events(BD)
    events_b = project_vaccine_events(BD)
    codes_a = [(e.code, e.dose, e.start.isoformat()) for e in events_a]
    codes_b = [(e.code, e.dose, e.start.isoformat()) for e in events_b]
    assert codes_a == codes_b


# ---------------------------------------------------------------- v0.9.0


def test_add_calendar_months_clamps_month_end() -> None:
    assert add_calendar_months(date(2020, 1, 31), 1) == date(2020, 2, 29)
    assert add_calendar_months(date(2021, 1, 31), 1) == date(2021, 2, 28)
    assert add_calendar_months(date(2020, 3, 15), 12) == date(2021, 3, 15)
    assert add_calendar_months(date(2020, 11, 30), 3) == date(2021, 2, 28)


def test_second_checkup_runs_until_day_before_seven_months() -> None:
    second = [e for e in project_checkup_events(BD) if e.dose == 2][0]
    assert second.start == date(2020, 7, 15)
    assert second.end == date(2020, 10, 14)
    assert second.window_note == "생후 4~6개월"
    assert "신체계측" in second.items


def test_eighth_checkup_includes_vaccination_check() -> None:
    eighth = [e for e in project_checkup_events(BD) if e.dose == 8][0]
    assert eighth.end == date(2026, 3, 14)  # day before 72 months
    assert any("예방접종" in item for item in eighth.items)


def test_oral_checkups_four_windows() -> None:
    events = project_oral_checkup_events(BD)
    assert [e.event_id for e in events] == [
        "oral_checkup_1",
        "oral_checkup_2",
        "oral_checkup_3",
        "oral_checkup_4",
    ]
    assert all(e.kind == "oral_checkup" for e in events)
    windows = [(e.start, e.end) for e in events]
    assert windows == [
        (date(2021, 9, 15), date(2022, 9, 14)),   # 18~29개월
        (date(2022, 9, 15), date(2023, 9, 14)),   # 30~41개월
        (date(2023, 9, 15), date(2024, 9, 14)),   # 42~53개월
        (date(2024, 9, 15), date(2025, 9, 14)),   # 54~65개월
    ]
    assert events[0].items == ("구강문진 및 진찰", "구강보건교육")


def test_vaccine_events_are_chronological() -> None:
    events = project_vaccine_events(BD)
    keys = [(e.start, e.end) for e in events]
    assert keys == sorted(keys)


def test_upcoming_returns_soonest_first_not_json_order() -> None:
    """Regression: the next-vaccine sensor used to read events[0] in JSON
    order (BCG, HepB, DTaP...), not the chronologically next window."""
    ref = date(2021, 2, 1)  # ~10.5 months old
    soon = upcoming(project_vaccine_events(BD), ref)
    starts = [e.start for e in soon]
    assert starts == sorted(starts)
    # MMR/VAR at 12 months must come before DTaP 4 (15 months).
    ids = [e.event_id for e in soon]
    assert ids.index("MMR_1") < ids.index("DTaP_4")


def test_upcoming_drops_completed_events() -> None:
    ref = date(2020, 5, 20)  # 2 months old — DTaP/IPV/Hib/PCV/RV window open
    events = project_vaccine_events(BD)
    before = {e.event_id for e in upcoming(events, ref)}
    assert {"DTaP_1", "IPV_1", "Hib_1", "PCV_1", "RV_1"} <= before
    after = {
        e.event_id
        for e in upcoming(events, ref, completed={"DTaP_1": {}, "IPV_1": {}})
    }
    assert "DTaP_1" not in after and "IPV_1" not in after
    assert "Hib_1" in after


def test_event_ids_are_unique() -> None:
    ids = [
        e.event_id
        for e in (
            *project_vaccine_events(BD),
            *project_checkup_events(BD),
            *project_oral_checkup_events(BD),
        )
    ]
    assert len(ids) == len(set(ids))


def test_influenza_is_projected_per_season() -> None:
    flu = [e for e in project_vaccine_events(BD) if e.code == "IIV"]
    assert flu[0].event_id == "IIV_2020"
    assert flu[0].start == date(2020, 10, 1)
    assert flu[0].end == date(2021, 4, 30)
    # Eligible until the day before 168 months (만 14세).
    assert flu[-1].end <= date(2034, 3, 14)
    assert all(e.dose is None and e.season is not None for e in flu)
    assert "절기" in flu[0].name_ko


def test_influenza_does_not_hog_next_vaccine() -> None:
    """A 14-year-long single flu window would always be 'next'; seasons fix it."""
    ref = date(2023, 6, 1)  # off-season, 38 months old
    soon = upcoming(project_vaccine_events(BD), ref)
    flu = [e for e in soon if e.code == "IIV"]
    # Off-season: the next flu window is in the future, not "open now".
    assert flu and all(e.start > ref for e in flu)
    # In-season with other doses open, those earlier windows sort first.
    ref2 = date(2021, 3, 20)  # 12 months old, 2020-21 season still open
    soon2 = upcoming(project_vaccine_events(BD), ref2)
    assert soon2.index(next(e for e in soon2 if e.code == "IIV")) > 0


def test_hpv_starts_at_twelve() -> None:
    hpv = [e for e in project_vaccine_events(BD) if e.code == "HPV"]
    assert hpv[0].start == date(2032, 3, 15)
    assert "남아" in hpv[0].note


def test_event_status_and_dict() -> None:
    ev = [e for e in project_checkup_events(BD) if e.dose == 2][0]
    assert event_status(ev, date(2020, 6, 1)) == STATUS_UPCOMING
    assert event_status(ev, date(2020, 8, 1)) == STATUS_OPEN
    assert event_status(ev, date(2021, 1, 1)) == STATUS_MISSED
    done = {"checkup_2": {"date": "2020-08-01"}}
    assert event_status(ev, date(2021, 1, 1), done) == STATUS_DONE
    d = event_to_dict(ev, date(2021, 1, 1), done)
    assert d["event_id"] == "checkup_2"
    assert d["status"] == STATUS_DONE
    assert d["completed_date"] == "2020-08-01"
    assert d["window_note_ko"] == "생후 4~6개월"


def test_single_dose_vaccines_carry_dose_count() -> None:
    events = {e.event_id: e for e in project_vaccine_events(BD)}
    assert events["BCG_1"].dose_count == 1
    assert events["VAR_1"].dose_count == 1
    assert events["DTaP_1"].dose_count == 5



def test_event_before_tracking_is_not_missed() -> None:
    from custom_components.kr_baby_kit.schedule import STATUS_PAST

    ev = [e for e in project_checkup_events(BD) if e.dose == 2][0]
    # Registered after the window closed -> past_before_tracking.
    assert event_status(ev, date(2021, 1, 1), None, date(2020, 12, 1)) == STATUS_PAST
    # Registered before it closed -> genuinely missed.
    assert event_status(ev, date(2021, 1, 1), None, date(2020, 9, 1)) == STATUS_MISSED
