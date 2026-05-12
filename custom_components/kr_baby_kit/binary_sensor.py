"""Binary sensors — schedule reminders + bi-directional percentile alerts."""
from __future__ import annotations

from datetime import date, timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, MEDICAL_DISCLAIMER
from .coordinator import BabyKitCoordinator
from .device import child_device


# Bi-directional percentile metrics: both ends warrant clinical follow-up.
# We expose these as binary "양극단 주의" rather than percentile sensors so
# their value never gets mistaken for a single-direction ranking.
_CLINICAL_LOW_PCT: float = 5.0
_CLINICAL_HIGH_PCT: float = 95.0


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
            HeadConcernSensor(coordinator, entry),
            BMIConcernSensor(coordinator, entry),
            WeightForLengthConcernSensor(coordinator, entry),
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
    _label = "일정_이번_달_예방접종"


class CheckupDueSensor(_DueSensor):
    _data_key = "upcoming_checkups"
    _label = "일정_이번_달_검진"


class _ConcernSensor(CoordinatorEntity[BabyKitCoordinator], BinarySensorEntity):
    """Binary "양극단 주의" alert for a bi-directionally concerning percentile.

    state=on when the underlying KDCA statistical percentile is below 5 or
    above 95. attributes expose the raw percentile, the direction (low/high),
    a Korean one-line summary, and the latest raw measurement so a dashboard
    card or automation can show details without bringing back the easy-to-
    misread percentile sensor.
    """

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _slug: str = ""
    _label: str = ""

    def __init__(self, coordinator: BabyKitCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_{self._slug}_concern"
        self._attr_name = self._label

    @property
    def device_info(self):
        return child_device(self.entry)

    def _info(self) -> dict:
        return {}

    @property
    def available(self) -> bool:
        # Available if we have an explicit percentile OR something meaningful
        # to surface via attributes (e.g. the <24mo BMI advisory). This keeps
        # the entity from showing "unavailable" when the missing percentile
        # itself is the information the parent needs to see.
        info = self._info()
        return (
            info.get("statistical_percentile") is not None
            or info.get("summary_ko") is not None
        )

    @property
    def is_on(self) -> bool:
        pct = self._info().get("statistical_percentile")
        if pct is None:
            # Either no measurement yet, or KDCA's percentile is intentionally
            # undefined at this age. Don't flag a concern.
            return False
        return pct < _CLINICAL_LOW_PCT or pct > _CLINICAL_HIGH_PCT

    @property
    def extra_state_attributes(self) -> dict:
        info = self._info()
        pct = info.get("statistical_percentile")
        level: str | None = None
        if pct is not None:
            if pct < _CLINICAL_LOW_PCT:
                level = "low"
            elif pct > _CLINICAL_HIGH_PCT:
                level = "high"
        return {
            "statistical_percentile": pct,
            "level": level,
            "summary_ko": info.get("summary_ko"),
            "value": info.get("value"),
            "measured_at": info.get("measured_at"),
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class HeadConcernSensor(_ConcernSensor):
    _slug = "head"
    _label = "양극단_주의_머리둘레"

    def _info(self) -> dict:
        return (self.coordinator.data or {}).get("percentiles", {}).get("head") or {}


class BMIConcernSensor(_ConcernSensor):
    _slug = "bmi"
    _label = "양극단_주의_BMI"

    def _info(self) -> dict:
        data = self.coordinator.data or {}
        info = (data.get("percentiles") or {}).get("bmi") or {}
        if info:
            return info
        # KDCA BMI percentile table starts at 24 months. Below that, surface a
        # human-readable advisory + the raw BMI so the entity stays available
        # and the parent sees *why* there's no percentile yet — rather than a
        # bare "unavailable" badge.
        age_m = data.get("age_months")
        if age_m is not None and age_m < 24:
            return {
                "summary_ko": (
                    "만 24개월 미만 — BMI 백분위는 KDCA 기준상 만 2세부터 "
                    "적용됩니다. 같은 자녀의 '신장별 몸무게 양극단 주의' "
                    "binary_sensor 를 함께 확인하세요."
                ),
                "value": data.get("bmi_raw"),
            }
        return {}


class WeightForLengthConcernSensor(_ConcernSensor):
    _slug = "weight_for_length"
    _label = "양극단_주의_신장별_몸무게"

    def _info(self) -> dict:
        wfl = (self.coordinator.data or {}).get("weight_for_length") or {}
        # adapt the weight_for_length dict to the same shape the concern
        # base class expects.
        if not wfl:
            return {}
        return {
            "statistical_percentile": wfl.get("statistical_percentile"),
            "summary_ko": wfl.get("summary_ko"),
            "value": {
                "length_cm": wfl.get("length_cm"),
                "weight_kg": wfl.get("weight_kg"),
                "band": wfl.get("band"),
            },
            "measured_at": wfl.get("measured_at"),
        }
