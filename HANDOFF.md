# Handover Document — Baby Kit (`kr_baby_kit`)

> Last updated: 2026-11-25 (Latest released tag: `v0.17.1`)

## 1. Project Overview

**Baby Kit** (Home Assistant domain: `kr_baby_kit`, HACS custom integration) is an offline-first Home Assistant integration for tracking child growth percentiles, immunization/checkup schedules, daily care logs (Baby Buddy–style), live timers, and photo diaries.

- **Repository**: `https://github.com/redchupa/kr_baby_kit`
- **Display name**: `Baby Kit` (renamed from `Korean Baby Kit` in `v0.15.0`; internal domain `kr_baby_kit` kept unchanged for backward compatibility).
- **Minimum Home Assistant**: `2024.11.0`
- **Supported regional profiles**:
  - `kr` (South Korea): KDCA 2017 growth charts (LMS), KDCA NIP immunizations, NHIS 8 infant health checkups + 4 oral checkups, MOE 2026 childcare tuition.
  - `global` (International): WHO Child Growth Standards (0–5y, 2006) & WHO Growth Reference (5–19y, 2007), WHO routine immunization reference, general pediatric & dental well-child milestones.

---

## 2. Critical Rules & Guardrails

1. **Privacy / Security Guard (Strict)**:
   - NEVER commit real child names, real birthdates, real measurements, daycare names, family names, or private LAN HA URLs/IPs.
   - CI enforces a regex check in `.github/workflows/test.yml` (`security-grep` job).
   - Use synthetic data only (`Child A`, `Baby A`, `2020-03-15`, `2024-07-01`).
2. **Release Checklist**:
   - Bump `custom_components/kr_baby_kit/manifest.json`, `custom_components/kr_baby_kit/panel.py` (`PANEL_VERSION` + JS `?v=` query strings in `frontend/panel.js`), and `CHANGELOG.md`.
   - Run `pytest -q`, `ruff check`, `python scripts/check_care_tuition.py --strict`, and Node ES module check.
   - Commit, push `main`, push annotated tag `vX.Y.Z`, and publish GitHub Release via `gh release create`.
3. **Backward Compatibility**:
   - Never change `DOMAIN = "kr_baby_kit"` or existing `unique_id` formats.
   - Existing Korean config entries without `profile` default to `kr`.

---

## 3. Architecture & File Map

### Backend (`custom_components/kr_baby_kit/`)
| File | Responsibility |
|---|---|
| `__init__.py` | Entry setup/unload/remove; loads profile-specific data, coordinator, LLM API, services, WebSocket API, and sidebar panel |
| `const.py` | Constants, `PROFILE_KR` / `PROFILE_GLOBAL`, `DEFAULT_BIRTHDATE = "2024-07-01"`, attribution & disclaimer helpers, `is_korean()` |
| `config_flow.py` | Config Flow & Options Flow with localized `SelectSelector` (`child_sex`, `profile`), default birthdate `2024-07-01` |
| `coordinator.py` | `BabyKitCoordinator` — computes age, LMS percentiles, BMI, weight-for-length, schedules, and KR tuition using HA local timezone (`dt_util`) |
| `growth.py` | LMS interpolation (`GrowthChart.from_profile("kr" | "global")`), `rank_percent`, `format_summary_ko`, `format_summary_en` |
| `schedule.py` | Calendar-month schedule projection for vaccines (incl. seasonal influenza), health checkups, and oral checkups |
| `care_tuition.py` | Birth-year age class lookup for South Korea MOE childcare tuition |
| `storage.py` | Lock-serialized HA `Store` persistence for measurement records, schedule completions, Baby Buddy activities, live timers, profile avatars, and private `.storage/kr_baby_kit_media/` photo files |
| `media_view.py` | Authenticated `HomeAssistantView` (`/api/kr_baby_kit/media/{child_id}/{filename}`, `requires_auth = True`) + short-lived signed URL helper (`sign_media_url`) with legacy `/local/` fallback |
| `sensor.py` | Localized percentile, age, BMI, next-event, open-deadline, daily care (`today_sleep_minutes`, `today_feeding_ml`, `today_diaper_count`, `last_temperature`, `active_timers`), and KR-only childcare tuition sensors |
| `binary_sensor.py` | Localized monthly due sensors + bi-directional concern alerts (`head_concern`, `bmi_concern`, `weight_for_length_concern`) |
| `calendar.py` | Localized immunization, health checkup, and oral/dental checkup calendars |
| `number.py` | Measurement input entities; fall back to 50th-percentile LMS median (`is_default_median: true`) before first measurement |
| `services.py` | `record_measurement`, `delete_measurement`, `get_measurements`, `mark_event_done`, `unmark_event_done`, `get_schedule` |
| `llm_api.py` | Per-child Home Assistant Assist LLM API (omits tuition tool for `global` profile) |
| `websocket_api.py` | WebSocket commands: `get_overview`, `add_child`, `update_child`, `delete_child`, `set_avatar`, `add_activity`, `delete_activity`, `start_timer`, `stop_timer` |
| `panel.py` | Registers static `/kr_baby_kit_static` and sidebar panel `Baby Kit` (`kr-baby-kit-panel`) |
| `strings.json`, `translations/en.json`, `translations/ko.json` | Full EN/KO localization for config/options, selectors, services, and all entities |

