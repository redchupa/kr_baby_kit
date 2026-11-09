"""End-to-end smoke test through pytest-homeassistant-custom-component.

Verifies:
  - Config entry sets up cleanly.
  - Sensors and calendars are registered with the expected unique_ids.
  - record_measurement service stores data and refreshes percentile sensors.
"""
from __future__ import annotations

import sys

import pytest

# HA's runner.py imports `fcntl`, which is Unix-only. The full integration
# stack therefore can't import on Windows. CI runs Ubuntu so this is fine
# end-to-end; locally we just skip.
#
# In CI the `conversation` integration (dep of our llm tool) drags in a long
# chain of audio/intent runtime deps that aren't part of the HA test plugin's
# default install set. Pinning every one of those just to keep this smoke test
# green is fragile — we keep the file in tree as documentation of the expected
# entity set but skip until the test harness gets a heavier dep install.
pytestmark = [
    pytest.mark.skipif(
        sys.platform == "win32",
        reason="pytest-homeassistant-custom-component requires POSIX (fcntl).",
    ),
]
# Collection is skipped entirely (tests/integration/conftest.py) when the
# conversation integration's deps (hassil, ...) are missing, which is the
# case in the default CI install.

from homeassistant.config_entries import ConfigEntryState  # noqa: E402
from homeassistant.core import HomeAssistant  # noqa: E402
from homeassistant.helpers import entity_registry as er  # noqa: E402
from pytest_homeassistant_custom_component.common import MockConfigEntry  # noqa: E402

from custom_components.kr_baby_kit.const import (  # noqa: E402
    CONF_CHILD_BIRTHDATE,
    CONF_CHILD_ID,
    CONF_CHILD_NAME,
    CONF_CHILD_SEX,
    DOMAIN,
)


CHILD_ID = "synthetic_baby_a"
BIRTHDATE = "2020-03-15"  # avoids real child's birth year per CLAUDE.md


def _mock_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Baby A",
        data={
            CONF_CHILD_ID: CHILD_ID,
            CONF_CHILD_NAME: "Baby A",
            CONF_CHILD_BIRTHDATE: BIRTHDATE,
            CONF_CHILD_SEX: "male",
        },
        unique_id=CHILD_ID,
    )


def _entity_id(hass: HomeAssistant, unique_id: str) -> str | None:
    registry = er.async_get(hass)
    for domain in ("sensor", "binary_sensor", "calendar", "number"):
        eid = registry.async_get_entity_id(domain, DOMAIN, unique_id)
        if eid:
            return eid
    return None


async def test_setup_registers_sensors_and_calendars(hass: HomeAssistant) -> None:
    entry = _mock_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state == ConfigEntryState.LOADED

    expected = [
        f"{DOMAIN}_{CHILD_ID}_age_months",
        f"{DOMAIN}_{CHILD_ID}_height_percentile",
        f"{DOMAIN}_{CHILD_ID}_weight_percentile",
        f"{DOMAIN}_{CHILD_ID}_bmi_raw",
        # v0.8.0: bi-directional metrics moved off percentile sensors and
        # onto binary "양극단 주의" alerts.
        f"{DOMAIN}_{CHILD_ID}_head_concern",
        f"{DOMAIN}_{CHILD_ID}_bmi_concern",
        f"{DOMAIN}_{CHILD_ID}_weight_for_length_concern",
        f"{DOMAIN}_{CHILD_ID}_upcoming_vaccines_due_this_month",
        f"{DOMAIN}_{CHILD_ID}_upcoming_checkups_due_this_month",
        f"{DOMAIN}_{CHILD_ID}_upcoming_oral_checkups_due_this_month",
        f"{DOMAIN}_{CHILD_ID}_immunization_calendar",
        f"{DOMAIN}_{CHILD_ID}_checkup_calendar",
        f"{DOMAIN}_{CHILD_ID}_oral_checkup_calendar",
        f"{DOMAIN}_{CHILD_ID}_next_vaccine",
        f"{DOMAIN}_{CHILD_ID}_next_checkup",
        f"{DOMAIN}_{CHILD_ID}_next_oral_checkup",
        f"{DOMAIN}_{CHILD_ID}_standard_tuition",
        f"{DOMAIN}_{CHILD_ID}_government_subsidy",
        f"{DOMAIN}_{CHILD_ID}_parent_share",
        f"{DOMAIN}_{CHILD_ID}_height_input",
        f"{DOMAIN}_{CHILD_ID}_weight_input",
        f"{DOMAIN}_{CHILD_ID}_head_input",
    ]
    for uid in expected:
        assert _entity_id(hass, uid) is not None, f"missing entity for {uid}"

    age_entity = _entity_id(hass, f"{DOMAIN}_{CHILD_ID}_age_months")
    age_state = hass.states.get(age_entity)
    assert age_state is not None
    assert float(age_state.state) > 0


