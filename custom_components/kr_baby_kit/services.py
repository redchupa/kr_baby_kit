"""kr_baby_kit services — record_measurement."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError

from .const import CONF_CHILD_ID, DOMAIN, LOGGER
from .storage import async_append_measurement

SERVICE_RECORD_MEASUREMENT = "record_measurement"

_RECORD_SCHEMA = vol.Schema(
    {
        vol.Optional("child_id"): str,
        vol.Required("date"): str,
        vol.Optional("height"): vol.Coerce(float),
        vol.Optional("weight"): vol.Coerce(float),
        vol.Optional("head"): vol.Coerce(float),
    }
)


def _entries(hass: HomeAssistant) -> dict[str, dict]:
    return hass.data.get(DOMAIN, {})


def _resolve_child_id(hass: HomeAssistant, requested: str | None) -> str:
    entries = _entries(hass)
    if requested:
        # Match either entry_id or stored child_id.
        for store in entries.values():
            coordinator = store.get("coordinator")
            if coordinator and coordinator.child_id == requested:
                return coordinator.child_id
        if requested in entries:
            return entries[requested]["coordinator"].child_id
        raise HomeAssistantError(f"등록되지 않은 child_id: {requested}")
    if len(entries) == 1:
        return next(iter(entries.values()))["coordinator"].child_id
    raise HomeAssistantError(
        "여러 자녀가 등록되어 있습니다. child_id 를 지정해 주세요."
    )


def _coordinator_for(hass: HomeAssistant, child_id: str):
    for store in _entries(hass).values():
        coordinator = store.get("coordinator")
        if coordinator and coordinator.child_id == child_id:
            return coordinator
    return None


def async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_RECORD_MEASUREMENT):
        return

    async def _handle_record(call: ServiceCall) -> ServiceResponse:
        data = call.data
        child_id = _resolve_child_id(hass, data.get(CONF_CHILD_ID))
        try:
            entry = await async_append_measurement(
                hass,
                child_id=child_id,
                measurement_date=data["date"],
                height=data.get("height"),
                weight=data.get("weight"),
                head=data.get("head"),
            )
        except ValueError as err:
            raise HomeAssistantError(str(err)) from err

        coordinator = _coordinator_for(hass, child_id)
        if coordinator is not None:
            await coordinator.async_request_refresh()
        LOGGER.debug("recorded measurement for %s: %s", child_id, entry)
        return {"child_id": child_id, "record": entry}

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_MEASUREMENT,
        _handle_record,
        schema=_RECORD_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )


def async_unregister_services(hass: HomeAssistant) -> None:
    # Only deregister if this was the last entry.
    if _entries(hass):
        return
    hass.services.async_remove(DOMAIN, SERVICE_RECORD_MEASUREMENT)
