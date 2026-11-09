"""NIP immunization, infant checkup, and infant oral checkup schedule projection.

Given a child's birthdate, compute vaccine dose windows and checkup windows
based on bundled JSON tables.

Window arithmetic (v0.9.0):

* Whole-month offsets use **calendar months** (생후 N개월 = the same day-of-
  month N months later, clamped to month end) instead of the previous
  30.4375-day approximation, so dates line up with what 건강iN shows.
* Fractional-month offsets still fall back to the day approximation.
* Checkup windows (`window_*_month`) are **inclusive month-of-age ranges**:
  "생후 4~6개월" runs from the day the child turns 4 months up to the day
  before they turn 7 months. Day-based windows (`window_*_day`, 1차 검진
  생후 14~35일) are taken literally.
"""
from __future__ import annotations

import calendar
import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

_DATA_DIR = Path(__file__).parent / "data"
_NIP_PATH = _DATA_DIR / "nip_schedule.json"
_CHECKUP_PATH = _DATA_DIR / "health_checkup_schedule.json"

_AVG_DAYS_PER_MONTH = 30.4375

KIND_VACCINE = "vaccine"
KIND_CHECKUP = "checkup"
KIND_ORAL_CHECKUP = "oral_checkup"


@dataclass(frozen=True)
class ScheduleEvent:
    kind: str          # "vaccine" | "checkup" | "oral_checkup"
    code: str
    name_ko: str
    name_en: str
    dose: int | None
    start: date
    end: date
    note: str = ""
    items: tuple[str, ...] = field(default_factory=tuple)
    window_note: str = ""
    season: int | None = None  # annual vaccines: season start year
    dose_count: int | None = None  # total doses of this vaccine (1 = single shot)

    @property
    def event_id(self) -> str:
        """Stable identifier used by the completion services.

        Vaccines: ``<code>_<dose>`` (e.g. ``DTaP_4``). Checkups already carry
        their order in the code (``checkup_3``, ``oral_checkup_2``).
        """
        if self.season is not None:
            return f"{self.code}_{self.season}"
        if self.kind == KIND_VACCINE and self.dose is not None:
            return f"{self.code}_{self.dose}"
        return self.code


def add_calendar_months(start: date, months: int) -> date:
    """Return the same day-of-month ``months`` later, clamped to month end."""
    total = start.month - 1 + months
    year = start.year + total // 12
    month = total % 12 + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _add_months(start: date, months: float) -> date:
    if float(months).is_integer():
        return add_calendar_months(start, int(months))
    return start + timedelta(days=round(months * _AVG_DAYS_PER_MONTH))


def load_nip_schedule(path: Path | None = None) -> dict:
    with (path or _NIP_PATH).open(encoding="utf-8") as fh:
        return json.load(fh)


def load_checkup_schedule(path: Path | None = None) -> dict:
    with (path or _CHECKUP_PATH).open(encoding="utf-8") as fh:
        return json.load(fh)


async def async_load_nip_schedule(hass, path: Path | None = None) -> dict:
    """Async variant safe to call from the HA event loop."""
    return await hass.async_add_executor_job(load_nip_schedule, path)


async def async_load_checkup_schedule(hass, path: Path | None = None) -> dict:
    """Async variant safe to call from the HA event loop."""
    return await hass.async_add_executor_job(load_checkup_schedule, path)


def project_vaccine_events(
    birthdate: date,
    schedule: dict | None = None,
) -> list[ScheduleEvent]:
    src = schedule or load_nip_schedule()
    events: list[ScheduleEvent] = []
    for vaccine in src.get("vaccines", []):
        dose_count = len(vaccine.get("doses", []))
        for dose in vaccine.get("doses", []):
            wmin = float(dose.get("window_min", dose.get("recommended_month", 0)))
            wmax = float(dose.get("window_max", wmin))
            if dose.get("recurrence") == "annual_season":
                events.extend(_project_seasonal(birthdate, vaccine, dose, wmin, wmax))
                continue
            events.append(
                ScheduleEvent(
                    kind=KIND_VACCINE,
                    code=vaccine["code"],
                    name_ko=vaccine["name_ko"],
                    name_en=vaccine.get("name_en", ""),
                    dose=dose.get("dose"),
                    start=_add_months(birthdate, wmin),
                    end=_add_months(birthdate, wmax),
                    note=dose.get("note", ""),
                    dose_count=dose_count,
                )
            )
    return sort_events(events)