async def test_record_measurement_updates_height_percentile(
    hass: HomeAssistant,
) -> None:
    entry = _mock_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    response = await hass.services.async_call(
        DOMAIN,
        "record_measurement",
        {
            CONF_CHILD_ID: CHILD_ID,
            "date": "2025-03-15",  # exactly 60 months after birth
            "height": 110.0,
            "weight": 18.0,
        },
        blocking=True,
        return_response=True,
    )
    assert response["child_id"] == CHILD_ID
    assert response["record"]["height"] == 110.0

    await hass.async_block_till_done()

    height_entity = _entity_id(
        hass, f"{DOMAIN}_{CHILD_ID}_height_percentile"
    )
    state = hass.states.get(height_entity)
    assert state is not None
    assert state.state not in ("unknown", "unavailable", None)
    # KDCA 60-month male median ≈ 109.6 cm. 110 cm sits a bit above median,
    # so the rank-percent sensor value (v0.6.0: 100 - statistical_percentile)
    # should fall in roughly 20–70.
    rank = float(state.state)
    assert 20.0 <= rank <= 70.0, f"unexpected rank {rank}"


async def test_number_set_value_records_measurement(hass: HomeAssistant) -> None:
    entry = _mock_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    height_input = _entity_id(hass, f"{DOMAIN}_{CHILD_ID}_height_input")
    assert height_input is not None

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": height_input, "value": 108.0},
        blocking=True,
    )
    await hass.async_block_till_done()

    height_pct_entity = _entity_id(
        hass, f"{DOMAIN}_{CHILD_ID}_height_percentile"
    )
    state = hass.states.get(height_pct_entity)
    assert state is not None
    assert state.state not in ("unknown", "unavailable", None)


