"""Growth percentile sensors per registered child."""
from __future__ import annotations

from datetime import datetime, time

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN, MEDICAL_DISCLAIMER, TZ_ASIA_SEOUL
from .coordinator import BabyKitCoordinator
from .device import child_device


_KIND_LABELS = {
    "height": ("백분위 · 키", "Height percentile"),
    "weight": ("백분위 · 몸무게", "Weight percentile"),
    "head": ("백분위 · 머리둘레", "Head circumference percentile"),
    "bmi": ("백분위 · BMI", "BMI percentile"),
}


_CARE_TUITION_FIELDS: list[tuple[str, str, str]] = [
    ("standard_tuition", "standard_tuition", "보육료 · 표준"),
    ("government_subsidy", "government_subsidy", "보육료 · 정부지원금"),
    ("parent_share", "parent_share", "보육료 · 본인부담금"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: BabyKitCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities: list = [
        PercentileSensor(coordinator, entry, kind) for kind in _KIND_LABELS
    ]
    entities.append(AgeMonthsSensor(coordinator, entry))
    entities.append(WeightForLengthSensor(coordinator, entry))
    entities.append(
        NextEventSensor(
            coordinator,
            entry,
            data_key="upcoming_vaccines",
            slug="next_vaccine",
            label="일정 · 다음 예방접종",
        )
    )
    entities.append(
        NextEventSensor(
            coordinator,
            entry,
            data_key="upcoming_checkups",
            slug="next_checkup",
            label="일정 · 다음 검진",
        )
    )
    for tuition_field, slug, label in _CARE_TUITION_FIELDS:
        entities.append(CareTuitionSensor(coordinator, entry, tuition_field, slug, label))
    entities.append(BMIRawSensor(coordinator, entry))
    async_add_entities(entities)


class PercentileSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    """One sensor per measurement kind."""

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: BabyKitCoordinator,
        entry: ConfigEntry,
        kind: str,
    ) -> None:
        super().__init__(coordinator)
        self._kind = kind
        ko, en = _KIND_LABELS[kind]
        self._attr_name = ko
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_{kind}_percentile"

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
        return {
            "value": info.get("value"),
            "measured_at": info.get("measured_at"),
            "z_score": info.get("z_score"),
            "top_percent": info.get("top_percent"),
            "summary_ko": info.get("summary_ko"),
            "age_months": data.get("age_months"),
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class AgeMonthsSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "정보 · 월령 (개월 수)"
    _attr_native_unit_of_measurement = "mo"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: BabyKitCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_age_months"

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    @property
    def native_value(self) -> float | None:
        am = (self.coordinator.data or {}).get("age_months")
        return round(am, 2) if am is not None else None


class WeightForLengthSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    """Weight-for-length / weight-for-height percentile.

    Uses recumbent length under 2y, standing height 2y+ per KDCA convention.
    """

    _attr_has_entity_name = True
    _attr_name = "백분위 · 신장별 몸무게"
    _attr_native_unit_of_measurement = "%"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: BabyKitCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = (
            f"{DOMAIN}_{coordinator.child_id}_weight_for_length_percentile"
        )

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    @property
    def native_value(self) -> float | None:
        wfl = (self.coordinator.data or {}).get("weight_for_length")
        if not wfl or wfl.get("percentile") is None:
            return None
        return round(wfl["percentile"], 1)

    @property
    def extra_state_attributes(self) -> dict:
        wfl = (self.coordinator.data or {}).get("weight_for_length") or {}
        return {
            "length_cm": wfl.get("length_cm"),
            "weight_kg": wfl.get("weight_kg"),
            "band": wfl.get("band"),
            "z_score": wfl.get("z_score"),
            "top_percent": wfl.get("top_percent"),
            "summary_ko": wfl.get("summary_ko"),
            "measured_at": wfl.get("measured_at"),
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class NextEventSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    """Timestamp sensor exposing the start of the next scheduled event.

    Lets dashboards render `Relative` cards ("in 14 days") and lets
    automations use `numeric_state` triggers without parsing calendar
    entity attributes.
    """

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP
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
        self._data_key = data_key
        self._attr_name = label
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_{slug}"

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    def _next_event(self):
        events = (self.coordinator.data or {}).get(self._data_key, [])
        return events[0] if events else None

    @property
    def native_value(self) -> datetime | None:
        event = self._next_event()
        if event is None:
            return None
        return datetime.combine(event.start, time.min, tzinfo=TZ_ASIA_SEOUL)

    @property
    def extra_state_attributes(self) -> dict:
        event = self._next_event()
        if event is None:
            return {"upcoming_count": 0}
        events = (self.coordinator.data or {}).get(self._data_key, [])
        return {
            "code": event.code,
            "name_ko": event.name_ko,
            "name_en": event.name_en,
            "dose": event.dose,
            "window_start": event.start.isoformat(),
            "window_end": event.end.isoformat(),
            "upcoming_count": len(events),
        }


class CareTuitionSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    """One of the three childcare-tuition figures for the current age class.

    State is ``None`` when the bundled tuition table is still in placeholder
    mode (``data_year == 0``), so dashboards don't show misleading zeros.
    The raw figure is always surfaced in ``raw_value`` so power users can
    write templates against it.
    """

    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = "KRW"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: BabyKitCoordinator,
        entry: ConfigEntry,
        field: str,
        slug: str,
        label: str,
    ) -> None:
        super().__init__(coordinator)
        self._field = field
        self._attr_name = label
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_{slug}"

    @property
    def device_info(self):
        return child_device(self.coordinator.entry)

    def _tier(self) -> dict | None:
        return (self.coordinator.data or {}).get("care_tuition")

    @property
    def available(self) -> bool:
        return self._tier() is not None

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
        return {
            "age_class": tier.get("age_class"),
            "age_class_label_ko": tier.get("label_ko"),
            "age_class_label_en": tier.get("label_en"),
            "data_year": tier.get("data_year"),
            "source_url": tier.get("source_url"),
            "raw_value": tier.get(self._field),
            "is_placeholder": tier.get("is_placeholder"),
            "disclaimer": MEDICAL_DISCLAIMER,
        }


class BMIRawSensor(CoordinatorEntity[BabyKitCoordinator], SensorEntity):
    """Raw BMI value (kg/m²) for every age.

    Complements the existing BMI percentile sensor, which is `unknown` under
    24 months because KDCA's BMI reference table starts there. The raw BMI is
    meaningful at every age, so this sensor stays populated as long as a
    height + weight measurement exists. Under 24 months the `summary_ko`
    attribute redirects readers to weight-for-length instead.
    """

    _attr_has_entity_name = True
    _attr_name = "정보 · BMI 수치"
    _attr_native_unit_of_measurement = "kg/m²"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_attribution = ATTRIBUTION
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator: BabyKitCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.child_id}_bmi_raw"

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
        age_m = data.get("age_months") or 0
        if age_m < 24:
            summary = "만 24개월 미만 — KDCA BMI 백분위 미정의, 신장별 몸무게 백분위를 함께 확인하세요."
        else:
            summary = bmi_info.get("summary_ko")
        return {
            "measured_at": data.get("bmi_measured_at"),
            "age_months": data.get("age_months"),
            "percentile": bmi_info.get("percentile"),
            "top_percent": bmi_info.get("top_percent"),
            "z_score": bmi_info.get("z_score"),
            "summary_ko": summary,
            "disclaimer": MEDICAL_DISCLAIMER,
        }
