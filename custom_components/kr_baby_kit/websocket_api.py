"""WebSocket API backing the kr_baby_kit Home Assistant sidebar panel."""
from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import (
    ACTIVITY_KINDS,
    CONF_CHILD_BIRTHDATE,
    CONF_CHILD_NAME,
    CONF_CHILD_SEX,
    CONF_PROFILE,
    DEFAULT_BIRTHDATE,
    DOMAIN,
    PROFILE_KR,
    PROFILE_OPTIONS,
    SEX_FEMALE,
    SEX_MALE,
    TIMER_KINDS,
    attribution_for,
    disclaimer_for,
    is_korean,
)
from .schedule import event_to_dict
from .storage import (
    async_add_activity,
    async_delete_activity,
    async_get_child_activities,
    async_get_child_profile_meta,
    async_get_child_timers,
    async_set_child_avatar,
    async_start_timer,
    async_stop_timer,
    latest,
)


def _default_median(coordinator, kind: str, step: float, lo: float, hi: float) -> float | None:
    age_m = (coordinator.data or {}).get("age_months")
    if age_m is None:
        return None
    pt = coordinator.chart.lookup(coordinator.child_sex, kind, max(0.0, float(age_m)))
    if pt is None:
        return None
    rounded = round(round(pt.M / step) * step, 2)
    return min(hi, max(lo, rounded))


def compute_today_summary(activities: list[dict[str, Any]], today_iso: str) -> dict[str, Any]:
    """Compute Baby Buddy–style daily totals for ``today_iso`` (YYYY-MM-DD)."""
    sleep_min = 0.0
    feeding_count = 0
    feeding_ml = 0.0
    diaper_wet = 0
    diaper_solid = 0
    tummy_min = 0.0
    pumping_ml = 0.0
    last_temp_c: float | None = None
    photo_count = 0

    for item in activities:
        if item.get("photo_url"):
            photo_count += 1
        ts = str(item.get("timestamp") or "")
        if not ts.startswith(today_iso):
            continue
        kind = item.get("kind")
        if kind == "sleep":
            sleep_min += float(item.get("duration_min") or 0.0)
        elif kind == "feeding":
            feeding_count += 1
            feeding_ml += float(item.get("amount_ml") or 0.0)
        elif kind == "diaper":
            dtype = item.get("diaper_type") or "wet"
            if dtype in ("wet", "both"):
                diaper_wet += 1
            if dtype in ("solid", "both"):
                diaper_solid += 1
        elif kind == "tummy_time":
            tummy_min += float(item.get("duration_min") or 0.0)
        elif kind == "pumping":
            pumping_ml += float(item.get("amount_ml") or 0.0)
        elif kind == "temperature" and last_temp_c is None and item.get("temperature_c") is not None:
            last_temp_c = float(item["temperature_c"])

    return {
        "sleep_min": round(sleep_min, 1),
        "feeding_count": feeding_count,
        "feeding_ml": round(feeding_ml, 1),
        "diaper_wet": diaper_wet,
        "diaper_solid": diaper_solid,
        "tummy_min": round(tummy_min, 1),
        "pumping_ml": round(pumping_ml, 1),
        "last_temp_c": last_temp_c,
        "photo_count": photo_count,
    }


