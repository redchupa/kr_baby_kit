# Smart Nursery Automation Cookbook

[English](smart-nursery-automations.en.md) | [한국어](smart-nursery-automations.md)

Unlike standalone mobile baby-tracking apps, **Baby Kit (`kr_baby_kit`)** runs natively inside Home Assistant — connecting directly with presence sensors, crib cameras, Zigbee/Matter wireless buttons, smart speakers (TTS), and Assist voice queries.

All recipes below are also built into the **Smart Nursery Automations** card inside the `Baby Kit` sidebar panel with your child's `child_id` pre-filled for one-click YAML copy.

---

## 1. 5-Minute Follow-Me Baby Cam When Washing Dishes or Showering

### Why parents love this
Running water in the kitchen sink or shower makes it hard to hear a baby crying. When crib motion or sound triggers **while the nursery occupancy counter is `0`** (no adult is inside the room), Home Assistant checks which room you are currently in and streams the crib camera + audio there for 5 minutes before dimming automatically.

```yaml
alias: "Nursery Safety — 5-Min Follow-Me Baby Cam When Room Counter Is 0"
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.nursery_cam_motion
      - binary_sensor.nursery_cry_detected
    from: "off"
    to: "on"
conditions:
  # Run only when no adult is currently inside the nursery
  - condition: numeric_state
    entity_id: number.nursery_people_count
    below: 1
actions:
  - parallel:
      # 1) Kitchen occupied: announce and cast crib stream for 5 minutes
      - if:
          - condition: state
            entity_id: binary_sensor.kitchen_presence
            state: "on"
        then:
          - action: tts.speak
            target:
              entity_id: tts.home_assistant_cloud
            data:
              media_player_entity_id: media_player.kitchen_display
              message: "Motion detected in the crib. Opening the nursery camera."
          - action: camera.play_stream
            target:
              entity_id: camera.nursery_cam
            data:
              media_player: media_player.kitchen_display
          - delay: "00:05:00"
          - action: media_player.turn_off
            target:
              entity_id: media_player.kitchen_display

      # 2) Bathroom occupied: boost speaker volume and announce
      - if:
          - condition: state
            entity_id: binary_sensor.bathroom_presence
            state: "on"
        then:
          - action: media_player.volume_set
            target:
              entity_id: media_player.bathroom_speaker
            data:
              volume_level: 0.55
          - action: tts.speak
            target:
              entity_id: tts.home_assistant_cloud
            data:
              media_player_entity_id: media_player.bathroom_speaker
              message: "Motion or crying detected in the nursery."
mode: single
max_exceeded: silent
```

---

## 2. 5-Minute Motion-Hold Virtual Sensor for Automatic Sleep Tracking

### Why parents love this
Raw camera motion sensors turn off after a few seconds, creating noisy logs. Creating a template binary sensor with `delay_off: "00:05:00"` identifies when the baby has truly settled asleep, automatically starting and stopping the Baby Kit sleep timer so your 7-day sleep chart fills itself hands-free.

```yaml
# configuration.yaml
template:
  - binary_sensor:
      - name: "Nursery Crib Active Within 5m"
        unique_id: nursery_crib_active_within_5m
        device_class: moving
        state: "{{ is_state('binary_sensor.nursery_cam_motion', 'on') }}"
        delay_off: "00:05:00"
```

```yaml
# automations.yaml
alias: "Nursery Sleep — Auto Start/Stop Sleep Timer From 5-Min Motion Hold"
triggers:
  - trigger: state
    entity_id: binary_sensor.nursery_crib_active_within_5m
    to: "off"
    id: fell_asleep
  - trigger: state
    entity_id: binary_sensor.nursery_crib_active_within_5m
    to: "on"
    for: "00:02:00"
    id: woke_up
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: fell_asleep
        sequence:
          - action: kr_baby_kit.start_timer
            data:
              kind: sleep
      - conditions:
          - condition: trigger
            id: woke_up
        sequence:
          - action: kr_baby_kit.stop_timer
            data:
              kind: sleep
              save_log: true
```

---

## 3. Formula Station Wireless Button & "When Did Baby Last Eat?" Voice Briefing

### Why parents love this
Place a Zigbee or Matter mini button next to your formula station:
- **Single press**: Calls `kr_baby_kit.log_care` to log a 140 mL formula feeding instantly without touching your phone.
- **Double press**: Reads `sensor.kr_baby_kit_<child>_last_feeding_at` and speaks how long ago the baby last ate.
- **Assist voice**: Ask *"When did the baby last eat?"* and Baby Kit's built-in LLM tool answers directly.

```yaml
alias: "Formula Station — Single Press to Log, Double Press for Voice Briefing"
triggers:
  - trigger: state
    entity_id: event.formula_station_button
    attribute: event_type
    to: "single"
    id: log_formula
  - trigger: state
    entity_id: event.formula_station_button
    attribute: event_type
    to: "double"
    id: check_formula
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: log_formula
        sequence:
          - action: kr_baby_kit.log_care
            data:
              kind: feeding
              method: formula
              amount_ml: 140
          - action: tts.speak
            target:
              entity_id: tts.home_assistant_cloud
            data:
              media_player_entity_id: media_player.living_room_speaker
              message: "Logged 140 milliliters of formula feeding."

      - conditions:
          - condition: trigger
            id: check_formula
        sequence:
          - action: tts.speak
            target:
              entity_id: tts.home_assistant_cloud
            data:
              media_player_entity_id: media_player.living_room_speaker
              message: >-
                {% set s = states('sensor.kr_baby_kit_child_last_feeding_at') %}
                {% if s in ('unknown', 'unavailable', '') %}
                  No feedings have been logged yet.
                {% else %}
                  {% set dt = as_local(as_datetime(s)) %}
                  {% set diff = (now() - dt).total_seconds() | int %}
                  {% set h = diff // 3600 %}
                  {% set m = (diff % 3600) // 60 %}
                  Last feeding was {{ h ~ ' hours and ' if h > 0 else '' }}{{ m }} minutes ago,
                  at {{ dt.strftime('%I:%M %p') }}.
                {% endif %}
```

---

## 4. 2 AM Dim Nursing Light & Fever Recheck Alert

- **Night Nursing Light**: When `feeding` appears in `sensor.<child>_active_timers`'s `running_kinds` attribute between `22:00` and `06:30`, turn on the nursery lamp at `8%` warm `2200K`.
- **Fever 2-Hour Recheck**: When `sensor.<child>_last_temperature` exceeds `37.7°C`, send an immediate family push alert and a 2-hour follow-up reminder.
