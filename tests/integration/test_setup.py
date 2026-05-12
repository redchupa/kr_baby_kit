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
pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="pytest-homeassistant-custom-component requires POSIX (fcntl).",
)

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
        f"{DOMAIN}_{CHILD_ID}_head_percentile",
        f"{DOMAIN}_{CHILD_ID}_bmi_percentile",
        f"{DOMAIN}_{CHILD_ID}_bmi_raw",
        f"{DOMAIN}_{CHILD_ID}_weight_for_length_percentile",
        f"{DOMAIN}_{CHILD_ID}_upcoming_vaccines_due_this_month",
        f"{DOMAIN}_{CHILD_ID}_upcoming_checkups_due_this_month",
        f"{DOMAIN}_{CHILD_ID}_immunization_calendar",
        f"{DOMAIN}_{CHILD_ID}_checkup_calendar",
        f"{DOMAIN}_{CHILD_ID}_next_vaccine",
        f"{DOMAIN}_{CHILD_ID}_next_checkup",
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


async def test_bmi_percentile_emitted_when_height_and_weight_recorded(
    hass: HomeAssistant,
) -> None:
    """BMI is derived from height+weight once the child is ≥24 months."""
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

    bmi_entity = _entity_id(hass, f"{DOMAIN}_{CHILD_ID}_bmi_percentile")
    state = hass.states.get(bmi_entity)
    assert state is not None
    assert state.state not in ("unknown", "unavailable", None)
    pct = float(state.state)
    assert 0.0 <= pct <= 100.0
    # Surfaced BMI value comes back via the `value` attribute.
    assert state.attributes.get("value") == pytest.approx(
        18.0 / (1.10 ** 2), rel=1e-3
    )


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
