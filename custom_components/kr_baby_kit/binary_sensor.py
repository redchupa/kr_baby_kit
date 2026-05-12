"""Binary sensors — e.g. 이번 달 예방접종 있음."""
from __future__ import annotations

from datetime import date, timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import BabyKitCoordinator
from .device import child_device


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BabyKitCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        [
            VaccineDueSensor(coordinator, entry),
            CheckupDueSensor(coordinator, entry),
        ]
    )


def _window_overlaps_month(start: date, end: date, ref: date) -> bool:
    month_start = ref.replace(day=1)
    next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end = next_month - timedelta(days=1)
    return start <= month_end and end >= month_start


class _DueSensor(CoordinatorEntity[BabyKitCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _data_key = ""
    _label = ""

    def __init__(self, coordinator: BabyKitCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.child_id}_{self._data_key}_due_this_month"
        )
        self._attr_name = self._label

    @property
    def device_info(self):
        return child_device(self.entry)

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        events = data.get(self._data_key, [])
        today_iso = data.get("today")
        if not today_iso:
            return False
        today = date.fromisoformat(today_iso)
        return any(_window_overlaps_month(e.start, e.end, today) for e in events)

    @property
    def extra_state_attributes(self) -> dict:
        events = (self.coordinator.data or {}).get(self._data_key, [])
        return {
            "count_within_horizon": len(events),
            "next": (
                {
                    "code": events[0].code,
                    "name_ko": events[0].name_ko,
                    "dose": events[0].dose,
                    "start": events[0].start.isoformat(),
                    "end": events[0].end.isoformat(),
                }
                if events
                else None
            ),
        }


class VaccineDueSensor(_DueSensor):
    _data_key = "upcoming_vaccines"
    _label = "일정 · 이번 달 예방접종"


class CheckupDueSensor(_DueSensor):
    _data_key = "upcoming_checkups"
    _label = "일정 · 이번 달 검진"
