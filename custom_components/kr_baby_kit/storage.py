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
import base64
import shutil
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    ACTIVITY_KINDS,
    DOMAIN,
    MEDIA_SUBDIR,
    STORAGE_KEY_ACTIVITIES,
    STORAGE_KEY_COMPLETIONS,
    STORAGE_KEY_PROFILES,
    STORAGE_KEY_RECORDS,
    STORAGE_KEY_TIMERS,
    STORAGE_VERSION,
    TIMER_KINDS,
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


def _activities_store(hass: HomeAssistant) -> Store:
    rt = _runtime(hass)
    if "activities" not in rt:
        rt["activities"] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}_{STORAGE_KEY_ACTIVITIES}"
        )
    return rt["activities"]


def _timers_store(hass: HomeAssistant) -> Store:
    rt = _runtime(hass)
    if "timers" not in rt:
        rt["timers"] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}_{STORAGE_KEY_TIMERS}"
        )
    return rt["timers"]


def _profiles_store(hass: HomeAssistant) -> Store:
    rt = _runtime(hass)
    if "profiles" not in rt:
        rt["profiles"] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}_{STORAGE_KEY_PROFILES}"
        )
    return rt["profiles"]


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


# ------------------------------------------------------- activities / timers / photos

_MAX_PHOTO_BYTES = 5 * 1024 * 1024  # 5 MB safety limit
_ALLOWED_MIME_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _safe_child_dir_name(child_id: str) -> str:
    cleaned = "".join(ch for ch in str(child_id) if ch.isalnum() or ch in ("_", "-"))
    if not cleaned:
        raise ValueError("Invalid child_id")
    return cleaned


def _decode_data_url(data_url: str) -> tuple[bytes, str]:
    """Decode a base64 image data URL into (raw_bytes, file_extension)."""
    if not isinstance(data_url, str) or not data_url.startswith("data:image/"):
        raise ValueError("Invalid image data URL.")
    try:
        header, b64 = data_url.split(",", 1)
    except ValueError as err:
        raise ValueError("Malformed image data URL.") from err
    mime = header[5:].split(";", 1)[0].strip().lower()
    ext = _ALLOWED_MIME_EXT.get(mime)
    if ext is None:
        raise ValueError(f"Unsupported image type: {mime}")
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception as err:
        raise ValueError("Invalid base64 image payload.") from err
    if not raw or len(raw) > _MAX_PHOTO_BYTES:
        raise ValueError("Image size must be between 1 byte and 5 MB.")
    return raw, ext


def _write_photo_sync(base_dir: Path, child_dir: str, raw: bytes, ext: str) -> str:
    target_dir = base_dir / child_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{uuid.uuid4().hex[:16]}{ext}"
    (target_dir / fname).write_bytes(raw)
    return f"/local/{MEDIA_SUBDIR}/{child_dir}/{fname}"


def _delete_photo_sync(base_dir: Path, photo_url: str) -> None:
    prefix = f"/local/{MEDIA_SUBDIR}/"
    if not photo_url or not photo_url.startswith(prefix):
        return
    rel = photo_url[len(prefix):]
    target = (base_dir / rel).resolve()
    try:
        target.relative_to(base_dir.resolve())
    except ValueError:
        return
    if target.is_file():
        target.unlink(missing_ok=True)


async def async_save_photo(
    hass: HomeAssistant, child_id: str, data_url: str
) -> str:
    """Persist an uploaded photo under ``<config>/www/kr_baby_kit_media/<child_id>/``."""
    raw, ext = _decode_data_url(data_url)
    child_dir = _safe_child_dir_name(child_id)
    base_dir = Path(hass.config.path("www", MEDIA_SUBDIR))
    return await hass.async_add_executor_job(
        _write_photo_sync, base_dir, child_dir, raw, ext
    )