def _mmdd(value: str, year: int) -> date:
    month, day = (int(x) for x in value.split("-"))
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def _project_seasonal(
    birthdate: date, vaccine: dict, dose: dict, wmin: float, wmax: float
) -> list[ScheduleEvent]:
    """One event per season (e.g. 인플루엔자 10월~이듬해 4월) while eligible.

    Eligibility runs from ``wmin`` months of age up to the day before
    ``wmax`` months; each season window is clipped to it.
    """
    eligible_start = _add_months(birthdate, wmin)
    eligible_end = _add_months(birthdate, wmax) - timedelta(days=1)
    season_start = dose.get("season_start_mmdd", "10-01")
    season_end = dose.get("season_end_mmdd", "04-30")
    out: list[ScheduleEvent] = []
    for year in range(eligible_start.year - 1, eligible_end.year + 1):
        start = max(_mmdd(season_start, year), eligible_start)
        end = min(_mmdd(season_end, year + 1), eligible_end)
        if start > end:
            continue
        out.append(
            ScheduleEvent(
                kind=KIND_VACCINE,
                code=vaccine["code"],
                name_ko=f"{vaccine['name_ko']} ({year}-{year + 1} 절기)",
                name_en=f"{vaccine.get('name_en', '')} ({year}-{year + 1} season)",
                dose=None,
                start=start,
                end=end,
                note=dose.get("note", ""),
                season=year,
            )
        )
    return out


def _checkup_window(birthdate: date, entry: dict) -> tuple[date, date]:
    if "window_min_day" in entry:
        start = birthdate + timedelta(days=int(entry["window_min_day"]))
        end = birthdate + timedelta(days=int(entry["window_max_day"]))
        return start, end
    wmin = float(entry["window_min_month"])
    wmax = float(entry["window_max_month"])
    start = _add_months(birthdate, wmin)
    # Inclusive month-of-age: "~6개월" ends the day before turning 7 months.
    end = _add_months(birthdate, wmax + 1) - timedelta(days=1)
    return start, end


def _project_checkup_list(
    birthdate: date, entries: Iterable[dict], *, kind: str, code_prefix: str
) -> list[ScheduleEvent]:
    events: list[ScheduleEvent] = []
    for entry in entries:
        start, end = _checkup_window(birthdate, entry)
        events.append(
            ScheduleEvent(
                kind=kind,
                code=f"{code_prefix}_{entry['order']}",
                name_ko=entry["name_ko"],
                name_en=entry.get("name_en", ""),
                dose=entry["order"],
                start=start,
                end=end,
                note=entry.get("note_ko", ""),
                items=tuple(entry.get("items_ko") or ()),
                window_note=entry.get("window_note_ko", ""),
            )
        )
    return sort_events(events)


def project_checkup_events(
    birthdate: date,
    schedule: dict | None = None,
) -> list[ScheduleEvent]:
    src = schedule or load_checkup_schedule()
    return _project_checkup_list(
        birthdate, src.get("checkups", []), kind=KIND_CHECKUP, code_prefix="checkup"
    )


def project_oral_checkup_events(
    birthdate: date,
    schedule: dict | None = None,
) -> list[ScheduleEvent]:
    src = schedule or load_checkup_schedule()
    return _project_checkup_list(
        birthdate,
        src.get("oral_checkups", []),
        kind=KIND_ORAL_CHECKUP,
        code_prefix="oral_checkup",
    )


def sort_events(events: Iterable[ScheduleEvent]) -> list[ScheduleEvent]:
    """Chronological order — earliest window first, ties by end then id."""
    return sorted(events, key=lambda e: (e.start, e.end, e.event_id))


def upcoming(
    events: list[ScheduleEvent],
    today: date,
    horizon_days: int = 365,
    completed: Iterable[str] | None = None,
) -> list[ScheduleEvent]:
    """Open or upcoming windows within the horizon, soonest first.

    ``completed`` is an iterable of ``event_id`` values to drop (doses the
    parent already marked as done).
    """
    horizon = today + timedelta(days=horizon_days)
    done = set(completed or ())
    return sort_events(
        e
        for e in events
        if e.end >= today and e.start <= horizon and e.event_id not in done
    )


STATUS_DONE = "done"
STATUS_OPEN = "open"
STATUS_UPCOMING = "upcoming"
STATUS_MISSED = "missed"


def event_status(
    event: ScheduleEvent, today: date, completed: Iterable[str] | dict | None = None
) -> str:
    """done / open (window includes today) / upcoming / missed (window passed)."""
    if completed and event.event_id in completed:
        return STATUS_DONE
    if event.end < today:
        return STATUS_MISSED
    if event.start > today:
        return STATUS_UPCOMING
    return STATUS_OPEN


def event_to_dict(
    event: ScheduleEvent,
    today: date | None = None,
    completed: dict | None = None,
) -> dict:
    """JSON-friendly view shared by services, LLM tools, and attributes."""
    out = {
        "event_id": event.event_id,
        "kind": event.kind,
        "code": event.code,
        "name_ko": event.name_ko,
        "name_en": event.name_en,
        "dose": event.dose,
        "window_start": event.start.isoformat(),
        "window_end": event.end.isoformat(),
    }
    if event.note:
        out["note"] = event.note
    if event.window_note:
        out["window_note_ko"] = event.window_note
    if event.items:
        out["items_ko"] = list(event.items)
    if today is not None:
        out["status"] = event_status(event, today, completed)
    if completed and event.event_id in completed:
        out["completed_date"] = (completed[event.event_id] or {}).get("date")
    return out
