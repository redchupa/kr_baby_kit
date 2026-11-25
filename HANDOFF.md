# Handover Document — Baby Kit (`kr_baby_kit`)

> Last updated: 2026-11-25 (Latest released tag: `v0.16.0`, working tree includes `ruff` lint + photo-validation order fix + this `HANDOFF.md`)

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
   - NEVER commit real child names, real birthdates, real measurements, daycare names, family names, or private HA URLs/IPs (`192.168.*`, `10.0.*`, `ha.redchupa`).
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
| `storage.py` | Lock-serialized HA `Store` persistence for measurement records, schedule completions, Baby Buddy activities, live timers, profile avatars, and local photo files |
| `sensor.py` | Localized percentile, age, BMI, next-event, open-deadline, and KR-only childcare tuition sensors |
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
- `panel.js` — Main `<kr-baby-kit-panel>` Shadow DOM web component (Hero card + `D+days`, status chips, Baby Buddy daily care & live timers, one-tap logs, photo diary & lightbox, growth gauges & sparklines, schedules with collapse/expand, mobile bottom nav bar, top-bar `EN`/`한국어` toggle, Gear customization drawer)
- `themes.js` — 12 architectural themes (`ha-native`, `nordic-nursery`, `paper-journal`, `glass-aurora`, `midnight-studio`, `bento-pop`, `clinical-chart`, `botanical-linen`, `pastel-cloud`, `retro-terminal`, `warm-terracotta`, `tokyo-minimal`)
- `cards.js` — 4 card style presets (`bubble`, `mushroom`, `bento-pro`, `classic`), inline SVG icon set, 0–100% LMS percentile gauge bar, and SVG growth sparkline

---

## 4. Final Quality & Security Audit Findings (Priority Recommendations for Next Upgrade)

### Fixed in This Audit
- Removed 3 unused imports caught by `ruff` (`config_flow.py`, `llm_api.py`).
- Fixed photo-orphan edge case in `storage.py:async_add_activity` by validating `temperature_c` before writing the uploaded photo to disk.
- Verified: `pytest -q` (162 passed), `ruff check` (0 errors), `scripts/check_care_tuition.py --strict` (OK), all JSON valid, security grep (0 leaks), Node ES module load check (OK).

### High-Priority Security & Privacy Improvements
1. **Authenticated Photo Serving (Important for Public-Facing HA Instances)**:
   - Currently, uploaded baby photos are saved under `<config>/www/kr_baby_kit_media/<child_id>/` and served at `/local/kr_baby_kit_media/...`.
   - Home Assistant serves `/local/` **without authentication**. While filenames are random 16-char hex UUIDs, anyone with a leaked URL can access them without logging in.
   - **Recommended upgrade**: Move storage to `<config>/.storage/kr_baby_kit_media/<child_id>/` and serve via an authenticated `HomeAssistantView` (`/api/kr_baby_kit/media/{child_id}/{filename}`, `requires_auth = True`) or signed HA auth URLs (`hass.auth`).
2. **Admin Guard Consideration on Config-Entry Mutations**:
   - `ws_add_child`, `ws_update_child`, `ws_delete_child` require an authenticated HA user (`connection.user`), but do not currently enforce `@websocket_api.require_admin`. Decide whether non-admin household members should be allowed to delete child entries, or add `require_admin` on `delete_child`.

### High-Priority UX & Visual Design Upgrades (User's Main Feedback)
The user specifically wants a **truly polished, mom-friendly mobile + PC experience** (like top-tier native baby apps, with zero awkward whitespace on PC and genuinely cohesive card design):
1. **Preserve Unsaved Form State on Partial Re-Renders (`frontend/panel.js`)**:
   - Currently, `_render()` replaces `this.shadowRoot.innerHTML` completely. If a user types a note in `<textarea name="note">` and then attaches a photo or switches a filter, the typed note text is cleared.
   - **Fix**: Keep draft form state (`this._draftCare`) in component state or move to incremental DOM updates / LitElement (bundled or lightweight reactive helper).
2. **True Visual Polish & Editorial Hierarchy (Mobile & PC)**:
   - Consider splitting `panel.js` (~2,200 lines) into focused ES modules (`components/hero.js`, `components/care.js`, `components/growth.js`, `components/timeline.js`, `components/settings.js`).
   - Add a **proper interactive LMS Growth Curve Chart** (plotting WHO/KDCA 3rd, 15th, 50th, 85th, 97th percentile curves as shaded SVG bands with the child's actual measurement dots overlaid — moms LOVE seeing their baby's curve!).
   - Replace plain inline `<form>` for daily care with a **clean bottom-sheet / modal quick-logger** triggered by large visual icon buttons (Sleep, Feed, Diaper, Tummy, Temp, Photo) so the main dashboard stays ultra-clean and uncluttered!
   - Add **daily/weekly trend charts** for Sleep & Feeding (Baby Buddy's signature 24-hour sleep timeline bar + daily feeding ml bar chart).
3. **Expose Daily Care Totals as Native HA Sensors**:
   - Right now daily sleep, feeding count/ml, diaper counts, and last temperature live in `storage.py` + WebSocket only. Exposing them as real HA `sensor` entities (`today_sleep_minutes`, `today_feeding_ml`, `today_diaper_count`, `last_temperature`, `active_timer`) will unlock HA dashboards, mobile notifications, and Assist voice queries ("How much did the baby drink today?").
4. **Prevent Double Reload on `ws_update_child`**:
   - In `websocket_api.py:ws_update_child`, `hass.config_entries.async_update_entry(...)` is followed by `await hass.config_entries.async_reload(...)`. Verify on live HA 2026.x whether `add_update_listener` already triggers a reload on `data` change to avoid double reloads.

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
