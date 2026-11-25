"""한국 영유아 키트 (Korean Baby Kit) — HACS integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_CHILD_ID,
    CONF_CHILD_NAME,
    CONF_PROFILE,
    DOMAIN,
    LOGGER,  # noqa: F401  (LOGGER re-exported)
    PROFILE_KR,
)
from .llm_api import async_cleanup_llm_api, async_setup_llm_api
from .panel import async_register_panel, async_unregister_panel
from .services import async_register_services, async_unregister_services
from .websocket_api import async_register_websocket_api

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a child entry."""
    hass.data.setdefault(DOMAIN, {})

    from .care_tuition import async_load_tuition_table
    from .coordinator import BabyKitCoordinator
    from .growth import GrowthChart
    from .schedule import (
        async_load_checkup_schedule_for_profile,
        async_load_vaccine_schedule,
    )

    profile = entry.data.get(CONF_PROFILE, PROFILE_KR)
    chart = await GrowthChart.async_from_profile(hass, profile)
    vaccine_schedule = await async_load_vaccine_schedule(hass, profile)
    checkup_schedule = await async_load_checkup_schedule_for_profile(hass, profile)
    tuition_table = (
        await async_load_tuition_table(hass) if profile == PROFILE_KR else None
    )

    coordinator = BabyKitCoordinator(
        hass,
        entry,
        chart=chart,
        nip_schedule=vaccine_schedule,
        checkup_schedule=checkup_schedule,
        tuition_table=tuition_table,
        profile=profile,
    )
    await coordinator.async_config_entry_first_refresh()

    unregister_llm = await async_setup_llm_api(
        hass,
        entry,
        child_id=entry.data.get(CONF_CHILD_ID, entry.entry_id),
        child_name=entry.data[CONF_CHILD_NAME],
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "unregister_llm": unregister_llm,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_register_services(hass)
    async_register_websocket_api(hass)
    await async_register_panel(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    # Armed last so a failed setup never leaves a timer behind.
    entry.async_on_unload(coordinator.async_schedule_midnight_refresh())
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        store = hass.data[DOMAIN].pop(entry.entry_id, {}) or {}
        async_cleanup_llm_api(store.get("unregister_llm"))
        async_unregister_services(hass)
        async_unregister_panel(hass)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Deleting a child entry also deletes that child's stored records."""
    from .storage import async_remove_child_data

    await async_remove_child_data(
        hass, entry.data.get(CONF_CHILD_ID, entry.entry_id)
    )