async def async_get_child_profile_meta(
    hass: HomeAssistant, child_id: str
) -> dict[str, Any]:
    data = await _profiles_store(hass).async_load() or {}
    return dict(data.get(child_id) or {})


async def async_set_child_avatar(
    hass: HomeAssistant, child_id: str, data_url: str | None
) -> str | None:
    """Save (or clear when None) a child's profile photo URL."""
    new_url = await async_save_photo(hass, child_id, data_url) if data_url else None
    base_dir = Path(hass.config.path("www", MEDIA_SUBDIR))
    async with _lock(hass):
        data = await _profiles_store(hass).async_load() or {}
        meta = dict(data.get(child_id) or {})
        old_url = meta.get("avatar_url")
        if new_url:
            meta["avatar_url"] = new_url
            data[child_id] = meta
        else:
            meta.pop("avatar_url", None)
            if meta:
                data[child_id] = meta
            else:
                data.pop(child_id, None)
        await _profiles_store(hass).async_save(data)
    if old_url and old_url != new_url:
        await hass.async_add_executor_job(_delete_photo_sync, base_dir, old_url)
    return new_url


async def async_get_child_activities(
    hass: HomeAssistant, child_id: str
) -> list[dict[str, Any]]:
    data = await _activities_store(hass).async_load() or {}
    items = [dict(a) for a in data.get(child_id, [])]
    items.sort(key=lambda a: a.get("timestamp", ""), reverse=True)
    return items


async def async_add_activity(
    hass: HomeAssistant,
    child_id: str,
    kind: str,
    *,
    timestamp: str | None = None,
    duration_min: float | None = None,
    amount_ml: float | None = None,
    method: str | None = None,
    diaper_type: str | None = None,
    temperature_c: float | None = None,
    note: str | None = None,
    photo_data_url: str | None = None,
) -> dict[str, Any]:
    """Append a Baby Buddy–style activity log (with optional photo attachment)."""
    if not child_id:
        raise ValueError("child_id is required")
    if kind not in ACTIVITY_KINDS:
        raise ValueError(f"Unsupported activity kind: {kind!r}")

    temp_val: float | None = None
    if temperature_c is not None:
        temp_val = round(float(temperature_c), 1)
        if not (34.0 <= temp_val <= 43.0):
            raise ValueError("Temperature must be between 34.0 and 43.0 °C.")

    photo_url = (
        await async_save_photo(hass, child_id, photo_data_url)
        if photo_data_url
        else None
    )
    ts = timestamp or dt_util.now().isoformat(timespec="seconds")
    entry: dict[str, Any] = {
        "id": uuid.uuid4().hex[:12],
        "kind": kind,
        "timestamp": ts,
    }
    if duration_min is not None:
        entry["duration_min"] = round(max(0.0, float(duration_min)), 1)
    if amount_ml is not None:
        entry["amount_ml"] = round(max(0.0, float(amount_ml)), 1)
    if method:
        entry["method"] = str(method).strip()
    if diaper_type:
        entry["diaper_type"] = str(diaper_type).strip()
    if temp_val is not None:
        entry["temperature_c"] = temp_val
    if note and str(note).strip():
        entry["note"] = str(note).strip()
    if photo_url:
        entry["photo_url"] = photo_url

    async with _lock(hass):
        data = await _activities_store(hass).async_load() or {}
        items = data.setdefault(child_id, [])
        items.append(entry)
        items.sort(key=lambda a: a.get("timestamp", ""), reverse=True)
        # Keep up to 1000 recent entries per child to keep JSON fast.
        if len(items) > 1000:
            data[child_id] = items[:1000]
        await _activities_store(hass).async_save(data)
    return dict(entry)


