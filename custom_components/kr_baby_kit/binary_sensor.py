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

from .const import DOMAIN, attribution_for, disclaimer_for, is_korean
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
            OralCheckupDueSensor(coordinator, entry),
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
    """on = a window of this kind overlaps the current month.

    ``translation_key`` maps on/off to readable states ("이번 달 접종 있음")
    instead of 켜짐/꺼짐.
    """

    _attr_has_entity_name = True
    _data_key = ""
    _translation_key = ""

    def __init__(self, coordinator: BabyKitCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.child_id}_{self._data_key}_due_this_month"
        )
        self._attr_translation_key = self._translation_key

    @property
    def attribution(self) -> str:
        return attribution_for(
            self.coordinator.profile, korean=is_korean(self.coordinator.hass)
        )

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
        data = self.coordinator.data or {}
        events = data.get(self._data_key, [])
        this_month: list[str] = []
        if data.get("today"):
            today = date.fromisoformat(data["today"])
            this_month = [
                e.event_id
                for e in events
                if _window_overlaps_month(e.start, e.end, today)
            ]
        return {
            "count_within_horizon": len(events),
            "this_month_event_ids": this_month,
            "next": (
                {
                    "event_id": events[0].event_id,
                    "code": events[0].code,
                    "name_ko": events[0].name_ko,
                    "name_en": events[0].name_en,
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
    _translation_key = "vaccine_due"


class CheckupDueSensor(_DueSensor):
    _data_key = "upcoming_checkups"
    _translation_key = "checkup_due"


class OralCheckupDueSensor(_DueSensor):
    _data_key = "upcoming_oral_checkups"
    _translation_key = "oral_checkup_due"


class _ConcernSensor(CoordinatorEntity[BabyKitCoordinator], BinarySensorEntity):
    """Binary alert for a bi-directionally concerning percentile (<5% or >95%)."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _slug: str = ""
    _translation_key: str = ""

    def __init__(self, coordinator: BabyKitCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self.entry = entry
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_{self._slug}_concern"
        self._attr_translation_key = self._translation_key

    @property
    def attribution(self) -> str:
        return attribution_for(
            self.coordinator.profile, korean=is_korean(self.coordinator.hass)
        )

    @property
    def device_info(self):
        return child_device(self.entry)

    def _info(self) -> dict:
        return {}

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        info = self._info()
        return (
            info.get("statistical_percentile") is not None
            or info.get("summary_ko") is not None
        )

    @property
    def is_on(self) -> bool:
        pct = self._info().get("statistical_percentile")
        if pct is None:
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
        ko = is_korean(self.coordinator.hass)
        return {
            "statistical_percentile": pct,
            "level": level,
            "summary_ko": info.get("summary_ko"),
            "summary_en": info.get("summary_en"),
            "value": info.get("value"),
            "measured_at": info.get("measured_at"),
            "disclaimer": disclaimer_for(korean=ko),
        }


class HeadConcernSensor(_ConcernSensor):
    _slug = "head"
    _translation_key = "head_concern"

    def _info(self) -> dict:
        return (self.coordinator.data or {}).get("percentiles", {}).get("head") or {}


class BMIConcernSensor(_ConcernSensor):
    _slug = "bmi"
    _translation_key = "bmi_concern"

    def _info(self) -> dict:
        data = self.coordinator.data or {}
        info = (data.get("percentiles") or {}).get("bmi") or {}
        if info:
            return info
        age_m = data.get("bmi_age_months")
        if age_m is None:
            age_m = data.get("age_months")
        if age_m is not None and age_m < 24:
            return {
                "summary_ko": (
                    "측정 당시 만 24개월 미만 — BMI 백분위는 "
                    "만 2세부터 적용됩니다. 같은 자녀의 '신장별 몸무게 양극단 "
                    "주의' binary_sensor 를 함께 확인하고, 만 2세 이후 다시 "
                    "측정하면 BMI 백분위가 계산됩니다."
                ),
                "summary_en": (
                    "Under 24 months at measurement — BMI percentiles apply "
                    "from age 2. Check the weight-for-length concern sensor "
                    "instead."
                ),
                "value": data.get("bmi_raw"),
            }
        return {}


class WeightForLengthConcernSensor(_ConcernSensor):
    _slug = "weight_for_length"
    _translation_key = "weight_for_length_concern"

    def _info(self) -> dict:
        wfl = (self.coordinator.data or {}).get("weight_for_length") or {}
        if not wfl:
            return {}
        return {
            "statistical_percentile": wfl.get("statistical_percentile"),
            "summary_ko": wfl.get("summary_ko"),
            "summary_en": wfl.get("summary_en"),
            "value": {
                "length_cm": wfl.get("length_cm"),
                "weight_kg": wfl.get("weight_kg"),
                "band": wfl.get("band"),
            },
            "measured_at": wfl.get("measured_at"),
        }
