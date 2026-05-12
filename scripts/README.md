# scripts/

Maintenance utilities. Not shipped with the integration.

## `build_growth_chart.py`

Materializes `custom_components/kr_baby_kit/data/growth_chart_kr.json` from the
KDCA-published source.

### From the official XLSX bundle

질병관리청 "2017 소아청소년 성장도표 — 성장도표+데이터+테이블.xls"
다운로드 → 임의 경로에 두고 실행:

```bash
python scripts/build_growth_chart.py path/to/성장도표+데이터+테이블.xls --xlsx
```

The script expects the published 7-sheet layout (height / weight / BMI /
length-weight × 3 / head). Length-weight sheets are skipped — v1 uses
age-indexed LMS only. After running, the bundled JSON contains:

- `male.height` / `female.height` — 0~228개월
- `male.weight` / `female.weight` — 0~228개월
- `male.bmi`    / `female.bmi`    — 24~227개월
- `male.head`   / `female.head`   — 0~72개월

### From a flat CSV (preferred for diffs / review)

Schema: `sex,kind,age_months,L,M,S`

```bash
python scripts/build_growth_chart.py path/to/lms.csv
```

### Notes

- Raw upstream files are **not** committed (see `.gitignore`). Redistribution
  is not within the 공공누리 제1유형 scope — attribution + the rebuilt JSON
  is.
- `--dry-run` prints row counts without writing.
- After rebuilding, run `python -m pytest tests/` to confirm fixture-bound
  tests still hold.

## `check_care_tuition.py`

Sanity-checks `data/care_tuition_kr.json` before tagging a release that
bumps the tuition `data_year`. Catches gaps in the 만 0~6세반 coverage,
forgotten tiers (still all-zero), and `parent_share + government_subsidy`
not summing to `standard_tuition`.

```bash
# Default: passes whether or not real values are present (placeholder mode allowed).
python scripts/check_care_tuition.py

# Release gate: fails if the bundle is still in placeholder mode.
python scripts/check_care_tuition.py --strict

# Check a candidate file before promoting it into the bundle.
python scripts/check_care_tuition.py --path path/to/care_tuition_candidate.json
```

Exit codes: `0` ok, `1` validation failure, `2` file not found.
