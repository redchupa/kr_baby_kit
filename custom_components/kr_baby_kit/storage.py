"""Per-child persistence (HA Store backed, plain JSON under ``.storage/``).

Two stores:

* measurement records — ``{child_id: [{date, height?, weight?, head?}, ...]}``
* completed schedule events — ``{child_id: {event_id: {"date": iso}}}``

Every read-modify-write runs under one ``asyncio.Lock`` and goes through a
single cached ``Store`` instance per key. Before v0.9.0 each call built a new
``Store`` and two quick writes (e.g. height + weight number entities set
back-to-back) could interleave and drop one of the values.
"""
from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    STORAGE_KEY_COMPLETIONS,
    STORAGE_KEY_RECORDS,
    STORAGE_VERSION,
)
from .validation import validate_measurement

_RUNTIME_KEY = f"{DOMAIN}_storage_runtime"
_MEASUREMENT_FIELDS: tuple[str, ...] = ("height", "weight", "head")


def _runtime(hass: HomeAssistant) -> dict[str, Any]:
    return hass.data.setdefault(_RUNTIME_KEY, {})


def _store(hass: HomeAssistant) -> Store:
    rt = _runtime(hass)
    if "records" not in rt:
        rt["records"] = Store(hass, STORAGE_VERSION, f"{DOMAIN}_{STORAGE_KEY_RECORDS}")
    return rt["records"]


def _completions_store(hass: HomeAssistant) -> Store:
    rt = _runtime(hass)
    if "completions" not in rt:
        rt["completions"] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}_{STORAGE_KEY_COMPLETIONS}"
        )
    return rt["completions"]


def _lock(hass: HomeAssistant) -> asyncio.Lock:
    rt = _runtime(hass)
    if "lock" not in rt:
        rt["lock"] = asyncio.Lock()
    return rt["lock"]


def _validate_date(value: str, label: str = "측정일") -> str:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError) as err:
        raise ValueError(
            f"{label} 형식이 올바르지 않습니다 (YYYY-MM-DD): {value!r}"
        ) from err
    return value


# ---------------------------------------------------------------- records


async def async_load_records(hass: HomeAssistant) -> dict[str, list[dict[str, Any]]]:
    raw = await _store(hass).async_load()
    return raw or {}


async def async_save_records(hass: HomeAssistant, records: dict) -> None:
    await _store(hass).async_save(records)


async def async_get_child_records(
    hass: HomeAssistant, child_id: str
) -> list[dict[str, Any]]:
    """Return a copy of one child's records, oldest first."""
    records = await async_load_records(hass)
    return [dict(r) for r in records.get(child_id, [])]


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
    _validate_date(measurement_date)

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

    async with _lock(hass):
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
        return dict(entry)


async def async_delete_measurement(
    hass: HomeAssistant,
    child_id: str,
    measurement_date: str,
    kinds: list[str] | None = None,
) -> dict[str, Any]:
    """Delete a whole record (``kinds`` empty) or just some of its fields.

    Returns ``{"date", "removed": [...], "remaining": {...} | None}``.
    Raises ``ValueError`` when nothing matches.
    """
    if not child_id:
        raise ValueError("child_id is required")
    _validate_date(measurement_date)
    wanted = list(kinds or [])
    for kind in wanted:
        if kind not in _MEASUREMENT_FIELDS:
            raise ValueError(f"알 수 없는 측정 항목: {kind!r}")

    async with _lock(hass):
        records = await async_load_records(hass)
        child_records = records.get(child_id, [])
        existing = next(
            (r for r in child_records if r.get("date") == measurement_date), None
        )
        if existing is None:
            raise ValueError(f"{measurement_date} 측정 기록이 없습니다.")

        if not wanted:
            removed = [k for k in _MEASUREMENT_FIELDS if k in existing]
            child_records.remove(existing)
            remaining = None
        else:
            removed = [k for k in wanted if k in existing]
            if not removed:
                raise ValueError(
                    f"{measurement_date} 기록에 삭제할 항목({', '.join(wanted)})이 없습니다."
                )
            for k in removed:
                existing.pop(k, None)
            if any(k in existing for k in _MEASUREMENT_FIELDS):
                remaining = dict(existing)
            else:
                child_records.remove(existing)
                remaining = None

        if not child_records:
            records.pop(child_id, None)
        await async_save_records(hass, records)
        return {"date": measurement_date, "removed": removed, "remaining": remaining}


# ------------------------------------------------------------ completions


async def async_load_completions(
    hass: HomeAssistant,
) -> dict[str, dict[str, dict[str, Any]]]:
    raw = await _completions_store(hass).async_load()
    return raw or {}


async def async_get_child_completions(
    hass: HomeAssistant, child_id: str
) -> dict[str, dict[str, Any]]:
    data = await async_load_completions(hass)
    return {k: dict(v) for k, v in (data.get(child_id) or {}).items()}


async def async_mark_completed(
    hass: HomeAssistant,
    child_id: str,
    event_ids: list[str],
    done_date: str,
) -> dict[str, dict[str, Any]]:
    """Mark one or more schedule events as done on ``done_date``."""
    if not child_id:
        raise ValueError("child_id is required")
    if not event_ids:
        raise ValueError("event_id 를 하나 이상 지정해 주세요.")
    _validate_date(done_date, "완료일")
    async with _lock(hass):
        data = await async_load_completions(hass)
        child = data.setdefault(child_id, {})
        for event_id in event_ids:
            child[event_id] = {"date": done_date}
        await _completions_store(hass).async_save(data)
        return {k: dict(child[k]) for k in event_ids}


async def async_unmark_completed(
    hass: HomeAssistant, child_id: str, event_ids: list[str]
) -> list[str]:
    """Undo completion marks. Returns the ids that were actually removed."""
    if not child_id:
        raise ValueError("child_id is required")
    async with _lock(hass):
        data = await async_load_completions(hass)
        child = data.get(child_id) or {}
        removed = [e for e in event_ids if child.pop(e, None) is not None]
        if not child:
            data.pop(child_id, None)
        if removed:
            await _completions_store(hass).async_save(data)
        return removed


# ---------------------------------------------------------------- cleanup


async def async_remove_child_data(hass: HomeAssistant, child_id: str) -> None:
    """Drop every record and completion mark for a deleted child entry."""
    async with _lock(hass):
        records = await async_load_records(hass)
        if records.pop(child_id, None) is not None:
            await async_save_records(hass, records)
        completions = await async_load_completions(hass)
        if completions.pop(child_id, None) is not None:
            await _completions_store(hass).async_save(completions)


def latest(records: list[dict], kind: str) -> dict | None:
    for entry in reversed(records or []):
        if entry.get(kind) is not None:
            return entry
    return None