async def test_bmi_concern_emitted_when_height_and_weight_recorded(
    hass: HomeAssistant,
) -> None:
    """v0.8.0: BMI is exposed as a binary "양극단 주의" alert + a raw-value sensor.

    A median-aged child measured at the population median should land in the
    normal band, so the concern alert stays off and the raw-value sensor
    carries the BMI.
    """
    entry = _mock_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "record_measurement",
        {
            CONF_CHILD_ID: CHILD_ID,
            "date": "2025-03-15",  # 60 months after birth — well past 24mo cutoff
            "height": 110.0,
            "weight": 18.0,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    bmi_concern = _entity_id(hass, f"{DOMAIN}_{CHILD_ID}_bmi_concern")
    state = hass.states.get(bmi_concern)
    assert state is not None
    # Median-ish BMI shouldn't trip the concern alert.
    assert state.state == "off"
    pct = state.attributes.get("statistical_percentile")
    assert pct is not None
    assert 0.0 <= pct <= 100.0

    bmi_raw = _entity_id(hass, f"{DOMAIN}_{CHILD_ID}_bmi_raw")
    raw_state = hass.states.get(bmi_raw)
    assert raw_state is not None
    assert float(raw_state.state) == pytest.approx(18.0 / (1.10 ** 2), rel=1e-3)


async def test_care_tuition_sensor_surfaces_2026_figures(
    hass: HomeAssistant,
) -> None:
    """Bundled tuition table now ships with 2026 교육부 figures (no longer placeholder).

    The synthetic birthdate falls inside the 만 0~6세반 range for the lifetime
    of this test fixture; if the child ages out, the sensor returns ``unknown``
    rather than a confusing zero. Either branch passes — the invariant is
    "no placeholder flag, no misleading values."
    """
    entry = _mock_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    eid = _entity_id(hass, f"{DOMAIN}_{CHILD_ID}_standard_tuition")
    state = hass.states.get(eid)
    assert state is not None
    if state.state in ("unknown", "unavailable"):
        return  # outside 보육료 coverage; nothing more to assert
    assert int(state.state) > 0
    assert state.attributes.get("is_placeholder") is False
    assert state.attributes.get("data_year") == 2026


async def test_unload_entry(hass: HomeAssistant) -> None:
    entry = _mock_entry()
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state == ConfigEntryState.NOT_LOADED


# ---------------------------------------------------------------- v0.9.0

from datetime import datetime, timedelta  # noqa: E402

from homeassistant.exceptions import (  # noqa: E402
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.util import dt as dt_util  # noqa: E402

from custom_components.kr_baby_kit.const import TZ_ASIA_SEOUL  # noqa: E402
from custom_components.kr_baby_kit.schedule import add_calendar_months  # noqa: E402
from custom_components.kr_baby_kit.storage import async_load_records  # noqa: E402

YOUNG_ID = "synthetic_baby_b"


def _young_entry(months_old: int = 2) -> MockConfigEntry:
    """A child a few days past ``months_old`` so the 2-month bundle is open."""
    today = datetime.now(TZ_ASIA_SEOUL).date()
    bd = add_calendar_months(today, -months_old) - timedelta(days=3)
    return MockConfigEntry(
        domain=DOMAIN,
        title="Baby B",
        data={
            CONF_CHILD_ID: YOUNG_ID,
            CONF_CHILD_NAME: "Baby B",
            CONF_CHILD_BIRTHDATE: bd.isoformat(),
            CONF_CHILD_SEX: "female",
        },
        unique_id=YOUNG_ID,
    )


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_mark_event_done_removes_it_from_next_vaccine(
    hass: HomeAssistant,
) -> None:
    await _setup(hass, _young_entry())
    next_vaccine = _entity_id(hass, f"{DOMAIN}_{YOUNG_ID}_next_vaccine")
    state = hass.states.get(next_vaccine)
    open_ids = state.attributes["open_event_ids"]
    assert "DTaP_1" in open_ids

    resp = await hass.services.async_call(
        DOMAIN,
        "mark_event_done",
        {"event_id": ", ".join(open_ids)},
        blocking=True,
        return_response=True,
    )
    assert set(resp["completed"]) == set(open_ids)
    await hass.async_block_till_done()

    state = hass.states.get(next_vaccine)
    assert state.attributes.get("event_id") not in open_ids

    schedule = await hass.services.async_call(
        DOMAIN, "get_schedule", {}, blocking=True, return_response=True
    )
    status = {v["event_id"]: v["status"] for v in schedule["vaccines"]}
    assert status["DTaP_1"] == "done"
    assert len(schedule["oral_checkups"]) == 4

    await hass.services.async_call(
        DOMAIN, "unmark_event_done", {"event_id": "DTaP_1"}, blocking=True
    )
    await hass.async_block_till_done()
    state = hass.states.get(next_vaccine)
    assert "DTaP_1" in state.attributes["open_event_ids"]


async def test_mark_event_done_rejects_unknown_id(hass: HomeAssistant) -> None:
    await _setup(hass, _young_entry())
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "mark_event_done", {"event_id": "NOPE_9"}, blocking=True
        )


async def test_delete_and_get_measurements(hass: HomeAssistant) -> None:
    await _setup(hass, _mock_entry())
    await hass.services.async_call(
        DOMAIN,
        "record_measurement",
        {"date": "2025-03-15", "height": 110.0, "weight": 18.0},
        blocking=True,
    )
    await hass.services.async_call(
        DOMAIN,
        "delete_measurement",
        {"date": "2025-03-15", "kinds": ["weight"]},
        blocking=True,
    )
    resp = await hass.services.async_call(
        DOMAIN, "get_measurements", {}, blocking=True, return_response=True
    )
    assert resp["records"] == [{"date": "2025-03-15", "height": 110.0}]


async def test_record_measurement_defaults_to_today(hass: HomeAssistant) -> None:
    await _setup(hass, _mock_entry())
    resp = await hass.services.async_call(
        DOMAIN,
        "record_measurement",
        {"height": 110.0},
        blocking=True,
        return_response=True,
    )
    assert resp["record"]["date"] == datetime.now(TZ_ASIA_SEOUL).date().isoformat()


async def test_number_out_of_range_raises_ha_error(hass: HomeAssistant) -> None:
    await _setup(hass, _mock_entry())
    from custom_components.kr_baby_kit.number import MeasurementNumber

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    number = MeasurementNumber(coordinator, entry, "height")
    number.hass = hass
    with pytest.raises(HomeAssistantError):
        await number.async_set_native_value(999.0)


async def test_options_flow_updates_child(hass: HomeAssistant) -> None:
    entry = _mock_entry()
    await _setup(hass, entry)
    await hass.services.async_call(
        DOMAIN,
        "record_measurement",
        {"date": "2025-03-15", "height": 110.0},
        blocking=True,
    )

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_CHILD_NAME: "Baby A2",
            CONF_CHILD_BIRTHDATE: "2020-04-15",
            CONF_CHILD_SEX: "female",
        },
    )
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()

    assert entry.title == "Baby A2"
    assert entry.data[CONF_CHILD_BIRTHDATE] == "2020-04-15"
    assert entry.data[CONF_CHILD_ID] == CHILD_ID  # identity unchanged
    assert entry.state == ConfigEntryState.LOADED
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    assert coordinator.birthdate.isoformat() == "2020-04-15"
    resp = await hass.services.async_call(
        DOMAIN, "get_measurements", {}, blocking=True, return_response=True
    )
    assert resp["count"] == 1  # records survive the reload


