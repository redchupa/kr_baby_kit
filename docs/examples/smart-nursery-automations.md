# 스마트 육아 자동화 가이드 (Smart Nursery Automation Cookbook)

스마트폰 단독 육아 기록 앱과 달리 **Baby Kit (`kr_baby_kit`)** 은 Home Assistant 내부에서 재실 센서, 카메라, 지그비(Zigbee)/Matter 무선 스위치, 스마트 스피커(TTS), 음성 비서(Assist)와 직접 연동됩니다.

아래 레시피들은 실제 가정에서 검증된 육아 자동화 패턴을 누구나 바로 복사해 쓸 수 있도록 정리한 예시입니다. `Baby Kit` 사이드바 화면의 **스마트 육아 자동화 가이드** 카드에서도 내 아이의 `child_id`가 자동 채워진 YAML을 원클릭으로 복사할 수 있습니다.

---

## 1. 설거지·샤워 중 안심 베이비캠 5분 자동 재생 (Follow-Me Baby Cam)

### 왜 유용한가요?
설거지 물소리가 나거나 샤워실에서 씻고 있을 때는 아기 울음소리가 들리지 않아 계속 휴대폰을 확인하게 됩니다.
**아기방 재실 카운터가 `0`(방에 어른이 없음)** 일 때 아기 침대 모션이나 울음 소리가 감지되면, **현재 사람이 감지된 공간(주방 태블릿, 욕실 스피커/방수 공기계 등)에서만** 카메라 영상과 소리를 5분간 자동 재생한 뒤 꺼지도록 구성하면 마음이 훨씬 편안해집니다.

```yaml
alias: "육아 안심 — 방에 어른 없을 때 현재 위치로 베이비캠 5분 재생"
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.nursery_cam_motion
      - binary_sensor.nursery_cry_detected
    from: "off"
    to: "on"
conditions:
  - condition: numeric_state
    entity_id: number.nursery_people_count
    below: 1
actions:
  - parallel:
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
              message: "아기 침대에서 움직임이 감지되어 화면을 연결합니다."
          - action: camera.play_stream
            target:
              entity_id: camera.nursery_cam
            data:
              media_player: media_player.kitchen_display
          - delay: "00:05:00"
          - action: media_player.turn_off
            target:
              entity_id: media_player.kitchen_display

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
              message: "아기방에서 움직임 또는 울음 소리가 감지되었습니다."
mode: single
max_exceeded: silent
```

---

## 2. 5분 무움직임 가상 센서로 실제 입면·기상 시간 자동 기록

### 왜 유용한가요?
카메라 모션 센서는 움직임이 멈추면 몇 초 만에 `off`로 바뀌기 때문에 그대로 쓰면 아이가 뒤척일 때마다 수면 기록이 쪼개집니다.
`delay_off: "00:05:00"` 옵션을 준 **5분 이내 움직임 유지 가상 센서**를 만들면, 5분 연속 움직임이 없을 때 진짜 잠든 것으로 판단해 `kr_baby_kit.start_timer`(`sleep`)를 켜고 기상 시 `kr_baby_kit.stop_timer`로 수면 통계와 7일 추이 차트를 완전 자동으로 채울 수 있습니다.

```yaml
# configuration.yaml
template:
  - binary_sensor:
      - name: "아기 침대 5분 내 움직임"
        unique_id: nursery_crib_active_within_5m
        device_class: moving
        state: "{{ is_state('binary_sensor.nursery_cam_motion', 'on') }}"
        delay_off: "00:05:00"
```

```yaml
# automations.yaml
alias: "육아 수면 — 5분 무움직임 시 Baby Kit 수면 타이머 자동 기록"
triggers:
  - trigger: state
    entity_id: binary_sensor.agi_cimdae_5bun_nae_umjigim
    to: "off"
    id: fell_asleep
  - trigger: state
    entity_id: binary_sensor.agi_cimdae_5bun_nae_umjigim
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

## 3. 분유통 옆 무선 버튼 원클릭 기록 & "분유 언제 먹었어?" 음성 안내

### 왜 유용한가요?
새벽이나 아이를 안고 있을 때 스마트폰 앱을 열어 수유 시간을 입력하기는 번거롭습니다.
분유 포트 옆에 지그비/Matter 무선 미니 스위치를 붙여 두면:
- **한 번 클릭 (`single`)**: `kr_baby_kit.log_care` 서비스로 분유 수유 시각과 용량이 즉시 기록됩니다.
- **두 번 클릭 (`double`) 또는 음성 비서 질문 ("분유 언제 먹었어?")**: `돌봄_마지막_수유_시각` (`last_feeding_at`) 센서를 읽어 경과 시간과 마지막 수유 시각을 스피커로 알려줍니다.
- **Assist 자연어 연동**: 별도 스크립트 없이도 Home Assistant Assist에게 *"오늘 수유 얼마나 했어?"*, *"분유 언제 먹었어?"* 라고 물으면 내장 LLM 도구가 즉시 답변합니다.

```yaml
alias: "육아 맘마존 — 무선 버튼 분유 기록(1클릭) · 마지막 수유 시간 방송(2클릭)"
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
              message: "분유 140밀리 수유 시간을 기록했습니다."

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
                  아직 기록된 수유 내역이 없습니다.
                {% else %}
                  {% set dt = as_local(as_datetime(s)) %}
                  {% set diff = (now() - dt).total_seconds() | int %}
                  {% set h = diff // 3600 %}
                  {% set m = (diff % 3600) // 60 %}
                  {% set ampm = '오전' if dt.hour < 12 else '오후' %}
                  {% set hr12 = dt.hour if dt.hour <= 12 else dt.hour - 12 %}
                  마지막 수유는 {{ h ~ '시간 ' if h > 0 else '' }}{{ m }}분 전,
                  {{ ampm }} {{ hr12 }}시 {{ dt.minute }}분이었습니다.
                {% endif %}
```

---

## 4. 새벽 수유 눈부심 방지 무드등 & 발열(37.8°C+) 재측정 알림

- **심야 수유등**: `sensor.<자녀>_active_timers`의 `running_kinds` 속성에 `feeding`이 포함될 때(22:00-06:30) 아기방 무드등을 밝기 `8%`, 색온도 `2200K`로 점등해 아기와 부모의 잠이 깨지 않도록 보호합니다.
- **발열 2시간 체크**: `sensor.<자녀>_last_temperature`가 `37.8` 이상으로 올라가면 부부 스마트폰으로 즉시 알림을 보내고 `delay: "02:00:00"` 후 체온 재측정 리마인더를 발송합니다.
