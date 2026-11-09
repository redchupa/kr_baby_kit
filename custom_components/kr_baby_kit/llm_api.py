"""LLM API — exposes growth / immunization / checkup tools to HA Assist.

Each registered child entry mounts its own llm.API id so the assistant can
pick the right child by name in multi-child households.
"""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any, Callable

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import llm

from .const import DOMAIN, MEDICAL_DISCLAIMER
from .schedule import event_to_dict

_LOGGER = logging.getLogger(__name__)


def _api_id(child_id: str) -> str:
    return f"{DOMAIN}__{child_id}"


def _api_prompt(child_name: str) -> str:
    return (
        f"You can answer questions about the child '{child_name}'. "
        "Use the available tools to look up upcoming immunizations, "
        "upcoming infant/child checkups (영유아 건강검진), infant oral "
        "checkups (영유아 구강검진), which doses/checkups were already "
        "marked as done, the latest growth percentiles, "
        "and the childcare tuition tier (표준보육료 / 정부지원금 / "
        "본인부담금) that applies to the child's age class. Always end "
        "medical-adjacent answers with a brief reminder that this is "
        "reference information, not medical advice. For tuition figures, "
        "remind the user to confirm the current year's published rate "
        "with their daycare or local government."
    )


def _next_event(events: list, today: date) -> dict | None:
    # ``events`` is the coordinator's upcoming list: chronologically sorted
    # and already stripped of completed items.
    for e in events:
        if e.end >= today:
            return event_to_dict(e, today)
    return None


def _events_in_window(events: list, today: date, days: int) -> list[dict]:
    horizon = today + timedelta(days=days)
    return [
        event_to_dict(e, today)
        for e in events
        if not (e.end < today or e.start > horizon)
    ]


