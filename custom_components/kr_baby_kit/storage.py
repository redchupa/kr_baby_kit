"""Per-child measurement record storage (HA Store backed)."""
from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    STORAGE_KEY_RECORDS,
    STORAGE_VERSION,
)
from .validation import validate_measurement


def _store(hass: HomeAssistant) -> Store:
    return Store(hass, STORAGE_VERSION, f"{DOMAIN}_{STORAGE_KEY_RECORDS}")


async def async_load_records(hass: HomeAssistant) -> dict[str, list[dict[str, Any]]]:
    raw = await _store(hass).async_load()
    return raw or {}


async def async_save_records(hass: HomeAssistant, records: dict) -> None:
    await _store(hass).async_save(records)


async def async_append_measurement(
    hass: HomeAssistant,
    child_id: str,
    measurement_date: str,
    height: float | None = None,
    weight: float | None = None,
    head: float | None = None,
) -> dict:
    """Persist a measurement. If a record for the same date already exists,
    merge the provided fields into it instead of creating a duplicate.
    """
    if not child_id:
        raise ValueError("child_id is required")
    try:
        date.fromisoformat(measurement_date)  # validate
    except (TypeError, ValueError) as err:
        raise ValueError(
            f"측정일 형식이 올바르지 않습니다 (YYYY-MM-DD): {measurement_date!r}"
        ) from err

    # Validate each provided measurement through the central helper. This is
    # the last line of defence: the service-call schema and the dashboard
    # number entity also validate, but persistence must never store an
    # implausible value regardless of how it arrived.
    new_fields: dict[str, Any] = {}
    if height is not None:
        new_fields["height"] = validate_measurement("height", height)
    if weight is not None:
        new_fields["weight"] = validate_measurement("weight", weight)
    if head is not None:
        new_fields["head"] = validate_measurement("head", head)
    if not new_fields:
        raise ValueError("키·몸무게·머리둘레 중 최소 한 값은 입력되어야 합니다.")

    records = await async_load_records(hass)
    child_records = records.setdefault(child_id, [])

    existing = next(
        (r for r in child_records if r.get("date") == measurement_date), None
    )
    if existing is not None:
        existing.update(new_fields)
        entry = existing
    else:
        entry = {"date": measurement_date, **new_fields}
        child_records.append(entry)

    child_records.sort(key=lambda r: r["date"])
    await async_save_records(hass, records)
    return entry


def latest(records: list[dict], kind: str) -> dict | None:
    for entry in reversed(records or []):
        if entry.get(kind) is not None:
            return entry
    return None
