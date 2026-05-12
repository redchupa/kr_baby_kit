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
    date.fromisoformat(measurement_date)  # validate

    new_fields: dict[str, Any] = {}
    if height is not None:
        new_fields["height"] = float(height)
    if weight is not None:
        new_fields["weight"] = float(weight)
    if head is not None:
        new_fields["head"] = float(head)
    if not new_fields:
        raise ValueError("at least one measurement value must be provided")

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