def _serialize_child(
    hass: HomeAssistant,
    entry_id: str,
    coordinator,
    *,
    avatar_url: str | None = None,
    activities: list[dict[str, Any]] | None = None,
    timers: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    data = coordinator.data or {}
    records = data.get("records") or []
    completed = data.get("completed") or {}
    today = date.fromisoformat(data["today"]) if data.get("today") else dt_util.now().date()
    today_iso = today.isoformat()
    ko = is_korean(hass)
    act_list = activities or []

    specs = (
        ("height", 0.1, 30.0, 200.0),
        ("weight", 0.05, 1.0, 100.0),
        ("head", 0.1, 25.0, 65.0),
    )
    inputs: dict[str, dict[str, Any]] = {}
    for kind, step, lo, hi in specs:
        last = latest(records, kind)
        if last:
            inputs[kind] = {
                "value": float(last[kind]),
                "is_default_median": False,
                "measured_at": last["date"],
            }
        else:
            inputs[kind] = {
                "value": _default_median(coordinator, kind, step, lo, hi),
                "is_default_median": True,
                "measured_at": None,
            }

    def _dump(events):
        return [event_to_dict(e, today, completed) for e in events]

    return {
        "entry_id": entry_id,
        "child_id": coordinator.child_id,
        "name": coordinator.child_name,
        "birthdate": coordinator.birthdate.isoformat(),
        "sex": coordinator.child_sex,
        "profile": coordinator.profile,
        "avatar_url": avatar_url,
        "age_months": round(float(data.get("age_months", 0.0)), 2),
        "today": today_iso,
        "inputs": inputs,
        "percentiles": data.get("percentiles") or {},
        "weight_for_length": data.get("weight_for_length"),
        "bmi_raw": data.get("bmi_raw"),
        "bmi_measured_at": data.get("bmi_measured_at"),
        "bmi_age_months": data.get("bmi_age_months"),
        "care_tuition": data.get("care_tuition"),
        "vaccines": _dump(coordinator.all_vaccines),
        "checkups": _dump(coordinator.all_checkups),
        "oral_checkups": _dump(coordinator.all_oral_checkups),
        "records": records[-20:],
        "activities": act_list[:100],
        "timers": timers or {},
        "today_summary": compute_today_summary(act_list, today_iso),
        "attribution": attribution_for(coordinator.profile, korean=ko),
        "disclaimer": disclaimer_for(korean=ko),
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_overview",
    }
)
@websocket_api.async_response
async def ws_get_overview(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return all registered children and their derived data for the panel."""
    domain_data = hass.data.get(DOMAIN) or {}
    children = []
    for entry_id, store in domain_data.items():
        if not isinstance(store, dict):
            continue
        coord = store.get("coordinator")
        if coord is None:
            continue
        meta = await async_get_child_profile_meta(hass, coord.child_id)
        activities = await async_get_child_activities(hass, coord.child_id)
        timers = await async_get_child_timers(hass, coord.child_id)
        children.append(
            _serialize_child(
                hass,
                entry_id,
                coord,
                avatar_url=meta.get("avatar_url"),
                activities=activities,
                timers=timers,
            )
        )
    children.sort(key=lambda c: (c["name"], c["child_id"]))
    connection.send_result(
        msg["id"],
        {
            "default_birthdate": DEFAULT_BIRTHDATE,
            "language": getattr(hass.config, "language", "ko") or "ko",
            "children": children,
        },
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/add_child",
        vol.Required("child_name"): str,
        vol.Optional("child_birthdate", default=DEFAULT_BIRTHDATE): str,
        vol.Required("child_sex"): vol.In([SEX_MALE, SEX_FEMALE]),
        vol.Optional("profile", default=PROFILE_KR): vol.In(PROFILE_OPTIONS),
    }
)
@websocket_api.async_response
async def ws_add_child(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Create a new child config entry from the sidebar panel."""
    name = msg["child_name"].strip()
    bd = msg["child_birthdate"].strip()
    if not name:
        connection.send_error(msg["id"], "invalid_name", "Child name is required.")
        return
    try:
        if date.fromisoformat(bd) > dt_util.now().date():
            connection.send_error(
                msg["id"], "future_date", "Future dates are not allowed."
            )
            return
    except ValueError:
        connection.send_error(
            msg["id"], "invalid_date", "Invalid date format (YYYY-MM-DD)."
        )
        return

    init_res = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    flow_id = init_res.get("flow_id")
    if not flow_id:
        connection.send_error(msg["id"], "flow_failed", "Failed to start config flow.")
        return
    result = await hass.config_entries.flow.async_configure(
        flow_id,
        {
            CONF_CHILD_NAME: name,
            CONF_CHILD_BIRTHDATE: bd,
            CONF_CHILD_SEX: msg["child_sex"],
            CONF_PROFILE: msg["profile"],
        },
    )
    if result.get("type") != "create_entry":
        connection.send_error(
            msg["id"],
            "create_failed",
            f"Could not add child: {result.get('errors') or result.get('reason')}",
        )
        return
    entry = result.get("result")
    connection.send_result(
        msg["id"],
        {"entry_id": entry.entry_id if entry is not None else None},
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/update_child",
        vol.Required("entry_id"): str,
        vol.Required("child_name"): str,
        vol.Required("child_birthdate"): str,
        vol.Required("child_sex"): vol.In([SEX_MALE, SEX_FEMALE]),
        vol.Required("profile"): vol.In(PROFILE_OPTIONS),
    }
)
@websocket_api.async_response
async def ws_update_child(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Update a child's name, birthdate, sex, or profile and reload."""
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_found", "Child entry not found.")
        return
    name = msg["child_name"].strip()
    bd = msg["child_birthdate"].strip()
    if not name:
        connection.send_error(msg["id"], "invalid_name", "Child name is required.")
        return
    try:
        if date.fromisoformat(bd) > dt_util.now().date():
            connection.send_error(
                msg["id"], "future_date", "Future dates are not allowed."
            )
            return
    except ValueError:
        connection.send_error(
            msg["id"], "invalid_date", "Invalid date format (YYYY-MM-DD)."
        )
        return

    new_data = {
        **entry.data,
        CONF_CHILD_NAME: name,
        CONF_CHILD_BIRTHDATE: bd,
        CONF_CHILD_SEX: msg["child_sex"],
        CONF_PROFILE: msg["profile"],
    }
    hass.config_entries.async_update_entry(entry, data=new_data, title=name)
    await hass.config_entries.async_reload(entry.entry_id)
    connection.send_result(msg["id"], {"entry_id": entry.entry_id})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_child",
        vol.Required("entry_id"): str,
    }
)
@websocket_api.async_response
async def ws_delete_child(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete a child config entry (and its stored records via async_remove_entry)."""
    entry = hass.config_entries.async_get_entry(msg["entry_id"])
    if entry is None or entry.domain != DOMAIN:
        connection.send_error(msg["id"], "not_found", "Child entry not found.")
        return
    await hass.config_entries.async_remove(entry.entry_id)
    connection.send_result(msg["id"], {"deleted": msg["entry_id"]})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/set_avatar",
        vol.Required("child_id"): str,
        vol.Optional("photo_data_url"): vol.Any(str, None),
    }
)
@websocket_api.async_response
async def ws_set_avatar(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Upload or clear a child's profile photo."""
    try:
        url = await async_set_child_avatar(
            hass, msg["child_id"], msg.get("photo_data_url")
        )
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_photo", str(err))
        return
    connection.send_result(msg["id"], {"avatar_url": url})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/add_activity",
        vol.Required("child_id"): str,
        vol.Required("kind"): vol.In(ACTIVITY_KINDS),
        vol.Optional("timestamp"): str,
        vol.Optional("duration_min"): vol.Coerce(float),
        vol.Optional("amount_ml"): vol.Coerce(float),
        vol.Optional("method"): str,
        vol.Optional("diaper_type"): str,
        vol.Optional("temperature_c"): vol.Coerce(float),
        vol.Optional("note"): str,
        vol.Optional("photo_data_url"): str,
    }
)
@websocket_api.async_response
async def ws_add_activity(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Log a sleep, feeding, diaper, tummy time, pumping, temperature, or photo note."""
    try:
        entry = await async_add_activity(
            hass,
            msg["child_id"],
            msg["kind"],
            timestamp=msg.get("timestamp"),
            duration_min=msg.get("duration_min"),
            amount_ml=msg.get("amount_ml"),
            method=msg.get("method"),
            diaper_type=msg.get("diaper_type"),
            temperature_c=msg.get("temperature_c"),
            note=msg.get("note"),
            photo_data_url=msg.get("photo_data_url"),
        )
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_activity", str(err))
        return
    connection.send_result(msg["id"], {"activity": entry})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/delete_activity",
        vol.Required("child_id"): str,
        vol.Required("activity_id"): str,
    }
)
@websocket_api.async_response
async def ws_delete_activity(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Delete an activity log and any attached photo."""
    ok = await async_delete_activity(hass, msg["child_id"], msg["activity_id"])
    connection.send_result(msg["id"], {"deleted": ok})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/start_timer",
        vol.Required("child_id"): str,
        vol.Required("kind"): vol.In(TIMER_KINDS),
    }
)
@websocket_api.async_response
async def ws_start_timer(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Start a live stopwatch timer for sleep, feeding, tummy time, or pumping."""
    try:
        timer_obj = await async_start_timer(hass, msg["child_id"], msg["kind"])
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_timer", str(err))
        return
    connection.send_result(msg["id"], {"timer": timer_obj})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/stop_timer",
        vol.Required("child_id"): str,
        vol.Required("kind"): vol.In(TIMER_KINDS),
        vol.Optional("save_log", default=True): bool,
        vol.Optional("note"): str,
        vol.Optional("amount_ml"): vol.Coerce(float),
        vol.Optional("method"): str,
    }
)
@websocket_api.async_response
async def ws_stop_timer(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Stop an active timer and save it as an activity log."""
    res = await async_stop_timer(
        hass,
        msg["child_id"],
        msg["kind"],
        save_log=msg.get("save_log", True),
        note=msg.get("note"),
        amount_ml=msg.get("amount_ml"),
        method=msg.get("method"),
    )
    connection.send_result(msg["id"], {"result": res})


def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register websocket commands once per Home Assistant instance."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("_ws_registered"):
        return
    websocket_api.async_register_command(hass, ws_get_overview)
    websocket_api.async_register_command(hass, ws_add_child)
    websocket_api.async_register_command(hass, ws_update_child)
    websocket_api.async_register_command(hass, ws_delete_child)
    websocket_api.async_register_command(hass, ws_set_avatar)
    websocket_api.async_register_command(hass, ws_add_activity)
    websocket_api.async_register_command(hass, ws_delete_activity)
    websocket_api.async_register_command(hass, ws_start_timer)
    websocket_api.async_register_command(hass, ws_stop_timer)
    domain_data["_ws_registered"] = True
