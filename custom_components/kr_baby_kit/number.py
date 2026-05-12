"""Number entities — direct height / weight / head input from dashboard.

Setting the value records a measurement dated today (Asia/Seoul) and
refreshes the coordinator. For backfilling historical values, use the
`record_measurement` service which accepts an explicit `date`.
"""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, TZ_ASIA_SEOUL
from .coordinator import BabyKitCoordinator
from .device import child_device
from .storage import async_append_measurement, latest


_NUMBER_SPECS = {
    "height": {
        "name": "키",
        "unit": "cm",
        "min": 30.0,
        "max": 200.0,
        "step": 0.1,
    },
    "weight": {
        "name": "몸무게",
        "unit": "kg",
        "min": 1.0,
        "max": 100.0,
        "step": 0.05,
    },
    "head": {
        "name": "머리둘레",
        "unit": "cm",
        "min": 25.0,
        "max": 65.0,
        "step": 0.1,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BabyKitCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities(
        MeasurementNumber(coordinator, entry, kind) for kind in _NUMBER_SPECS
    )


class MeasurementNumber(CoordinatorEntity[BabyKitCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: BabyKitCoordinator,
        entry: ConfigEntry,
        kind: str,
    ) -> None:
        super().__init__(coordinator)
        self._kind = kind
        spec = _NUMBER_SPECS[kind]
        self._attr_name = spec["name"]
        self._attr_native_unit_of_measurement = spec["unit"]
        self._attr_native_min_value = spec["min"]
        self._attr_native_max_value = spec["max"]
        self._attr_native_step = spec["step"]
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.child_id}_{kind}_input"
        )

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    @property
    def native_value(self) -> float | None:
        records = (self.coordinator.data or {}).get("records") or []
        last = latest(records, self._kind)
        if not last:
            return None
        return float(last[self._kind])

    async def async_set_native_value(self, value: float) -> None:
        today = datetime.now(TZ_ASIA_SEOUL).date().isoformat()
        await async_append_measurement(
            self.hass,
            child_id=self.coordinator.child_id,
            measurement_date=today,
            **{self._kind: value},
        )
        await self.coordinator.async_request_refresh()
