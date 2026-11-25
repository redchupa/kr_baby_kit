"""WebSocket API backing the kr_baby_kit Home Assistant sidebar panel."""
from __future__ import annotations

from datetime import date
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
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
    attribution_for,
    disclaimer_for,
    is_korean,
)
from .schedule import event_to_dict
from .storage import latest


def _default_median(coordinator, kind: str, step: float, lo: float, hi: float) -> float | None:
    age_m = (coordinator.data or {}).get("age_months")
    if age_m is None:
        return None
    pt = coordinator.chart.lookup(coordinator.child_sex, kind, max(0.0, float(age_m)))
    if pt is None:
        return None
    rounded = round(round(pt.M / step) * step, 2)
    return min(hi, max(lo, rounded))


def _serialize_child(hass: HomeAssistant, entry_id: str, coordinator) -> dict[str, Any]:
    data = coordinator.data or {}
    records = data.get("records") or []
    completed = data.get("completed") or {}
    today = date.fromisoformat(data["today"]) if data.get("today") else dt_util.now().date()
    ko = is_korean(hass)

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
        "age_months": round(float(data.get("age_months", 0.0)), 2),
        "today": today.isoformat(),
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
        "attribution": attribution_for(coordinator.profile, korean=ko),
        "disclaimer": disclaimer_for(korean=ko),
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/get_overview",
    }
)
@callback
def ws_get_overview(
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
        children.append(_serialize_child(hass, entry_id, coord))
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


def async_register_websocket_api(hass: HomeAssistant) -> None:
    """Register websocket commands once per Home Assistant instance."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("_ws_registered"):
        return
    websocket_api.async_register_command(hass, ws_get_overview)
    websocket_api.async_register_command(hass, ws_add_child)
    websocket_api.async_register_command(hass, ws_update_child)
    websocket_api.async_register_command(hass, ws_delete_child)
    domain_data["_ws_registered"] = True