class _BabyKitTool(llm.Tool):
    """Common helpers for kr_baby_kit tools."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._entry_id = entry_id

    def _coordinator(self):
        store = self._hass.data.get(DOMAIN, {}).get(self._entry_id) or {}
        return store.get("coordinator")


class GetNextVaccineTool(_BabyKitTool):
    name = "get_next_vaccine"
    description = (
        "Return the next upcoming or currently-open NIP vaccine window for "
        "this child."
    )
    parameters = vol.Schema({})

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> dict[str, Any]:
        coord = self._coordinator()
        if coord is None or coord.data is None:
            return {"error": "데이터 준비 중", "disclaimer": MEDICAL_DISCLAIMER}
        today = date.fromisoformat(coord.data["today"])
        nxt = _next_event(coord.data.get("upcoming_vaccines", []), today)
        return {
            "child_name": coord.child_name,
            "today": coord.data["today"],
            "next_vaccine": nxt,
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class GetNextCheckupTool(_BabyKitTool):
    name = "get_next_checkup"
    description = (
        "Return the next upcoming or currently-open 영유아 (infant) health "
        "checkup window for this child."
    )
    parameters = vol.Schema({})

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> dict[str, Any]:
        coord = self._coordinator()
        if coord is None or coord.data is None:
            return {"error": "데이터 준비 중", "disclaimer": MEDICAL_DISCLAIMER}
        today = date.fromisoformat(coord.data["today"])
        nxt = _next_event(coord.data.get("upcoming_checkups", []), today)
        return {
            "child_name": coord.child_name,
            "today": coord.data["today"],
            "next_checkup": nxt,
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class GetNextOralCheckupTool(_BabyKitTool):
    name = "get_next_oral_checkup"
    description = (
        "Return the next upcoming or currently-open 영유아 구강검진 (infant "
        "oral/dental checkup) window for this child. Korea runs 4 oral "
        "checkups: 18-29, 30-41, 42-53, 54-65 months."
    )
    parameters = vol.Schema({})

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> dict[str, Any]:
        coord = self._coordinator()
        if coord is None or coord.data is None:
            return {"error": "데이터 준비 중", "disclaimer": MEDICAL_DISCLAIMER}
        today = date.fromisoformat(coord.data["today"])
        nxt = _next_event(coord.data.get("upcoming_oral_checkups", []), today)
        return {
            "child_name": coord.child_name,
            "today": coord.data["today"],
            "next_oral_checkup": nxt,
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class GetCompletedEventsTool(_BabyKitTool):
    name = "get_completed_events"
    description = (
        "Return the vaccine doses and checkups the parent has marked as done "
        "for this child (event_id, name, completed date), plus windows that "
        "already passed without a completion mark."
    )
    parameters = vol.Schema({})

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> dict[str, Any]:
        coord = self._coordinator()
        if coord is None or coord.data is None:
            return {"error": "데이터 준비 중", "disclaimer": MEDICAL_DISCLAIMER}
        today = date.fromisoformat(coord.data["today"])
        completed = coord.data.get("completed") or {}
        all_events = [
            *coord.all_vaccines,
            *coord.all_checkups,
            *coord.all_oral_checkups,
        ]
        dumped = [event_to_dict(e, today, completed) for e in all_events]
        return {
            "child_name": coord.child_name,
            "today": coord.data["today"],
            "completed": [d for d in dumped if d["status"] == "done"],
            "missed_without_mark": [d for d in dumped if d["status"] == "missed"],
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class GetGrowthPercentilesTool(_BabyKitTool):
    name = "get_growth_percentiles"
    description = (
        "Return the latest growth percentiles for this child: age-indexed "
        "height/weight/head and the weight-for-length percentile (recumbent "
        "length <2y, standing height 2y+). Sourced from KDCA 2017 LMS."
    )
    parameters = vol.Schema({})

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> dict[str, Any]:
        coord = self._coordinator()
        if coord is None or coord.data is None:
            return {"error": "데이터 준비 중", "disclaimer": MEDICAL_DISCLAIMER}
        return {
            "child_name": coord.child_name,
            "age_months": coord.data.get("age_months"),
            "percentiles": coord.data.get("percentiles") or {},
            "weight_for_length": coord.data.get("weight_for_length"),
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class GetCareTuitionTool(_BabyKitTool):
    name = "get_care_tuition"
    description = (
        "Return the childcare tuition tier (표준보육료 / 정부지원금 / "
        "본인부담금) that applies to this child's current age class "
        "(만 N세반). Returns null fields when the bundled data is still in "
        "placeholder mode (data_year == 0); always cross-check with the "
        "child's daycare for the current year's published rates."
    )
    parameters = vol.Schema({})

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> dict[str, Any]:
        coord = self._coordinator()
        if coord is None or coord.data is None:
            return {"error": "데이터 준비 중", "disclaimer": MEDICAL_DISCLAIMER}
        tier = (coord.data or {}).get("care_tuition")
        if tier is None:
            return {
                "child_name": coord.child_name,
                "age_months": coord.data.get("age_months"),
                "care_tuition": None,
                "note": "No tuition tier applies to this age (보육료 only covers 만 0~6세반).",
                "disclaimer": MEDICAL_DISCLAIMER,
            }
        return {
            "child_name": coord.child_name,
            "age_months": coord.data.get("age_months"),
            "care_tuition": tier,
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class ListUpcomingEventsTool(_BabyKitTool):
    name = "list_upcoming_events"
    description = (
        "List all upcoming (not yet completed) vaccine, checkup and oral "
        "checkup windows within the next N days for this child."
    )
    parameters = vol.Schema(
        {
            vol.Optional("days", default=90): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=730)
            ),
        }
    )

    async def async_call(
        self,
        hass: HomeAssistant,
        tool_input: llm.ToolInput,
        llm_context: llm.LLMContext,
    ) -> dict[str, Any]:
        coord = self._coordinator()
        if coord is None or coord.data is None:
            return {"error": "데이터 준비 중", "disclaimer": MEDICAL_DISCLAIMER}
        days = int(tool_input.tool_args.get("days", 90))
        today = date.fromisoformat(coord.data["today"])
        return {
            "child_name": coord.child_name,
            "horizon_days": days,
            "vaccines": _events_in_window(
                coord.data.get("upcoming_vaccines", []), today, days
            ),
            "checkups": _events_in_window(
                coord.data.get("upcoming_checkups", []), today, days
            ),
            "oral_checkups": _events_in_window(
                coord.data.get("upcoming_oral_checkups", []), today, days
            ),
            "disclaimer": MEDICAL_DISCLAIMER,
        }


_TOOL_CLASSES = [
    GetNextVaccineTool,
    GetNextCheckupTool,
    GetNextOralCheckupTool,
    GetCompletedEventsTool,
    GetGrowthPercentilesTool,
    GetCareTuitionTool,
    ListUpcomingEventsTool,
]


class _BabyKitAPI(llm.API):
    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        child_id: str,
        child_name: str,
    ) -> None:
        super().__init__(
            hass=hass,
            id=_api_id(child_id),
            name=f"kr_baby_kit · {child_name}",
        )
        self._entry_id = entry_id
        self._child_id = child_id
        self._child_name = child_name

    async def async_get_api_instance(
        self, llm_context: llm.LLMContext
    ) -> llm.APIInstance:
        tools = [cls(self.hass, self._entry_id) for cls in _TOOL_CLASSES]
        return llm.APIInstance(
            api=self,
            api_prompt=_api_prompt(self._child_name),
            llm_context=llm_context,
            tools=tools,
        )


async def async_setup_llm_api(
    hass: HomeAssistant, entry: ConfigEntry, child_id: str, child_name: str
) -> Callable[[], None] | None:
    api = _BabyKitAPI(hass, entry.entry_id, child_id, child_name)
    try:
        unreg = llm.async_register_api(hass, api)
    except HomeAssistantError:
        # A stale registration survived a failed unload; replace it.
        _drop_api(hass, api.id)
        unreg = llm.async_register_api(hass, api)
    if unreg is None:
        # HA releases before the unregister callable existed return None.
        # Without this fallback every entry reload failed with
        # "API ... is already registered".
        def unreg() -> None:
            _drop_api(hass, api.id)

    _LOGGER.info("Registered LLM API %s", api.id)
    return unreg


def _drop_api(hass: HomeAssistant, api_id: str) -> None:
    get_apis = getattr(llm, "_async_get_apis", None)
    if get_apis is None:  # pragma: no cover - future HA internals
        return
    get_apis(hass).pop(api_id, None)


def async_cleanup_llm_api(unregister: Callable[[], None] | None) -> None:
    if unregister is None:
        return
    try:
        unregister()
    except Exception:  # pragma: no cover
        _LOGGER.debug("error unregistering llm api", exc_info=True)