async def async_delete_activity(
    hass: HomeAssistant, child_id: str, activity_id: str
) -> bool:
    """Delete an activity log and any attached photo file."""
    base_dir = Path(hass.config.path("www", MEDIA_SUBDIR))
    removed_photo: str | None = None
    found = False
    async with _lock(hass):
        data = await _activities_store(hass).async_load() or {}
        items = data.get(child_id, [])
        kept = []
        for item in items:
            if item.get("id") == activity_id:
                found = True
                removed_photo = item.get("photo_url")
            else:
                kept.append(item)
        if found:
            if kept:
                data[child_id] = kept
            else:
                data.pop(child_id, None)
            await _activities_store(hass).async_save(data)
    if removed_photo:
        await hass.async_add_executor_job(_delete_photo_sync, base_dir, removed_photo)
    return found


async def async_get_child_timers(
    hass: HomeAssistant, child_id: str
) -> dict[str, dict[str, Any]]:
    data = await _timers_store(hass).async_load() or {}
    return {k: dict(v) for k, v in (data.get(child_id) or {}).items()}


async def async_start_timer(
    hass: HomeAssistant, child_id: str, kind: str
) -> dict[str, Any]:
    if kind not in TIMER_KINDS:
        raise ValueError(f"Unsupported timer kind: {kind!r}")
    started_at = dt_util.now().isoformat(timespec="seconds")
    timer_obj = {"kind": kind, "started_at": started_at}
    async with _lock(hass):
        data = await _timers_store(hass).async_load() or {}
        child = data.setdefault(child_id, {})
        child[kind] = timer_obj
        await _timers_store(hass).async_save(data)
    return dict(timer_obj)


async def async_stop_timer(
    hass: HomeAssistant,
    child_id: str,
    kind: str,
    *,
    save_log: bool = True,
    note: str | None = None,
    amount_ml: float | None = None,
    method: str | None = None,
) -> dict[str, Any] | None:
    """Stop an active timer and optionally save it as an activity log."""
    async with _lock(hass):
        data = await _timers_store(hass).async_load() or {}
        child = data.get(child_id) or {}
        timer_obj = child.pop(kind, None)
        if not child:
            data.pop(child_id, None)
        await _timers_store(hass).async_save(data)

    if timer_obj is None:
        return None
    if not save_log:
        return {"cancelled": True, "kind": kind}

    start_dt = dt_util.parse_datetime(timer_obj["started_at"])
    now_dt = dt_util.now()
    duration_min = 0.0
    if start_dt is not None:
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=now_dt.tzinfo)
        duration_min = max(0.1, (now_dt - start_dt).total_seconds() / 60.0)

    return await async_add_activity(
        hass,
        child_id,
        kind,
        timestamp=timer_obj["started_at"],
        duration_min=duration_min,
        amount_ml=amount_ml,
        method=method,
        note=note,
    )


# ---------------------------------------------------------------- cleanup


async def async_remove_child_data(hass: HomeAssistant, child_id: str) -> None:
    """Drop every record, completion mark, activity, timer, and photo for a deleted child."""
    async with _lock(hass):
        records = await async_load_records(hass)
        if records.pop(child_id, None) is not None:
            await async_save_records(hass, records)
        completions = await async_load_completions(hass)
        if completions.pop(child_id, None) is not None:
            await _completions_store(hass).async_save(completions)
        activities = await _activities_store(hass).async_load() or {}
        if activities.pop(child_id, None) is not None:
            await _activities_store(hass).async_save(activities)
        timers = await _timers_store(hass).async_load() or {}
        if timers.pop(child_id, None) is not None:
            await _timers_store(hass).async_save(timers)
        profiles = await _profiles_store(hass).async_load() or {}
        if profiles.pop(child_id, None) is not None:
            await _profiles_store(hass).async_save(profiles)

    try:
        child_dir = _safe_child_dir_name(child_id)
        target = Path(hass.config.path("www", MEDIA_SUBDIR)) / child_dir
        await hass.async_add_executor_job(shutil.rmtree, target, True)
    except Exception:
        pass


def latest(records: list[dict], kind: str) -> dict | None:
    for entry in reversed(records or []):
        if entry.get(kind) is not None:
            return entry
    return None
