"""Sanity-check the bundled care_tuition_kr.json before a release.

Verifies:
  - All seven 만 0~6세반 tiers present, in order, with non-overlapping
    [age_months_min, age_months_max] ranges that fully cover 0..83 months.
  - `_meta.data_year` is a sane four-digit year (or 0 for placeholder mode).
  - When `_meta.data_year` is non-zero, no tier may be all zeros (catches
    "I forgot to fill in 만 5세반" mistakes before publishing).
  - `parent_share + government_subsidy == standard_tuition` per tier when
    real values are present.

Run before tagging a release that bumps the tuition `data_year`:

    python scripts/check_care_tuition.py
    python scripts/check_care_tuition.py --path some/other.json
    python scripts/check_care_tuition.py --strict   # disallow placeholder mode

Exits non-zero on any failure so it can be wired into CI.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = (
    REPO_ROOT
    / "custom_components"
    / "kr_baby_kit"
    / "data"
    / "care_tuition_kr.json"
)

EXPECTED_AGE_CLASSES: list[int] = [0, 1, 2, 3, 4, 5, 6]
COVERAGE_MIN = 0
COVERAGE_MAX = 83  # 만 6세반 (preschool) ends at 83 months inclusive
NUMERIC_FIELDS = ("standard_tuition", "government_subsidy", "parent_share")


def _fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def _check_meta(meta: dict, errors: list[str], strict: bool) -> bool:
    """Return True when we should also enforce the 'real values' invariants."""
    data_year = meta.get("data_year")
    try:
        year_int = int(data_year)
    except (TypeError, ValueError):
        _fail(errors, f"_meta.data_year must be an integer; got {data_year!r}")
        return False

    current_year = datetime.now().year
    if year_int == 0:
        if strict:
            _fail(errors, "_meta.data_year is 0 (placeholder) and --strict was set")
        return False

    if year_int < 2010 or year_int > current_year + 1:
        _fail(
            errors,
            f"_meta.data_year={year_int} looks implausible "
            f"(expected 2010..{current_year + 1})",
        )
    return True


def _check_tier_schema(tier: dict, errors: list[str]) -> None:
    required = (
        "age_class",
        "label_ko",
        "label_en",
        "age_months_min",
        "age_months_max",
        *NUMERIC_FIELDS,
    )
    for key in required:
        if key not in tier:
            _fail(errors, f"tier {tier.get('age_class', '?')} missing key '{key}'")


def _check_age_coverage(tiers: list[dict], errors: list[str]) -> None:
    sorted_tiers = sorted(tiers, key=lambda t: int(t.get("age_months_min", -1)))
    cursor = COVERAGE_MIN
    for tier in sorted_tiers:
        try:
            amin = int(tier["age_months_min"])
            amax = int(tier["age_months_max"])
        except (KeyError, TypeError, ValueError):
            return  # already reported by schema check
        if amin != cursor:
            _fail(
                errors,
                f"age coverage gap or overlap before tier {tier.get('age_class')}: "
                f"expected min={cursor}, got {amin}",
            )
        if amax < amin:
            _fail(
                errors,
                f"tier {tier.get('age_class')} has age_months_max < age_months_min",
            )
        cursor = amax + 1
    if cursor - 1 != COVERAGE_MAX:
        _fail(
            errors,
            f"age coverage stops at {cursor - 1}, expected {COVERAGE_MAX} "
            "(만 6세반 ends at 83 months inclusive)",
        )


def _check_age_classes(tiers: list[dict], errors: list[str]) -> None:
    classes = sorted(int(t.get("age_class", -1)) for t in tiers)
    if classes != EXPECTED_AGE_CLASSES:
        _fail(
            errors,
            f"age_class set is {classes}, expected {EXPECTED_AGE_CLASSES}",
        )


def _check_real_values(tiers: list[dict], errors: list[str]) -> None:
    for tier in tiers:
        try:
            std = int(tier.get("standard_tuition") or 0)
            sub = int(tier.get("government_subsidy") or 0)
            share = int(tier.get("parent_share") or 0)
        except (TypeError, ValueError):
            _fail(
                errors,
                f"tier {tier.get('age_class')} has non-integer tuition values",
            )
            continue

        if std == 0 and sub == 0 and share == 0:
            _fail(
                errors,
                f"tier {tier.get('age_class')} (만 {tier.get('age_class')}세반) "
                "is still all-zero - fill in or remove",
            )
            continue

        if sub + share != std:
            _fail(
                errors,
                f"tier {tier.get('age_class')}: parent_share({share:,}) + "
                f"government_subsidy({sub:,}) != standard_tuition({std:,}) "
                "(차액이 있다면 _meta._note에 사유 명시)",
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat placeholder mode (data_year == 0) as a failure",
    )
    args = parser.parse_args(argv)

    if not args.path.exists():
        print(f"care_tuition file not found: {args.path}", file=sys.stderr)
        return 2

    table = json.loads(args.path.read_text(encoding="utf-8"))
    meta = table.get("_meta") or {}
    tiers = table.get("tiers") or []

    errors: list[str] = []
    if not isinstance(tiers, list) or not tiers:
        _fail(errors, "tiers[] is missing or empty")
    else:
        _check_age_classes(tiers, errors)
        for tier in tiers:
            _check_tier_schema(tier, errors)
        _check_age_coverage(tiers, errors)

    enforce_real = _check_meta(meta, errors, strict=args.strict)
    if enforce_real:
        _check_real_values(tiers, errors)

    if errors:
        print(f"care_tuition sanity check FAILED ({len(errors)} issue(s)):")
        for msg in errors:
            print(f"  - {msg}")
        return 1

    mode = "REAL" if enforce_real else "placeholder"
    print(
        f"care_tuition sanity check OK - {len(tiers)} tiers, "
        f"data_year={meta.get('data_year')} ({mode})."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
