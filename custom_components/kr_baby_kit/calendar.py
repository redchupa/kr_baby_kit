"""Calendar entities — immunization, infant checkup, and oral checkup schedule.

Since v0.9.0:

* The calendars show the **whole** projected schedule (past windows too), so
  scrolling back in the HA calendar view shows what was due and whether it
  was marked done. Completed events get a ``✅`` prefix; passed windows that
  were never marked get ``⚠️``.
* Windows are all-day events (``date`` start, exclusive ``date`` end) rather
  than 00:00–23:59:59.999999 timed events.
* The entity's ``event`` (calendar state) is the next not-yet-completed
  window, so a completed dose no longer keeps the calendar ``on``.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, attribution_for, is_korean
from .coordinator import BabyKitCoordinator
from .device import child_device
from .schedule import (
    KIND_VACCINE,
    STATUS_DONE,
    STATUS_PAST,
    ScheduleEvent,
    event_status,
)

_CALENDARS: tuple[tuple[str, str, str, str], ...] = (
    # (upcoming data key, full-list data key, unique-id slug, translation_key)
    ("upcoming_vaccines", "all_vaccines", "immunization", "immunization_calendar"),
    ("upcoming_checkups", "all_checkups", "checkup", "checkup_calendar"),
    ("upcoming_oral_checkups", "all_oral_checkups", "oral_checkup", "oral_checkup_calendar"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BabyKitCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        BabyKitCalendar(
            coordinator,
            entry,
            upcoming_key=upcoming_key,
            all_key=all_key,
            slug=slug,
            translation_key=translation_key,
        )
        for upcoming_key, all_key, slug, translation_key in _CALENDARS
    )


def _to_calendar_event(
    event: ScheduleEvent,
    *,
    child_id: str,
    today: date | None = None,
    completed: dict | None = None,
    korean: bool = True,
    profile: str = "kr",
) -> CalendarEvent:
    base_name = event.name_ko if korean else (event.name_en or event.name_ko)
    summary = base_name
    if (
        event.dose is not None
        and event.kind == KIND_VACCINE
        and (event.dose_count or 0) != 1  # single-shot vaccines: no "(1차)"
    ):
        summary = (
            f"{base_name} ({event.dose}차)"
            if korean
            else f"{base_name} (dose {event.dose})"
        )

    status = event_status(event, today, completed) if today else None
    description_lines: list[str] = []
    if status == STATUS_DONE:
        summary = f"✓ {summary}" if not korean else f"✅ {summary}"
        done_date = ((completed or {}).get(event.event_id) or {}).get("date")
        if korean:
            description_lines.append(f"완료: {done_date}" if done_date else "완료")
        else:
            description_lines.append(f"Done: {done_date}" if done_date else "Done")
    elif status == STATUS_PAST:
        description_lines.append("기간 지남" if korean else "Window passed")

    wnote = event.window_note if korean else (event.window_note_en or event.window_note)
    if wnote:
        description_lines.append(
            f"검진 시기: {wnote}" if korean else f"Window: {wnote}"
        )
    items = event.items if korean else (event.items_en or event.items)
    if items:
        prefix = "검진 항목: " if korean else "Items: "
        description_lines.append(prefix + ", ".join(items))
    if event.note:
        description_lines.append(event.note)
    description_lines.append(
        f"일정 ID: {event.event_id}" if korean else f"Event ID: {event.event_id}"
    )
    if korean:
        description_lines.append(
            f"출처: {attribution_for(profile, korean=True)} (참고용)"
        )
    else:
        description_lines.append(
            f"Source: {attribution_for(profile, korean=False)} (for reference only)"
        )
    return CalendarEvent(
        summary=summary,
        start=event.start,
        end=event.end + timedelta(days=1),  # all-day end is exclusive
        description="\n".join(description_lines),
        uid=f"{DOMAIN}_{child_id}_{event.event_id}",
    )


class BabyKitCalendar(CoordinatorEntity[BabyKitCoordinator], CalendarEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: BabyKitCoordinator,
        entry: ConfigEntry,
        *,
        upcoming_key: str,
        all_key: str,
        slug: str,
        translation_key: str,
    ) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._upcoming_key = upcoming_key
        self._all_key = all_key
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_{slug}_calendar"

    @property
    def attribution(self) -> str:
        return attribution_for(
            self.coordinator.profile, korean=is_korean(self.coordinator.hass)
        )

    @property
    def device_info(self):
        return child_device(self.entry)

    def _today_and_completed(self) -> tuple[date | None, dict]:
        data = self.coordinator.data or {}
        today = date.fromisoformat(data["today"]) if data.get("today") else None
        return today, data.get("completed") or {}

    def _convert(self, event: ScheduleEvent) -> CalendarEvent:
        today, completed = self._today_and_completed()
        return _to_calendar_event(
            event,
            child_id=self.coordinator.child_id,
            today=today,
            completed=completed,
            korean=is_korean(self.coordinator.hass),
            profile=self.coordinator.profile,
        )

    @property
    def event(self) -> CalendarEvent | None:
        events = (self.coordinator.data or {}).get(self._upcoming_key, [])
        if not events:
            return None
        return self._convert(events[0])

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        start_utc = dt_util.as_utc(start_date)
        end_utc = dt_util.as_utc(end_date)
        out: list[CalendarEvent] = []
        for event in (self.coordinator.data or {}).get(self._all_key, []):
            cal = self._convert(event)
            # All-day events resolve against HA's configured local time zone.
            if (
                dt_util.as_utc(cal.end_datetime_local) > start_utc
                and dt_util.as_utc(cal.start_datetime_local) < end_utc
            ):
                out.append(cal)
        return out
