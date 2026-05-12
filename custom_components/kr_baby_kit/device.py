"""Device descriptor — one device per registered child."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    CONF_CHILD_ID,
    CONF_CHILD_NAME,
    DOMAIN,
    DONATION_MANUFACTURER,
    DONATION_MODEL,
    DONATION_SW_VERSION,
)


def child_device(entry: ConfigEntry) -> DeviceInfo:
    cid = entry.data.get(CONF_CHILD_ID, entry.entry_id)
    return DeviceInfo(
        identifiers={(DOMAIN, f"child_{cid}")},
        name=entry.data.get(CONF_CHILD_NAME, "Child"),
        manufacturer=DONATION_MANUFACTURER,
        model=DONATION_MODEL,
        sw_version=DONATION_SW_VERSION,
        entry_type=dr.DeviceEntryType.SERVICE,
    )