### Bundled Reference Data (`custom_components/kr_baby_kit/data/`)
- `growth_chart_kr.json` — KDCA 2017 LMS tables (0–228m)
- `growth_chart_who.json` — WHO Child Growth Standards (0–60m, 2006) + WHO Reference (61–228m, 2007)
- `nip_schedule.json` / `health_checkup_schedule.json` — South Korea NIP & NHIS schedules
- `who_schedule.json` / `global_checkup_schedule.json` — International WHO routine vaccine & well-child schedules
- `care_tuition_kr.json` — South Korea 2026 MOE childcare tuition rates

### Frontend (`custom_components/kr_baby_kit/frontend/`)
- `panel.js` — Main `<kr-baby-kit-panel>` Shadow DOM web component (Hero card + `D+days`, status chips, Baby Buddy daily care & live timers, modal/bottom-sheet care logger with draft preservation, one-tap logs, photo diary & lightbox, LMS growth curve chart + gauges & sparklines, schedules with collapse/expand, mobile bottom nav bar, top-bar `EN`/`한국어` toggle, Gear customization drawer)
- `charts.js` — Interactive LMS Growth Curve SVG chart (P3/P15/P50/P85/P97 bands + child trajectory + current-age marker) and 7-day Sleep & Feeding grouped bar chart
- `themes.js` — 12 architectural themes (`ha-native`, `nordic-nursery`, `paper-journal`, `glass-aurora`, `midnight-studio`, `bento-pop`, `clinical-chart`, `botanical-linen`, `pastel-cloud`, `retro-terminal`, `warm-terracotta`, `tokyo-minimal`)
- `cards.js` — 4 card style presets (`bubble`, `mushroom`, `bento-pro`, `classic`), inline SVG icon set, 0–100% LMS percentile gauge bar, and SVG growth sparkline

---

## 4. Completed in `v0.17.0` Upgrade

All priority security, backend, and UX/visual recommendations from the previous audit were implemented in `v0.17.0`:
1. **Authenticated Photo Serving (`media_view.py`, `storage.py`)**: Photos are now saved under `<config>/.storage/kr_baby_kit_media/<child_id>/` and served via `/api/kr_baby_kit/media/{child_id}/{filename}` (`requires_auth = True`) using `async_sign_path` short-lived signed URLs (with read/delete fallback for legacy `www/kr_baby_kit_media/` files).
2. **Admin Guard & Single Reload (`websocket_api.py`)**: Added `@websocket_api.require_admin` on `ws_delete_child` and removed the duplicate `async_reload` in `ws_update_child`.
3. **Draft State Preservation & Modal/Bottom-Sheet Care Logger (`frontend/panel.js`)**: Typed notes and inputs in `_careDraft` and `_measureDraft` persist across photo uploads, tab changes, and language switches; replaced the inline care form with clean category launcher tiles + slide-up/modal logger.
4. **Interactive LMS Growth Curve & 7-Day Care Charts (`frontend/charts.js`, `growth.py`, `coordinator.py`)**: Added inverse LMS `value_at_z` / `curve_series` (P3/P15/P50/P85/P97 shaded bands + child trajectory) and a 7-day Sleep & Feeding bar chart.
5. **Native HA Daily Care Sensors & Assist Tool (`sensor.py`, `llm_api.py`)**: Added `today_sleep_minutes`, `today_feeding_ml`, `today_diaper_count`, `last_temperature`, `active_timers`, and the `get_daily_care_summary` Assist LLM tool.

---

## 5. Quick Verification Commands

```powershell
# Unit + integration tests
pytest -q

# Lint
ruff check custom_components/kr_baby_kit tests/

# Childcare tuition table integrity
python scripts/check_care_tuition.py --strict

# Frontend ES module syntax check
node --input-type=module -e "globalThis.HTMLElement = class {}; globalThis.customElements = { get: () => true, define: () => {} }; globalThis.window = { localStorage: { getItem: () => null, setItem: () => {} }, setInterval: () => 1, clearInterval: () => {} }; import('./custom_components/kr_baby_kit/frontend/panel.js').then(() => console.log('OK'));"
```
