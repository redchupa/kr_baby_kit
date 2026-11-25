"""Growth percentile sensors per registered child."""
from __future__ import annotations

from datetime import date, datetime, time

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    PROFILE_KR,
    attribution_for,
    disclaimer_for,
    is_korean,
)
from .coordinator import BabyKitCoordinator
from .device import child_device
from .schedule import event_to_dict


_KIND_KEYS = ("height", "weight")
# head / bmi / weight-for-length intentionally omitted — they are bi-directional
# (양극단 우려) and exposing them as a percentile sensor invited users to read a
# single-direction ranking. They live as `binary_sensor.<child>_<kind>_concern`
# instead, with the raw percentile preserved on that entity's attributes.


_CARE_TUITION_FIELDS: list[tuple[str, str]] = [
    ("standard_tuition", "standard_tuition"),
    ("government_subsidy", "government_subsidy"),
    ("parent_share", "parent_share"),
]


# (data key, next-event uid/translation slug, open-deadline uid/translation slug)
# The two sensors split what one sensor used to mix: an already-open window
# showed its (past) start date under a "다음" name.
_SCHEDULE_SENSORS: tuple[tuple[str, str, str], ...] = (
    ("upcoming_vaccines", "next_vaccine", "vaccine_open_deadline"),
    ("upcoming_checkups", "next_checkup", "checkup_open_deadline"),
    ("upcoming_oral_checkups", "next_oral_checkup", "oral_checkup_open_deadline"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BabyKitCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list = [
        PercentileSensor(coordinator, entry, kind) for kind in _KIND_KEYS
    ]
    entities.append(AgeMonthsSensor(coordinator, entry))
    for data_key, next_slug, open_slug in _SCHEDULE_SENSORS:
        entities.append(
            NextEventSensor(
                coordinator, entry, data_key=data_key, slug=next_slug
            )
        )
        entities.append(
            OpenDeadlineSensor(
                coordinator, entry, data_key=data_key, slug=open_slug
            )
        )
    if coordinator.profile == PROFILE_KR:
        for tuition_field, slug in _CARE_TUITION_FIELDS:
            entities.append(CareTuitionSensor(coordinator, entry, tuition_field, slug))
    entities.append(BMIRawSensor(coordinator, entry))
    async_add_entities(entities)


class PercentileSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    """One sensor per measurement kind."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BabyKitCoordinator,
        entry: ConfigEntry,
        kind: str,
    ) -> None:
        super().__init__(coordinator)
        self._kind = kind
        self._attr_translation_key = f"{kind}_percentile"
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_{kind}_percentile"

    @property
    def attribution(self) -> str:
        return attribution_for(
            self.coordinator.profile, korean=is_korean(self.coordinator.hass)
        )

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    @property
    def native_value(self) -> float | None:
        data = self.coordinator.data or {}
        pct = (data.get("percentiles") or {}).get(self._kind, {}).get("percentile")
        return round(pct, 1) if pct is not None else None

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        info = (data.get("percentiles") or {}).get(self._kind, {})
        ko = is_korean(self.coordinator.hass)
        return {
            "value": info.get("value"),
            "measured_at": info.get("measured_at"),
            "z_score": info.get("z_score"),
            "statistical_percentile": info.get("statistical_percentile"),
            "top_percent": info.get("top_percent"),
            "summary_ko": info.get("summary_ko"),
            "summary_en": info.get("summary_en"),
            "age_months_at_measurement": info.get("age_months_at_measurement"),
            "age_months": data.get("age_months"),
            "profile": self.coordinator.profile,
            "disclaimer": disclaimer_for(korean=ko),
        }


class AgeMonthsSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "age_months"
    _attr_native_unit_of_measurement = "mo"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: BabyKitCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_age_months"

    @property
    def attribution(self) -> str:
        return attribution_for(
            self.coordinator.profile, korean=is_korean(self.coordinator.hass)
        )

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    @property
    def native_value(self) -> float | None:
        am = (self.coordinator.data or {}).get("age_months")
        return round(am, 2) if am is not None else None


class NextEventSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    """Start date of the next window that has NOT opened yet (always future).

    Windows that are already open live on ``OpenDeadlineSensor`` instead;
    before v0.9.0 this sensor showed an open window's past start date under
    a "다음" name. ``open_event_ids`` is still exposed for scripts.
    """

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: BabyKitCoordinator,
        entry: ConfigEntry,
        *,
        data_key: str,
        slug: str,
    ) -> None:
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_translation_key = slug
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_{slug}"

    @property
    def attribution(self) -> str:
        return attribution_for(
            self.coordinator.profile, korean=is_korean(self.coordinator.hass)
        )

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    def _today(self) -> date | None:
        data = self.coordinator.data or {}
        return date.fromisoformat(data["today"]) if data.get("today") else None

    def _events(self) -> list:
        return (self.coordinator.data or {}).get(self._data_key, [])

    def _next_event(self):
        today = self._today()
        return next(
            (e for e in self._events() if today is None or e.start > today), None
        )

    @property
    def native_value(self) -> datetime | None:
        event = self._next_event()
        if event is None:
            return None
        return datetime.combine(event.start, time.min, tzinfo=dt_util.DEFAULT_TIME_ZONE)

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        today = self._today()
        events = self._events()
        open_ids = [
            e.event_id for e in events if today is not None and e.start <= today
        ]
        event = self._next_event()
        if event is None:
            return {"upcoming_count": 0, "open_event_ids": open_ids}
        attrs = event_to_dict(event, today, data.get("completed"))
        if today is not None:
            attrs["days_until_start"] = (event.start - today).days
        attrs["upcoming_count"] = len(events)
        # Windows open right now (e.g. the whole 2-month bundle) for
        # one-shot mark_event_done scripts.
        attrs["open_event_ids"] = open_ids
        return attrs


class OpenDeadlineSensor(NextEventSensor):
    """Deadline of the window(s) open right now; unknown when none is open.

    State is the end of the last allowed day, so a dashboard shows
    "N일 후" / "in N days" until the deadline passes. Every open, not-completed
    event is listed with its own deadline in ``open_events``.
    """

    def _open_events(self) -> list:
        today = self._today()
        if today is None:
            return []
        return sorted(
            (e for e in self._events() if e.start <= today <= e.end),
            key=lambda e: (e.end, e.event_id),
        )

    @property
    def native_value(self) -> datetime | None:
        events = self._open_events()
        if not events:
            return None
        return datetime.combine(
            events[0].end, time(23, 59, 59), tzinfo=dt_util.DEFAULT_TIME_ZONE
        )

    @property
    def extra_state_attributes(self) -> dict:
        today = self._today()
        events = self._open_events()
        out = {
            "open_count": len(events),
            "open_event_ids": [e.event_id for e in events],
            "open_events": [
                {
                    "event_id": e.event_id,
                    "name_ko": e.name_ko,
                    "name_en": e.name_en,
                    "dose": e.dose,
                    "window_start": e.start.isoformat(),
                    "deadline": e.end.isoformat(),
                    "days_left": (e.end - today).days if today else None,
                }
                for e in events
            ],
        }
        if events:
            first = events[0]
            out["event_id"] = first.event_id
            out["name_ko"] = first.name_ko
            out["name_en"] = first.name_en
            out["deadline"] = first.end.isoformat()
            out["days_left"] = (first.end - today).days if today else None
        return out


class CareTuitionSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    """One of the three childcare-tuition figures for the current age class.

    Only created for the South Korea (`kr`) profile.
    """

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "KRW"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: BabyKitCoordinator,
        entry: ConfigEntry,
        field: str,
        slug: str,
    ) -> None:
        super().__init__(coordinator)
        self._field = field
        self._attr_translation_key = slug
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_{slug}"

    @property
    def attribution(self) -> str:
        return attribution_for(
            self.coordinator.profile, korean=is_korean(self.coordinator.hass)
        )

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    def _tier(self) -> dict | None:
        return (self.coordinator.data or {}).get("care_tuition")

    @property
    def available(self) -> bool:
        return super().available and self._tier() is not None

    @property
    def native_value(self) -> int | None:
        tier = self._tier()
        if tier is None or tier.get("is_placeholder"):
            return None
        raw = tier.get(self._field)
        return int(raw) if raw is not None else None

    @property
    def extra_state_attributes(self) -> dict:
        tier = self._tier() or {}
        ko = is_korean(self.coordinator.hass)
        return {
            "age_class": tier.get("age_class"),
            "age_class_label_ko": tier.get("label_ko"),
            "age_class_label_en": tier.get("label_en"),
            "age_class_basis": tier.get("age_class_basis"),
            "data_year": tier.get("data_year"),
            "source_url": tier.get("source_url"),
            "raw_value": tier.get(self._field),
            "is_placeholder": tier.get("is_placeholder"),
            "disclaimer": disclaimer_for(korean=ko),
        }


class BMIRawSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    """Raw BMI value (kg/m²) for every age."""

    _attr_has_entity_name = True
    _attr_translation_key = "bmi_raw"
    _attr_native_unit_of_measurement = "kg/m²"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: BabyKitCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_bmi_raw"

    @property
    def attribution(self) -> str:
        return attribution_for(
            self.coordinator.profile, korean=is_korean(self.coordinator.hass)
        )

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    @property
    def native_value(self) -> float | None:
        return (self.coordinator.data or {}).get("bmi_raw")

    @property
    def extra_state_attributes(self) -> dict:
        data = self.coordinator.data or {}
        bmi_info = (data.get("percentiles") or {}).get("bmi") or {}
        age_m = data.get("bmi_age_months")
        if age_m is None:
            age_m = data.get("age_months") or 0
        if age_m < 24:
            summary_ko = "측정 당시 만 24개월 미만 — BMI 백분위는 만 2세부터 적용됩니다. 신장별 몸무게를 함께 확인하세요."
            summary_en = "Under 24 months at measurement — BMI percentile starts at age 2. Check weight-for-length instead."
        else:
            summary_ko = bmi_info.get("summary_ko")
            summary_en = bmi_info.get("summary_en")
        ko = is_korean(self.coordinator.hass)
        return {
            "measured_at": data.get("bmi_measured_at"),
            "age_months": data.get("age_months"),
            "percentile": bmi_info.get("percentile"),
            "statistical_percentile": bmi_info.get("statistical_percentile"),
            "top_percent": bmi_info.get("top_percent"),
            "z_score": bmi_info.get("z_score"),
            "summary_ko": summary_ko,
            "summary_en": summary_en,
            "disclaimer": disclaimer_for(korean=ko),
        }
