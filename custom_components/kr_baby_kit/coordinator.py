"""Coordinator for kr_baby_kit — per child entry."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CHILD_BIRTHDATE,
    CONF_CHILD_ID,
    CONF_CHILD_NAME,
    CONF_CHILD_SEX,
    DOMAIN,
    LOGGER,
    TZ_ASIA_SEOUL,
)
from .care_tuition import TuitionTier, tuition_for_age_months
from .growth import GrowthChart, age_months, format_summary_ko, top_percent
from .schedule import (
    project_checkup_events,
    project_vaccine_events,
    upcoming,
)
from .storage import async_load_records, latest


class BabyKitCoordinator(DataUpdateCoordinator):
    """Refreshes derived state for a single registered child."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.child_name: str = entry.data[CONF_CHILD_NAME]
        self.child_id: str = entry.data.get(CONF_CHILD_ID, entry.entry_id)
        self.child_sex: str = entry.data[CONF_CHILD_SEX]
        self.birthdate: date = date.fromisoformat(entry.data[CONF_CHILD_BIRTHDATE])
        self.chart = GrowthChart.from_default()
        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_{self.child_id}",
            update_interval=timedelta(hours=6),
        )

    async def _async_update_data(self) -> dict:
        records = (await async_load_records(self.hass)).get(self.child_id, [])
        today = datetime.now(TZ_ASIA_SEOUL).date()
        age_m = age_months(self.birthdate.isoformat(), today.isoformat())

        percentiles: dict[str, dict] = {}
        for kind in ("height", "weight", "head"):
            last = latest(records, kind)
            if not last:
                continue
            z, pct = self.chart.percentile(
                self.child_sex, kind, age_m, float(last[kind])
            )
            percentiles[kind] = {
                "value": float(last[kind]),
                "measured_at": last["date"],
                "z_score": z,
                "percentile": pct,
                "top_percent": top_percent(pct),
                "summary_ko": format_summary_ko(kind, pct),
            }

        h_record = latest(records, "height")
        w_record = latest(records, "weight")
        # BMI raw value is always meaningful; KDCA BMI *percentile* table
        # only starts at 24 months (under-2s use weight-for-length instead).
        bmi_raw: float | None = None
        bmi_measured_at: str | None = None
        if h_record and w_record:
            h_cm = float(h_record["height"])
            w_kg = float(w_record["weight"])
            if h_cm > 0:
                bmi_raw = round(w_kg / (h_cm / 100.0) ** 2, 2)
                bmi_measured_at = max(h_record["date"], w_record["date"])
                if age_m >= 24 and self.chart.has(self.child_sex, "bmi"):
                    z, pct = self.chart.percentile(
                        self.child_sex, "bmi", age_m, bmi_raw
                    )
                    if pct is not None:
                        percentiles["bmi"] = {
                            "value": bmi_raw,
                            "measured_at": bmi_measured_at,
                            "z_score": z,
                            "percentile": pct,
                            "top_percent": top_percent(pct),
                            "summary_ko": format_summary_ko("bmi", pct),
                        }

        weight_for_length: dict | None = None
        if h_record and w_record:
            h = float(h_record["height"])
            w = float(w_record["weight"])
            z, pct, band = self.chart.weight_for_length_percentile(
                self.child_sex, age_m, h, w
            )
            if pct is not None:
                weight_for_length = {
                    "length_cm": h,
                    "weight_kg": w,
                    "band": band,
                    "z_score": z,
                    "percentile": pct,
                    "top_percent": top_percent(pct),
                    "summary_ko": format_summary_ko("weight_for_length", pct),
                    "measured_at": max(
                        h_record["date"], w_record["date"]
                    ),
                }

        vaccines = upcoming(project_vaccine_events(self.birthdate), today)
        checkups = upcoming(project_checkup_events(self.birthdate), today)

        tier: TuitionTier | None = tuition_for_age_months(age_m)
        care_tuition = None
        if tier is not None:
            care_tuition = {
                "age_class": tier.age_class,
                "label_ko": tier.label_ko,
                "label_en": tier.label_en,
                "standard_tuition": tier.standard_tuition,
                "government_subsidy": tier.government_subsidy,
                "parent_share": tier.parent_share,
                "data_year": tier.data_year,
                "source_url": tier.source_url,
                "is_placeholder": tier.is_placeholder,
            }

        return {
            "age_months": age_m,
            "today": today.isoformat(),
            "records": records,
            "percentiles": percentiles,
            "weight_for_length": weight_for_length,
            "upcoming_vaccines": vaccines,
            "upcoming_checkups": checkups,
            "care_tuition": care_tuition,
            "bmi_raw": bmi_raw,
            "bmi_measured_at": bmi_measured_at,
        }
