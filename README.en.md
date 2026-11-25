# Korean Baby Kit

[English](README.en.md) | [한국어](README.md)

[![Validate](https://github.com/redchupa/kr_baby_kit/actions/workflows/hassfest.yml/badge.svg)](https://github.com/redchupa/kr_baby_kit/actions/workflows/hassfest.yml)
[![Tests](https://github.com/redchupa/kr_baby_kit/actions/workflows/test.yml/badge.svg)](https://github.com/redchupa/kr_baby_kit/actions/workflows/test.yml)
[![HACS](https://raw.githubusercontent.com/redchupa/kr_baby_kit/main/images/hacs-custom-badge.png)](https://github.com/hacs/integration)
[![Release](https://img.shields.io/github/v/release/redchupa/kr_baby_kit?include_prereleases&label=release)](https://github.com/redchupa/kr_baby_kit/releases)

A Home Assistant (HACS) integration for tracking a child's growth percentiles, immunization schedules, and pediatric/dental checkups locally.

It supports two regional profiles:

- **International (`global`)**: WHO Child Growth Standards (0-5 years, 2006) & WHO Growth Reference (5-19 years, 2007), WHO routine immunization reference schedule, and general well-child / dental checkup milestones.
- **South Korea (`kr`)**: KDCA 2017 growth charts, KDCA National Immunization Program (NIP), NHIS 8-stage infant health checkups & 4-stage oral checkups, and Ministry of Education childcare tuition figures.

All reference tables are bundled with the integration. No external API keys or cloud services are required.

## Features

- **LMS growth percentiles**: Enter height, weight, and head circumference to compute percentiles and Z-scores against the child's age at the time of measurement. Height and weight are reported as top-percent rank sensors; bi-directional indicators (head circumference, BMI, weight-for-length) are exposed as `binary_sensor` alerts that turn on only outside the 5th-95th statistical percentile band.
- **Regional profile selection**: Choose between `International (WHO Growth Standards)` and `South Korea (KDCA · NIP · Childcare Tuition)` when registering a child. The default matches your Home Assistant language setting, and you can switch profiles later in the integration options without losing stored measurements.
- **Vaccination, well-child, and dental schedules**: Projected from the child's birthdate into calendars and sensors. Open windows expose a deadline sensor; upcoming windows expose a next-window start sensor.
- **Completion tracking**: Mark completed doses or visits with `kr_baby_kit.mark_event_done` to remove them from upcoming sensors and monthly reminders. Marking is optional; windows that have passed without a mark simply show as passed without triggering warnings.
- **Home Assistant localization & timezone**: Entity names, states, summaries, and calendar events automatically follow your Home Assistant language (`en` / `ko`) and configured local time zone.
- **Assist (LLM API)**: Registers a per-child LLM API for Home Assistant Assist so you can ask about upcoming vaccines, checkups, or latest growth percentiles in natural language.
- **South Korea childcare tuition (KR profile only)**: Exposes monthly standard tuition, government subsidy, and parent share in KRW based on birth-year age class. Not created when using the International profile.

## Installation

Requires Home Assistant 2024.11 or later and HACS.

### 1. Add custom repository in HACS

1. Open **HACS** → **Integrations** → top-right menu (⋮) → **Custom repositories**.
2. Add `https://github.com/redchupa/kr_baby_kit` with category **Integration**.
3. Search for **Korean Baby Kit**, download it, and restart Home Assistant.

### 2. Register a child

1. Go to **Settings → Devices & Services → Add integration** and select `kr_baby_kit`.
2. Fill in the child details:

| Field | Example | Notes |
|---|---|---|
| Child name or alias | `Baby A`, `First-born` | Display name on dashboards |
| Birthdate | `2023-05-14` | `YYYY-MM-DD` |
| Sex | Male / Female | Used for sex-specific LMS tables |
| Region / Standard | International (WHO) / South Korea | Selects growth chart and schedule tables |

Add the integration again for additional children. You can edit name, birthdate, sex, or regional standard later under **Settings → Devices & Services → Korean Baby Kit → Configure** while preserving measurement history and completion marks.

## Entities

Each registered child gets one device with the following entities (localized to English when Home Assistant is set to English):

### Measurement inputs (`number`)

- **Record height (today)** (`cm`)
- **Record weight (today)** (`kg`)
- **Record head circumference (today)** (`cm`)

Updating a number entity stores a reading for today (in your Home Assistant local time zone) and refreshes all percentiles immediately. To backfill past measurements, call `kr_baby_kit.record_measurement` with an explicit `date`.

### Growth metrics (`sensor`, `binary_sensor`)

- **Height rank among peers (top %)**, **Weight rank among peers (top %)**: Smaller numbers mean taller/heavier. Raw LMS values (`statistical_percentile`, `z_score`, `summary_en`, `summary_ko`) are available in attributes.
- **Head circumference concern**, **BMI concern**, **Weight-for-length concern**: `binary_sensor` (`problem` device class) that turns on when the statistical percentile falls below 5% or above 95%. Under 24 months, BMI percentile is not defined and the sensor directs you to weight-for-length instead.
- **BMI** (`kg/m²`), **Age (months)** (`mo`)

### Immunization, health checkup, and dental checkup (`sensor`, `binary_sensor`, `calendar`)

Each of the three categories provides:

| Entity | Purpose |
|---|---|
| **Open ... window deadline** | End date of the currently open window (unknown when none is open). `open_events` lists every open item with its deadline and remaining days. |
| **Next ... window start** | Start date of the next future window (`days_until_start` included). |
| **... this month** | Turns on when a non-completed window overlaps the current calendar month. |
| **... schedule** (`calendar`) | Full schedule as all-day events, including past and completed entries. |

### Childcare tuition (`sensor`, KRW — South Korea profile only)

- **Monthly standard childcare tuition**, **Monthly government subsidy**, **Monthly parent share**

## Services

| Service | Description |
|---|---|
| `kr_baby_kit.record_measurement` | Record height, weight, and/or head circumference (`date` defaults to today) |
| `kr_baby_kit.delete_measurement` | Delete a full date record or specific fields |
| `kr_baby_kit.get_measurements` | Return stored measurement history (response action) |
| `kr_baby_kit.mark_event_done` | Mark one or more `event_id`s completed (comma-separated) |
| `kr_baby_kit.unmark_event_done` | Remove completion marks |
| `kr_baby_kit.get_schedule` | Return the full schedule with `event_id` and status (`done`, `open`, `upcoming`, `past`) |

Example `event_id` values: `DTaP_4`, `IIV_2026`, `checkup_3`, `oral_checkup_1`.

## Automation Examples

```yaml
# Notify 14 days before the next vaccine window opens
- alias: Vaccine reminder D-14
  trigger:
    - platform: template
      value_template: >-
        {% set t = states('sensor.kr_baby_kit_<child>_next_vaccine') %}
        {{ t not in ('unknown','unavailable','') and
           (as_datetime(t) - now()).days == 14 }}
  action:
    - service: notify.mobile_app
      data:
        title: "Upcoming immunization"
        message: "{{ state_attr('sensor.kr_baby_kit_<child>_next_vaccine', 'name_en') }} starts in 14 days."

# Notify if BMI percentile falls outside the 5th-95th band
- alias: BMI concern notification
  trigger:
    - platform: state
      entity_id: binary_sensor.kr_baby_kit_<child>_bmi_concern
      to: "on"
  action:
    - service: notify.mobile_app
      data:
        title: "Growth reference alert"
        message: >-
          {{ state_attr('binary_sensor.kr_baby_kit_<child>_bmi_concern', 'summary_en') }}
          Consider reviewing this at your next pediatric visit.
```

```yaml
# Mark all currently open vaccines done in one call
- service: kr_baby_kit.mark_event_done
  data:
    event_id: "{{ state_attr('sensor.kr_baby_kit_<child>_next_vaccine', 'open_event_ids') | join(',') }}"
```

More examples are available in [docs/examples/automation-examples.yaml](docs/examples/automation-examples.yaml).

## Data Sources

### International profile (`global`)

| Dataset | Source |
|---|---|
| Child Growth Standards (0-5y) & Growth Reference (5-19y) | [WHO Child Growth Standards (2006)](https://www.who.int/tools/child-growth-standards) · [WHO Growth Reference 5-19y (2007)](https://www.who.int/tools/growth-reference-data-for-5to19-years) |
| Routine Immunization Reference | [WHO Recommendations for Routine Immunization](https://www.who.int/teams/immunization-vaccines-and-biologicals/policies/who-recommendations-for-routine-immunization---summary-tables) |
| Well-child & Dental Milestones | General pediatric visit milestones (confirm exact national schedules with your local health provider) |

### South Korea profile (`kr`)

| Dataset | Source | License |
|---|---|---|
| Pediatric Growth Charts (LMS) | [KDCA 2017 Growth Charts](https://www.kdca.go.kr/kdca/5458/subview.do) | KOGL Type 1 |
| National Immunization Program (NIP) | [KDCA Immunization Helper](https://nip.kdca.go.kr/irhp/goMainInfo.do) | KOGL Type 1 |
| Infant Health (8) & Oral (4) Checkups | [NHIS](https://www.nhis.or.kr/nhis/healthin/wbhabb02100m01.do) · [MOHW](https://www.mohw.go.kr/board.es?mid=a10503010100&bid=0027&act=view&list_no=362391) | KOGL Type 1 |
| Childcare Tuition Rates (2026) | [Ministry of Education 2026 Guidelines](https://www.daejeon.go.kr/data/drh/sub05/2026_data_02.pdf) | KOGL Type 1 |

See [docs/data-sources.md](docs/data-sources.md) for full references and licensing details.

## Privacy & Storage

- Measurements and completion records are stored locally as plain JSON inside Home Assistant's `.storage/` directory. Nothing is sent to external servers.
- Removing a child entry deletes its stored measurements and completion marks.
- Measurement inputs are validated against plausible ranges at both the service schema and storage layers.

## Medical Disclaimer

All growth percentiles, immunization schedules, and checkup milestones provided by this integration are for reference only and do not replace professional medical diagnosis or pediatric care.

## License

[MIT License](LICENSE). Public-sector data attributions and notices are listed in [NOTICE](NOTICE).

## Issues & Support

Please open an issue at [GitHub Issues](https://github.com/redchupa/kr_baby_kit/issues) for bug reports or suggestions. Pull requests for translations and documentation are welcome.

If you find this integration useful, you can support maintenance via PayPal:

<table>
  <tr>
    <td align="center">
      <b>PayPal</b><br/>
      <img src="https://raw.githubusercontent.com/redchupa/kr_baby_kit/main/images/paypal-donation.png" alt="PayPal QR" width="180"/>
    </td>
  </tr>
</table>
