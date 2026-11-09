"""Coordinator for kr_baby_kit — per child entry."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CHILD_BIRTHDATE,
    CONF_CHILD_ID,
    CONF_CHILD_NAME,
    CONF_CHILD_SEX,
    DOMAIN,
    LOGGER,
    TZ_ASIA_SEOUL,
    UPDATE_INTERVAL,
)
from .care_tuition import TuitionTier, tuition_for_age_months
from .growth import GrowthChart, age_months, format_summary_ko, rank_percent
from .schedule import (
    project_checkup_events,
    project_oral_checkup_events,
    project_vaccine_events,
    upcoming,
)
from .storage import async_get_child_completions, async_load_records, latest

UPCOMING_HORIZON_DAYS = 365 * 20


class BabyKitCoordinator(DataUpdateCoordinator):
    """Refreshes derived state for a single registered child."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        *,
        chart: GrowthChart,
        nip_schedule: dict,
        checkup_schedule: dict,
        tuition_table: dict,
    ) -> None:
        self.entry = entry
        self.child_name: str = entry.data[CONF_CHILD_NAME]
        self.child_id: str = entry.data.get(CONF_CHILD_ID, entry.entry_id)
        self.child_sex: str = entry.data[CONF_CHILD_SEX]
        self.birthdate: date = date.fromisoformat(entry.data[CONF_CHILD_BIRTHDATE])
        self.chart = chart
        self._nip_schedule = nip_schedule
        self._checkup_schedule = checkup_schedule
        self._tuition_table = tuition_table
        # Schedule projections depend only on the birthdate, so compute them
        # once per entry load (the entry reloads when the birthdate changes).
        self.all_vaccines = project_vaccine_events(self.birthdate, nip_schedule)
        self.all_checkups = project_checkup_events(self.birthdate, checkup_schedule)
        self.all_oral_checkups = project_oral_checkup_events(
            self.birthdate, checkup_schedule
        )
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{self.child_id}",
            update_interval=UPDATE_INTERVAL,
        )

    def _age_at(self, iso_date: str) -> float:
        return max(0.0, age_months(self.birthdate.isoformat(), iso_date))

    def known_event_ids(self) -> set[str]:
        return {
            e.event_id
            for e in (*self.all_vaccines, *self.all_checkups, *self.all_oral_checkups)
        }

    @callback
    def async_schedule_midnight_refresh(self) -> Callable[[], None]:
        """Refresh right after every Asia/Seoul midnight.

        Returns an unsubscribe callable; the entry owns it via
        ``entry.async_on_unload``.
        """
        unsub: Callable[[], None] | None = None

        @callback
        def _arm() -> None:
            nonlocal unsub
            now = datetime.now(TZ_ASIA_SEOUL)
            next_midnight = datetime.combine(
                now.date() + timedelta(days=1), time(0, 0, 5), tzinfo=TZ_ASIA_SEOUL
            )
            unsub = async_track_point_in_utc_time(self.hass, _fire, next_midnight)

        @callback
        def _fire(_now: datetime) -> None:
            self.hass.async_create_task(self.async_request_refresh())
            _arm()

        _arm()

        @callback
        def _cancel() -> None:
            if unsub is not None:
                unsub()

        return _cancel

    async def _async_update_data(self) -> dict:
        records = (await async_load_records(self.hass)).get(self.child_id, [])
        completed = await async_get_child_completions(self.hass, self.child_id)
        today = datetime.now(TZ_ASIA_SEOUL).date()
        age_m = age_months(self.birthdate.isoformat(), today.isoformat())

        percentiles: dict[str, dict] = {}
        for kind in ("height", "weight", "head"):
            last = latest(records, kind)
            if not last:
                continue
            # Compare against the curve at the age the child was MEASURED,
            # not the current age; otherwise an old record drifts toward the
            # bottom of the chart as the child grows (pre-v0.9.0 bug).
            age_at = self._age_at(last["date"])
            z, pct = self.chart.percentile(
                self.child_sex, kind, age_at, float(last[kind])
            )
            rank = rank_percent(kind, pct)
            percentiles[kind] = {
                "value": float(last[kind]),
                "measured_at": last["date"],
                "z_score": z,
                # "percentile" is the user-facing sensor value. For metrics
                # that favor a single direction (height, weight) this is the
                # rank percent (big raw → small number). For bi-directional
                # metrics (head, bmi, weight_for_length) this stays as the
                # KDCA statistical percentile so 50 means "normal".
                "percentile": rank,
                "statistical_percentile": pct,
                "top_percent": round(max(0.0, 100.0 - pct), 1) if pct is not None else None,
                "summary_ko": format_summary_ko(kind, pct),
                "age_months_at_measurement": round(age_at, 2),
            }

        h_record = latest(records, "height")
        w_record = latest(records, "weight")
        # BMI raw value is always meaningful; KDCA BMI *percentile* table
        # only starts at 24 months (under-2s use weight-for-length instead).
        bmi_raw: float | None = None
        bmi_measured_at: str | None = None
        bmi_age: float | None = None
        if h_record and w_record:
            h_cm = float(h_record["height"])
            w_kg = float(w_record["weight"])
            if h_cm > 0:
                bmi_raw = round(w_kg / (h_cm / 100.0) ** 2, 2)
                bmi_measured_at = max(h_record["date"], w_record["date"])
                bmi_age = self._age_at(bmi_measured_at)
                if bmi_age >= 24 and self.chart.has(self.child_sex, "bmi"):
                    z, pct = self.chart.percentile(
                        self.child_sex, "bmi", bmi_age, bmi_raw
                    )
                    if pct is not None:
                        rank = rank_percent("bmi", pct)
                        percentiles["bmi"] = {
                            "value": bmi_raw,
                            "measured_at": bmi_measured_at,
                            "z_score": z,
                            "percentile": rank,
                            "statistical_percentile": pct,
                            "top_percent": round(max(0.0, 100.0 - pct), 1),
                            "summary_ko": format_summary_ko("bmi", pct),
                            "age_months_at_measurement": round(bmi_age, 2),
                        }

        weight_for_length: dict | None = None
        if h_record and w_record:
            h = float(h_record["height"])
            w = float(w_record["weight"])
            wfl_at = max(h_record["date"], w_record["date"])
            z, pct, band = self.chart.weight_for_length_percentile(
                self.child_sex, self._age_at(wfl_at), h, w
            )
            if pct is not None:
                rank = rank_percent("weight_for_length", pct)
                weight_for_length = {
                    "length_cm": h,
                    "weight_kg": w,
                    "band": band,
                    "z_score": z,
                    "percentile": rank,
                    "statistical_percentile": pct,
                    "top_percent": round(max(0.0, 100.0 - pct), 1),
                    "summary_ko": format_summary_ko("weight_for_length", pct),
                    "measured_at": max(
                        h_record["date"], w_record["date"]
                    ),
                }

        # No practical horizon: the next-event sensors must show the next
        # window even when it is more than a year out (e.g. the first oral
        # checkup at 18 months for a newborn). "This month" sensors and the
        # LLM list filter by their own date range.
        vaccines = upcoming(
            self.all_vaccines, today, UPCOMING_HORIZON_DAYS, completed
        )
        checkups = upcoming(
            self.all_checkups, today, UPCOMING_HORIZON_DAYS, completed
        )
        oral_checkups = upcoming(
            self.all_oral_checkups, today, UPCOMING_HORIZON_DAYS, completed
        )

        tier: TuitionTier | None = tuition_for_age_months(
            age_m, self._tuition_table
        )
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
            "upcoming_oral_checkups": oral_checkups,
            "all_vaccines": self.all_vaccines,
            "all_checkups": self.all_checkups,
            "all_oral_checkups": self.all_oral_checkups,
            "completed": completed,
            "care_tuition": care_tuition,
            "bmi_raw": bmi_raw,
            "bmi_measured_at": bmi_measured_at,
            # Age at the BMI measurement: decides the under-24-month advisory
            # (KDCA BMI percentiles start at 24 months of age *at measurement*).
            "bmi_age_months": round(bmi_age, 2) if bmi_age is not None else None,
        }
