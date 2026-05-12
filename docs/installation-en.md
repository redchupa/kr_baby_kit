# Installation Guide (English)

## 1. Prerequisites

- Home Assistant 2024.6 or later
- HACS installed
- Your child's birthdate and sex

## 2. Install via HACS

1. HACS → Integrations → top-right ⋮ → **Custom repositories**
2. URL: `https://github.com/redchupa/kr_baby_kit`
3. Category: **Integration**
4. **Add** → search for *Korean Baby Kit* → download
5. Restart Home Assistant

## 3. Register a child

1. **Settings → Devices & Services → Add integration**
2. Pick *kr_baby_kit*
3. Enter:
   - **Child name or alias** (e.g. `First-born`, `Baby A`)
   - **Birthdate**: YYYY-MM-DD
   - **Sex**: Male / Female
4. One device per child. Add the integration again for additional children.

## 4. Record measurements

### Recommended: dashboard number entities

Each child device exposes three `number` entities:

- `number.<child>_height` (cm)
- `number.<child>_weight` (kg)
- `number.<child>_head` (cm)

Changing the value records a measurement dated **today** and refreshes all
percentile sensors immediately. Updates on the same date are merged into one
record.

### Backfilling historical data

Use the `kr_baby_kit.record_measurement` service with an explicit `date`:

```yaml
service: kr_baby_kit.record_measurement
data:
  child_id: "ab12cd34ef56"   # optional when only one child is registered
  date: "2025-08-15"
  height: 75.4   # cm
  weight: 9.2    # kg
  head: 46.0     # cm (optional)
```

Sensors like `sensor.kr_baby_kit_<name>_height_percentile` refresh automatically.

## 5. Calendars

- `calendar.kr_baby_kit_<name>_immunization`
- `calendar.kr_baby_kit_<name>_checkup`

Each window is computed from the child's birthdate using the published KDCA NIP
schedule and the standard 7-stage infant checkup schedule.

## 5-1. Childcare tuition sensors (v0.4.0a alpha)

Three KRW-denominated sensors are auto-matched to the child's age class
(만 0~6세반):

- `sensor.<child>_표준보육료` (standard tuition)
- `sensor.<child>_보육료_정부지원금` (government subsidy)
- `sensor.<child>_보육료_본인부담금` (parent's share)

⚠️ The bundled `data/care_tuition_kr.json` ships with **placeholder zeros**
(`data_year: 0`). Update it with the latest 보건복지부 표준보육료 고시
before deploying. While in placeholder mode the sensors return `Unknown`
(state `None`) and expose `is_placeholder: true` in their attributes.

You only need to edit:
- `_meta.data_year` → the year of the figures you paste in (e.g. `2025`)
- each `tiers[].standard_tuition` / `government_subsidy` / `parent_share`

## 6. Voice assistant (Assist)

A child-specific LLM API is registered automatically. To enable it:

1. Settings → Voice assistants → edit your active pipeline
2. Under **LLM API**, tick `kr_baby_kit · <child name>`
3. Try: "When is the next vaccine?" / "What's the latest height percentile?" / "How much is this month's tuition?"

## ⚠️ Notes

- This information is **for reference only** and does not replace medical advice.
- Measurements are stored in HA Storage and are never transmitted off-device.
- The integration runs entirely offline — all reference data is bundled.
