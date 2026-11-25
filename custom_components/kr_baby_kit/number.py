"""Number entities — direct height / weight / head input from dashboard.

Setting the value records a measurement dated today (in Home Assistant's
configured local time zone) and refreshes the coordinator. Before any
measurement is recorded, each entity defaults to the age- and sex-specific
LMS median (50th percentile) from the active growth chart. For backfilling
historical values, use the `record_measurement` service which accepts an
explicit `date`.
"""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, attribution_for, is_korean
from .coordinator import BabyKitCoordinator
from .device import child_device
from .storage import async_append_measurement, latest


_NUMBER_SPECS = {
    "height": {
        "unit": "cm",
        "min": 30.0,
        "max": 200.0,
        "step": 0.1,
    },
    "weight": {
        "unit": "kg",
        "min": 1.0,
        "max": 100.0,
        "step": 0.05,
    },
    "head": {
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

    def __init__(
        self,
        coordinator: BabyKitCoordinator,
        entry: ConfigEntry,
        kind: str,
    ) -> None:
        super().__init__(coordinator)
        self._kind = kind
        spec = _NUMBER_SPECS[kind]
        self._attr_translation_key = f"{kind}_input"
        self._attr_native_unit_of_measurement = spec["unit"]
        self._attr_native_min_value = spec["min"]
        self._attr_native_max_value = spec["max"]
        self._attr_native_step = spec["step"]
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.child_id}_{kind}_input"
        )

    @property
    def attribution(self) -> str:
        return attribution_for(
            self.coordinator.profile, korean=is_korean(self.coordinator.hass)
        )

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    def _default_median(self) -> float | None:
        """Return the 50th-percentile LMS median for the child's current age."""
        age_m = (self.coordinator.data or {}).get("age_months")
        if age_m is None:
            return None
        point = self.coordinator.chart.lookup(
            self.coordinator.child_sex, self._kind, max(0.0, float(age_m))
        )
        if point is None:
            return None
        step = float(self._attr_native_step)
        rounded = round(round(point.M / step) * step, 2)
        return min(
            float(self._attr_native_max_value),
            max(float(self._attr_native_min_value), rounded),
        )

    @property
    def native_value(self) -> float | None:
        records = (self.coordinator.data or {}).get("records") or []
        last = latest(records, self._kind)
        if last:
            return float(last[self._kind])
        return self._default_median()

    @property
    def extra_state_attributes(self) -> dict:
        records = (self.coordinator.data or {}).get("records") or []
        last = latest(records, self._kind)
        if last:
            return {
                "is_default_median": False,
                "measured_at": last["date"],
            }
        return {
            "is_default_median": True,
            "measured_at": None,
        }

    async def async_set_native_value(self, value: float) -> None:
        today = dt_util.now().date().isoformat()
        try:
            await async_append_measurement(
                self.hass,
                child_id=self.coordinator.child_id,
                measurement_date=today,
                **{self._kind: value},
            )
        except ValueError as err:
            # Surface as a clean UI error instead of an unhandled traceback.
            raise ServiceValidationError(str(err)) from err
        await self.coordinator.async_refresh()
