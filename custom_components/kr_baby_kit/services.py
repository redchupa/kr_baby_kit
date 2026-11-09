"""kr_baby_kit services.

* ``record_measurement`` — 키·몸무게·머리둘레 기록 (date 생략 시 오늘)
* ``delete_measurement`` — 특정 날짜 기록 전체 또는 일부 항목 삭제
* ``get_measurements`` — 측정 기록 조회 (response only)
* ``mark_event_done`` / ``unmark_event_done`` — 예방접종·검진·구강검진 완료 표시
* ``get_schedule`` — 전체 일정 + event_id + 상태 조회 (response only)
"""
from __future__ import annotations

import math
from datetime import date, datetime

import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .const import CONF_CHILD_ID, DOMAIN, LOGGER, TZ_ASIA_SEOUL
from .schedule import event_to_dict
from .storage import (
    async_append_measurement,
    async_delete_measurement,
    async_get_child_records,
    async_mark_completed,
    async_unmark_completed,
)
from .validation import measurement_range

SERVICE_RECORD_MEASUREMENT = "record_measurement"
SERVICE_DELETE_MEASUREMENT = "delete_measurement"
SERVICE_GET_MEASUREMENTS = "get_measurements"
SERVICE_MARK_EVENT_DONE = "mark_event_done"
SERVICE_UNMARK_EVENT_DONE = "unmark_event_done"
SERVICE_GET_SCHEDULE = "get_schedule"

ALL_SERVICES = (
    SERVICE_RECORD_MEASUREMENT,
    SERVICE_DELETE_MEASUREMENT,
    SERVICE_GET_MEASUREMENTS,
    SERVICE_MARK_EVENT_DONE,
    SERVICE_UNMARK_EVENT_DONE,
    SERVICE_GET_SCHEDULE,
)


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


def _iso_date(value) -> str:
    """Accept a date/datetime/str and normalise to YYYY-MM-DD."""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    try:
        return date.fromisoformat(str(value).strip()).isoformat()
    except ValueError as err:
        raise vol.Invalid(f"날짜 형식이 올바르지 않습니다 (YYYY-MM-DD): {value!r}") from err


def _today() -> str:
    return datetime.now(TZ_ASIA_SEOUL).date().isoformat()


_MEASUREMENT_KIND = vol.In(["height", "weight", "head"])

_RECORD_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CHILD_ID): str,
        vol.Optional("date"): _iso_date,
        vol.Optional("height"): _bounded_float("height"),
        vol.Optional("weight"): _bounded_float("weight"),
        vol.Optional("head"): _bounded_float("head"),
    }
)

_DELETE_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CHILD_ID): str,
        vol.Required("date"): _iso_date,
        vol.Optional("kinds"): vol.All(cv.ensure_list, [_MEASUREMENT_KIND]),
    }
)

_GET_MEASUREMENTS_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CHILD_ID): str,
        vol.Optional("start_date"): _iso_date,
        vol.Optional("end_date"): _iso_date,
    }
)

_MARK_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CHILD_ID): str,
        vol.Required("event_id"): vol.All(cv.ensure_list_csv, [cv.string]),
        vol.Optional("date"): _iso_date,
    }
)

_UNMARK_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_CHILD_ID): str,
        vol.Required("event_id"): vol.All(cv.ensure_list_csv, [cv.string]),
    }
)

_GET_SCHEDULE_SCHEMA = vol.Schema({vol.Optional(CONF_CHILD_ID): str})


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
        raise ServiceValidationError(f"등록되지 않은 child_id: {requested}")
    if len(entries) == 1:
        return next(iter(entries.values()))["coordinator"].child_id
    if not entries:
        raise ServiceValidationError("등록된 자녀가 없습니다.")
    raise ServiceValidationError(
        "여러 자녀가 등록되어 있습니다. child_id 를 지정해 주세요."
    )


def _coordinator_for(hass: HomeAssistant, child_id: str):
    for store in _entries(hass).values():
        coordinator = store.get("coordinator")
        if coordinator and coordinator.child_id == child_id:
            return coordinator
    return None


async def _refresh(hass: HomeAssistant, child_id: str) -> None:
    # Immediate refresh: async_request_refresh() is debounced (~10 s), which
    # left entity state stale right after a service call.
    coordinator = _coordinator_for(hass, child_id)
    if coordinator is not None:
        await coordinator.async_refresh()


def _check_measurement_date(hass: HomeAssistant, child_id: str, iso: str) -> None:
    if iso > _today():
        raise ServiceValidationError(f"미래 날짜에는 기록할 수 없습니다: {iso}")
    coordinator = _coordinator_for(hass, child_id)
    if coordinator is not None and iso < coordinator.birthdate.isoformat():
        raise ServiceValidationError(
            f"측정일({iso})이 생년월일({coordinator.birthdate.isoformat()})보다 빠릅니다."
        )


