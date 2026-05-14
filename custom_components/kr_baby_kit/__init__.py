"""한국 영유아 키트 (Korean Baby Kit) — HACS integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_CHILD_ID, CONF_CHILD_NAME, DOMAIN, LOGGER  # noqa: F401  (LOGGER re-exported)
from .llm_api import async_cleanup_llm_api, async_setup_llm_api
from .services import async_register_services, async_unregister_services

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
    from .schedule import async_load_checkup_schedule, async_load_nip_schedule

    chart = await GrowthChart.async_from_default(hass)
    nip_schedule = await async_load_nip_schedule(hass)
    checkup_schedule = await async_load_checkup_schedule(hass)
    tuition_table = await async_load_tuition_table(hass)

    coordinator = BabyKitCoordinator(
        hass,
        entry,
        chart=chart,
        nip_schedule=nip_schedule,
        checkup_schedule=checkup_schedule,
        tuition_table=tuition_table,
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
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        store = hass.data[DOMAIN].pop(entry.entry_id, {}) or {}
        async_cleanup_llm_api(store.get("unregister_llm"))
        async_unregister_services(hass)
    return unload_ok
