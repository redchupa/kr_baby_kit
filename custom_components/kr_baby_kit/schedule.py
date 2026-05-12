"""NIP immunization and infant checkup schedule projection.

Given a child's birthdate, compute upcoming vaccine doses and checkup windows
based on bundled JSON tables.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

_DATA_DIR = Path(__file__).parent / "data"
_NIP_PATH = _DATA_DIR / "nip_schedule.json"
_CHECKUP_PATH = _DATA_DIR / "health_checkup_schedule.json"

_AVG_DAYS_PER_MONTH = 30.4375


@dataclass(frozen=True)
class ScheduleEvent:
    kind: str          # "vaccine" | "checkup"
    code: str
    name_ko: str
    name_en: str
    dose: int | None
    start: date
    end: date
    note: str = ""


def _add_months(start: date, months: float) -> date:
    return start + timedelta(days=round(months * _AVG_DAYS_PER_MONTH))


def load_nip_schedule(path: Path | None = None) -> dict:
    with (path or _NIP_PATH).open(encoding="utf-8") as fh:
        return json.load(fh)


def load_checkup_schedule(path: Path | None = None) -> dict:
    with (path or _CHECKUP_PATH).open(encoding="utf-8") as fh:
        return json.load(fh)


def project_vaccine_events(
    birthdate: date,
    schedule: dict | None = None,
) -> list[ScheduleEvent]:
    src = schedule or load_nip_schedule()
    events: list[ScheduleEvent] = []
    for vaccine in src.get("vaccines", []):
        for dose in vaccine.get("doses", []):
            wmin = float(dose.get("window_min", dose.get("recommended_month", 0)))
            wmax = float(dose.get("window_max", wmin))
            events.append(
                ScheduleEvent(
                    kind="vaccine",
                    code=vaccine["code"],
                    name_ko=vaccine["name_ko"],
                    name_en=vaccine.get("name_en", ""),
                    dose=dose.get("dose"),
                    start=_add_months(birthdate, wmin),
                    end=_add_months(birthdate, wmax),
                    note=dose.get("note", ""),
                )
            )
    return events


def project_checkup_events(
    birthdate: date,
    schedule: dict | None = None,
) -> list[ScheduleEvent]:
    src = schedule or load_checkup_schedule()
    events: list[ScheduleEvent] = []
    for entry in src.get("checkups", []):
        wmin = float(entry["window_min_month"])
        wmax = float(entry["window_max_month"])
        events.append(
            ScheduleEvent(
                kind="checkup",
                code=f"checkup_{entry['order']}",
                name_ko=entry["name_ko"],
                name_en=entry.get("name_en", ""),
                dose=entry["order"],
                start=_add_months(birthdate, wmin),
                end=_add_months(birthdate, wmax),
            )
        )
    return events


def upcoming(events: list[ScheduleEvent], today: date, horizon_days: int = 365) -> list[ScheduleEvent]:
    horizon = today + timedelta(days=horizon_days)
    return [e for e in events if e.end >= today and e.start <= horizon]
