"""kr_baby_kit services — record_measurement."""
from __future__ import annotations

import math

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
from .validation import measurement_range

SERVICE_RECORD_MEASUREMENT = "record_measurement"


def _bounded_float(kind: str):
    """Schema fragment: coerce to float, reject NaN/Inf, enforce kind's range.

    The storage layer re-validates with the same bounds via
    ``validation.validate_measurement`` — this schema rejects bad input
    early so the service-call response carries a clean voluptuous error,
    but is not the authoritative check.
    """
    lo, hi = measurement_range(kind)

    def _coerce(value):
        if isinstance(value, bool):
            raise vol.Invalid(f"{kind} 값은 숫자여야 합니다 (참/거짓 X).")
        try:
            v = float(value)
        except (TypeError, ValueError) as err:
            raise vol.Invalid(
                f"{kind} 값을 숫자로 읽지 못했습니다: {value!r}"
            ) from err
        if math.isnan(v) or math.isinf(v):
            raise vol.Invalid(f"{kind} 값이 NaN/Infinity 입니다.")
        if v < lo or v > hi:
            raise vol.Invalid(
                f"{kind} 값이 허용 범위를 벗어났습니다: {v} (허용: {lo}–{hi})."
            )
        return v

    return _coerce


_RECORD_SCHEMA = vol.Schema(
    {
        vol.Optional("child_id"): str,
        vol.Required("date"): str,
        vol.Optional("height"): _bounded_float("height"),
        vol.Optional("weight"): _bounded_float("weight"),
        vol.Optional("head"): _bounded_float("head"),
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
