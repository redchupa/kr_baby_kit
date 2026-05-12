"""Calendar entities — immunization + infant checkup schedule."""
from __future__ import annotations

from datetime import datetime, time

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, TZ_ASIA_SEOUL
from .coordinator import BabyKitCoordinator
from .device import child_device
from .schedule import ScheduleEvent


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BabyKitCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            BabyKitCalendar(
                coordinator,
                entry,
                data_key="upcoming_vaccines",
                slug="immunization",
                label="캘린더_예방접종",
            ),
            BabyKitCalendar(
                coordinator,
                entry,
                data_key="upcoming_checkups",
                slug="checkup",
                label="캘린더_검진",
            ),
        ]
    )


def _to_calendar_event(event: ScheduleEvent) -> CalendarEvent:
    summary = event.name_ko
    if event.dose is not None and event.kind == "vaccine":
        summary = f"{event.name_ko} ({event.dose}차)"
    description_lines = []
    if event.note:
        description_lines.append(event.note)
    description_lines.append("출처: 질병관리청·보건복지부 (참고용)")
    return CalendarEvent(
        summary=summary,
        start=datetime.combine(event.start, time.min, tzinfo=TZ_ASIA_SEOUL),
        end=datetime.combine(event.end, time.max, tzinfo=TZ_ASIA_SEOUL),
        description="\n".join(description_lines),
    )


class BabyKitCalendar(CoordinatorEntity[BabyKitCoordinator], CalendarEntity):
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: BabyKitCoordinator,
        entry: ConfigEntry,
        *,
        data_key: str,
        slug: str,
        label: str,
    ) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._data_key = data_key
        self._attr_name = label
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_{slug}_calendar"

    @property
    def device_info(self):
        return child_device(self.entry)

    def _events(self) -> list[ScheduleEvent]:
        return (self.coordinator.data or {}).get(self._data_key, [])

    @property
    def event(self) -> CalendarEvent | None:
        events = self._events()
        if not events:
            return None
        return _to_calendar_event(events[0])

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        out: list[CalendarEvent] = []
        for event in self._events():
            cal = _to_calendar_event(event)
            if cal.end >= start_date and cal.start <= end_date:
                out.append(cal)
        return out
