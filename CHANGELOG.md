# Changelog

All notable changes will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
versions follow [SemVer](https://semver.org/).

## [0.6.0] - 2026-05-13

### Changed (BREAKING — sensor numeric value meaning is inverted)

- **All percentile sensors now report a rank percent (`100 - statistical_percentile`) instead of the KDCA statistical percentile.** A tall child now shows a *small* number ("키 위치 = 5") and a small child shows a *large* number ("키 위치 = 90"), matching the school-ranking intuition the user expects.
- Affected sensors: `<child>_height_percentile`, `_weight_percentile`, `_head_percentile`, `_bmi_percentile`, `_weight_for_length_percentile`.
- `summary_ko` is rewritten to reuse the same rank number ("키: 또래 상위 5.3% (큰 편)" / "키: 또래 상위 95.0% (작은 편)" / "키: 또래 평균 수준"), so the on-card text and the sensor value never disagree.
- The original KDCA statistical percentile is preserved as a new attribute `statistical_percentile` for users who want the textbook form in their own templates.
- `top_percent` attribute is kept (same numeric value as the new `native_value`); existing templates that read `top_percent` continue to work unchanged.

### Automation example impact

- `docs/examples/automation-examples.yaml` updated:
  - Example #2 (small-stature alert): `below: 3` → `above: 97` to preserve the original "kid is short" intent under the inverted scale.
  - Example #4 (BMI extremes): threshold values unchanged (5 / 95) but the *meaning* flipped — `below: 5` now flags an unusually **high** BMI (비만 경향), `above: 95` flags an unusually **low** BMI (저체중 경향). The dual-threshold alert keeps catching both ends as before.
- Any automation users wrote against v0.4.0 / v0.5.0 percentile sensors needs the same flip. There are no on-disk migrations because `unique_id` is unchanged.

### Notes

- KDCA reference tables are not changed; the inversion is purely a display-layer decision so dashboard numbers behave like rankings (smaller = better-ranked for height, etc.).
- No bundled-data changes; care_tuition `data_year` still 2026; stale-check cron untouched.

## [0.5.0] - 2026-05-12

### Changed

- **Entity friendly names regrouped by category** so HA's sort-by-name view keeps related entities together. New form is `<카테고리> · <항목>`:
  - 측정 · 키 / 몸무게 / 머리둘레 (number inputs)
  - 백분위 · 키 / 몸무게 / 머리둘레 / BMI / 신장별 몸무게
  - 일정 · 다음 예방접종 / 다음 검진 / 이번 달 예방접종 / 이번 달 검진
  - 보육료 · 표준 / 정부지원금 / 본인부담금
  - 캘린더 · 예방접종 / 검진
  - 정보 · BMI 수치 / 월령 (개월 수)  ← `월령` was unfamiliar to non-medical users; the parenthesized hint stays.
- **`summary_ko` now mirrors the sensor's raw percentile**, so the on-card number always matches the sensor's native value. Previous form `"키: 또래 평균 상위 5.3%"` (when the percentile was 94.7) made two numbers visible at once and was easy to misread. New form: `"키: 또래보다 큰 편 (백분위 94.7)"` / `"몸무게: 또래보다 적게 나가는 편 (백분위 12.5)"` / `"BMI: 또래 평균 수준 (백분위 50.0)"`. Direction adjectives are picked per metric (키/머리둘레/BMI = "큰/작은", 몸무게/신장별 체중 = "많이/적게 나가는").
- `top_percent` attribute is preserved unchanged for users who prefer the inverted view in their own templates / cards.

### Notes

- `unique_id` for every entity is unchanged, so existing v0.4.0 installs keep their `entity_id` after upgrade — only the friendly name shifts. Brand-new installs (HACS first-install) pick up category-prefixed `entity_id` slugs.
- No bundled-data changes; `data_year` still 2026, `care_tuition_stale_check.yml` cron untouched.
- Donation QR table added to README (Toss + PayPal) — same pattern already in `ha-app-dhlottery` and `kr_component_kit`.

## [0.4.0] - 2026-05-12

### Added
- **Childcare tuition (보육료) integration** — new `data/care_tuition_kr.json` table covering 만 0~6세반 age classes, plus a `care_tuition.py` lookup module.
- Three new sensors per child: `<child>_표준보육료`, `<child>_보육료_정부지원금`, `<child>_보육료_본인부담금` (unit: KRW). Each surfaces the matching age-class tier and exposes raw + placeholder flag in `extra_state_attributes`.
- LLM tool `get_care_tuition` — answers "이번 달 보육료 얼마야?" / "정부지원금 얼마?" with the tier matching the child's current age class.
- Release-gate script `scripts/check_care_tuition.py`: validates 만 0~6세반 coverage, age-range monotonicity, plausible `data_year`, no all-zero tiers when real values are present, and `parent_share + government_subsidy == standard_tuition`. Wired into the CI matrix in non-strict mode; run with `--strict` before tagging a release.

### Data
- Tuition table populated with the **2026년도 보육사업안내 (교육부)** figures:
  - 0세반 584,000원 · 1세반 515,000원 · 2세반 426,000원 · 3~5세반 280,000원 (누리공통과정).
  - 만 6세반: 취학유예 시(2019년생, 1차 한정) 만 5세반 단가(280,000)를 동일 적용.
  - 전 연령 종일반 기준 본인부담금 0원 (무상보육).
- Citation in `_meta`: 발간등록번호 `11-1342000-100026-10`, 교육부, effective `2026-01-01`.
- Source URL pinned to a public mirror of the official 부록 PDF — replace with the current 교육부 누리집 link when refreshing for 2027.

### Notes
- Boychild care policy moved from 보건복지부 → 교육부 in 2026 (유보통합). When updating for future years, use 교육부 누리집 as the primary source.
- Schema for `care_tuition_kr.json` is intentionally simple so users can paste annual updates with minimal effort.
- Coordinator now exposes `data["care_tuition"]` (dict or `None`) with the matched tier.

## [0.3.0] - 2026-05-12

### Added
- BMI percentile sensor (`sensor.<child>_bmi_percentile`) — derived from latest height + weight, gated to ≥24 months per KDCA reference range.
- Next-event timestamp sensors (`sensor.<child>_next_vaccine`, `sensor.<child>_next_checkup`) using `device_class: timestamp` so dashboards render relative-time tiles and automations can trigger on `numeric_state` directly.
- Additional automation examples: BMI extreme-percentile alert and TIMESTAMP-driven D-day notifications.

### Notes
- Existing growth percentile sensor unique_ids unchanged; BMI uses a new `<child_id>_bmi_percentile` unique_id.
- LLM `get_growth_percentiles` tool now includes BMI when applicable (no schema change).

## [0.2.0] - 2026-05-12

### Added
- KDCA 2017 full LMS tables bundled (height/weight/BMI/head, 0-228 months, both sexes).
- Weight-for-length percentile (recumbent length <2y, standing height 2y+) — three age bands per sex.
- `number` platform: `<child>_height` / `_weight` / `_head` entities for one-tap dashboard input.
- Same-date measurements automatically merge into a single record.
- LLM tools: `get_next_vaccine`, `get_next_checkup`, `get_growth_percentiles`, `list_upcoming_events`.
- `record_measurement` service for backfilling historical values.
- Korean + English translations.
- Documentation: installation-ko/en, automation examples, data-sources attribution.
- CI: hassfest + HACS validation + pytest matrix + security-grep for personal identifiers.
- Integration tests via `pytest-homeassistant-custom-component` (Linux only).

### Reference
- 질병관리청 2017 소아청소년 성장도표 — 공공누리 제1유형
- 질병관리청 표준 예방접종 일정 (NIP) — 공공누리 제1유형
- 보건복지부 영유아 건강검진 표준 7회 일정 — 공공누리 제1유형

## [0.1.0] - 2026-05-12

### Added
- Initial scaffold (M0): repository structure, manifest, config flow.