def async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_RECORD_MEASUREMENT):
        return

    async def _handle_record(call: ServiceCall) -> ServiceResponse:
        data = call.data
        child_id = _resolve_child_id(hass, data.get(CONF_CHILD_ID))
        measurement_date = data.get("date") or _today()
        _check_measurement_date(hass, child_id, measurement_date)
        try:
            entry = await async_append_measurement(
                hass,
                child_id=child_id,
                measurement_date=measurement_date,
                height=data.get("height"),
                weight=data.get("weight"),
                head=data.get("head"),
            )
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err

        await _refresh(hass, child_id)
        LOGGER.debug("recorded measurement for %s: %s", child_id, entry)
        return {"child_id": child_id, "record": entry}

    async def _handle_delete(call: ServiceCall) -> ServiceResponse:
        data = call.data
        child_id = _resolve_child_id(hass, data.get(CONF_CHILD_ID))
        try:
            result = await async_delete_measurement(
                hass,
                child_id=child_id,
                measurement_date=data["date"],
                kinds=data.get("kinds"),
            )
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        await _refresh(hass, child_id)
        return {"child_id": child_id, **result}

    async def _handle_get_measurements(call: ServiceCall) -> ServiceResponse:
        data = call.data
        child_id = _resolve_child_id(hass, data.get(CONF_CHILD_ID))
        records = await async_get_child_records(hass, child_id)
        start = data.get("start_date")
        end = data.get("end_date")
        if start:
            records = [r for r in records if r["date"] >= start]
        if end:
            records = [r for r in records if r["date"] <= end]
        coordinator = _coordinator_for(hass, child_id)
        return {
            "child_id": child_id,
            "child_name": coordinator.child_name if coordinator else None,
            "count": len(records),
            "records": records,
        }

    async def _handle_mark(call: ServiceCall) -> ServiceResponse:
        data = call.data
        child_id = _resolve_child_id(hass, data.get(CONF_CHILD_ID))
        coordinator = _coordinator_for(hass, child_id)
        event_ids: list[str] = [e.strip() for e in data["event_id"] if e.strip()]
        if coordinator is not None:
            unknown = [e for e in event_ids if e not in coordinator.known_event_ids()]
            if unknown:
                raise ServiceValidationError(
                    f"알 수 없는 event_id: {', '.join(unknown)}. "
                    "get_schedule 서비스로 사용 가능한 ID를 확인하세요."
                )
        try:
            marked = await async_mark_completed(
                hass, child_id, event_ids, data.get("date") or _today()
            )
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        await _refresh(hass, child_id)
        return {"child_id": child_id, "completed": marked}

    async def _handle_unmark(call: ServiceCall) -> ServiceResponse:
        data = call.data
        child_id = _resolve_child_id(hass, data.get(CONF_CHILD_ID))
        event_ids = [e.strip() for e in data["event_id"] if e.strip()]
        try:
            removed = await async_unmark_completed(hass, child_id, event_ids)
        except ValueError as err:
            raise ServiceValidationError(str(err)) from err
        await _refresh(hass, child_id)
        return {"child_id": child_id, "removed": removed}

    async def _handle_get_schedule(call: ServiceCall) -> ServiceResponse:
        child_id = _resolve_child_id(hass, call.data.get(CONF_CHILD_ID))
        coordinator = _coordinator_for(hass, child_id)
        if coordinator is None or coordinator.data is None:
            raise HomeAssistantError("데이터 준비 중입니다. 잠시 후 다시 시도하세요.")
        today = date.fromisoformat(coordinator.data["today"])
        completed = coordinator.data.get("completed") or {}

        def _dump(events):
            return [event_to_dict(e, today, completed) for e in events]

        return {
            "child_id": child_id,
            "child_name": coordinator.child_name,
            "today": today.isoformat(),
            "vaccines": _dump(coordinator.all_vaccines),
            "checkups": _dump(coordinator.all_checkups),
            "oral_checkups": _dump(coordinator.all_oral_checkups),
        }

    hass.services.async_register(
        DOMAIN,
        SERVICE_RECORD_MEASUREMENT,
        _handle_record,
        schema=_RECORD_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_DELETE_MEASUREMENT,
        _handle_delete,
        schema=_DELETE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_MEASUREMENTS,
        _handle_get_measurements,
        schema=_GET_MEASUREMENTS_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_MARK_EVENT_DONE,
        _handle_mark,
        schema=_MARK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UNMARK_EVENT_DONE,
        _handle_unmark,
        schema=_UNMARK_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_SCHEDULE,
        _handle_get_schedule,
        schema=_GET_SCHEDULE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


def async_unregister_services(hass: HomeAssistant) -> None:
    # Only deregister if this was the last entry.
    if _entries(hass):
        return
    for service in ALL_SERVICES:
        hass.services.async_remove(DOMAIN, service)