async def test_options_flow_rejects_future_birthdate(hass: HomeAssistant) -> None:
    entry = _mock_entry()
    await _setup(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_CHILD_NAME: "Baby A",
            CONF_CHILD_BIRTHDATE: "2999-01-01",
            CONF_CHILD_SEX: "male",
        },
    )
    assert result["type"] == "form"
    assert result["errors"] == {CONF_CHILD_BIRTHDATE: "future_date"}


async def test_calendar_lists_past_and_completed_events(hass: HomeAssistant) -> None:
    await _setup(hass, _mock_entry())
    await hass.services.async_call(
        DOMAIN,
        "mark_event_done",
        {"event_id": "oral_checkup_1", "date": "2021-10-01"},
        blocking=True,
    )
    await hass.async_block_till_done()
    cal_id = _entity_id(hass, f"{DOMAIN}_{CHILD_ID}_oral_checkup_calendar")
    resp = await hass.services.async_call(
        "calendar",
        "get_events",
        {
            "entity_id": cal_id,
            "start_date_time": dt_util.as_local(datetime(2021, 1, 1)).isoformat(),
            "end_date_time": dt_util.as_local(datetime(2026, 1, 1)).isoformat(),
        },
        blocking=True,
        return_response=True,
    )
    events = resp[cal_id]["events"]
    assert len(events) == 4
    assert events[0]["summary"].startswith("✅")
    assert events[1]["summary"].startswith("⚠️")


async def test_remove_entry_deletes_child_records(hass: HomeAssistant) -> None:
    entry = _mock_entry()
    await _setup(hass, entry)
    await hass.services.async_call(
        DOMAIN,
        "record_measurement",
        {"date": "2025-03-15", "height": 110.0},
        blocking=True,
    )
    assert CHILD_ID in await async_load_records(hass)
    assert await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()
    assert CHILD_ID not in await async_load_records(hass)


async def test_bmi_concern_advisory_uses_age_at_measurement(hass: HomeAssistant) -> None:
    """Child is now >24 months but was measured at 18 months: no KDCA BMI
    percentile exists for that measurement, so the entity must show the
    advisory (state off) instead of going unavailable."""
    await _setup(hass, _mock_entry())
    await hass.services.async_call(
        DOMAIN,
        "record_measurement",
        {"date": "2021-09-15", "height": 82.0, "weight": 11.0},
        blocking=True,
    )
    await hass.async_block_till_done()
    eid = _entity_id(hass, f"{DOMAIN}_{CHILD_ID}_bmi_concern")
    state = hass.states.get(eid)
    assert state.state == "off"
    assert "측정 당시" in state.attributes["summary_ko"]
    raw = hass.states.get(_entity_id(hass, f"{DOMAIN}_{CHILD_ID}_bmi_raw"))
    assert "측정 당시" in raw.attributes["summary_ko"]


async def test_next_oral_checkup_shown_beyond_one_year(hass: HomeAssistant) -> None:
    """A 2-month-old's first oral checkup (18 months) is >1 year out; the
    next-event sensor must still show it instead of unknown."""
    await _setup(hass, _young_entry())
    state = hass.states.get(
        _entity_id(hass, f"{DOMAIN}_{YOUNG_ID}_next_oral_checkup")
    )
    assert state.state not in ("unknown", "unavailable")
    assert state.attributes["event_id"] == "oral_checkup_1"


async def test_single_dose_vaccine_has_no_dose_suffix(hass: HomeAssistant) -> None:
    await _setup(hass, _young_entry())
    cal_id = _entity_id(hass, f"{DOMAIN}_{YOUNG_ID}_immunization_calendar")
    today = datetime.now(TZ_ASIA_SEOUL)
    resp = await hass.services.async_call(
        "calendar",
        "get_events",
        {
            "entity_id": cal_id,
            "start_date_time": (today - timedelta(days=120)).isoformat(),
            "end_date_time": today.isoformat(),
        },
        blocking=True,
        return_response=True,
    )
    summaries = [e["summary"] for e in resp[cal_id]["events"]]
    bcg = [s for s in summaries if "BCG" in s]
    assert bcg and all("차)" not in s for s in bcg)
    assert any("B형간염 (1차)" in s for s in summaries)
