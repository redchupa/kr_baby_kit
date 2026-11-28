/* Layout presets (8 modes) & Smart Nursery Automation Recipes for Baby Kit */

function esc(val) {
  return String(val ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export const LAYOUT_MODES = [
  {
    id: "bento",
    nameKo: "2열 밸런스 벤토",
    nameEn: "2-Col Bento",
    descKo: "좌·우 독립 컬럼이 카드 높이만큼 빈틈없이 채워지는 균형 배치",
    descEn: "Balanced 2-column masonry with zero wasted card space",
  },
  {
    id: "bento-3",
    nameKo: "3열 와이드 스튜디오",
    nameEn: "3-Col Studio",
    descKo: "돌봄·성장·일정을 3열 와이드 화면에 한눈에 펼치는 관제형 배치",
    descEn: "Wide 3-column studio showing care, growth & schedules together",
  },
  {
    id: "quad-dense",
    nameKo: "4열 초밀집 매트릭스",
    nameEn: "4-Col Dense Matrix",
    descKo: "PC와 모바일 모두 4열 초소형 타일로 압축해 스크롤을 최소화",
    descEn: "Ultra-dense 4-column micro-tiles on both desktop & mobile",
  },
  {
    id: "cockpit",
    nameKo: "상단 요약 콕핏",
    nameEn: "Top KPI Cockpit",
    descKo: "전폭 돌봄 상황판 아래 주 영역(좌)과 보조 레일(우) 비대칭 배치",
    descEn: "Full-width care command bar over an asymmetric 60/40 split",
  },
  {
    id: "magazine",
    nameKo: "매거진 스플릿",
    nameEn: "Magazine Split",
    descKo: "왼쪽 고정 돌봄 도크 + 오른쪽 넓은 성장곡선·사진 일기 캔버스",
    descEn: "Sticky left care dock paired with a wide growth & diary canvas",
  },
  {
    id: "app-tabs",
    nameKo: "탭 포커스 앱",
    nameEn: "Tabbed App Deck",
    descKo: "돌봄·성장·일기·일정·자동화를 상단 탭으로 깔끔하게 전환",
    descEn: "Focused native-app tab deck switching one category at a time",
  },
  {
    id: "compact",
    nameKo: "컴팩트 보드",
    nameEn: "Compact Board",
    descKo: "패딩과 간격을 조밀하게 줄인 월패드·소형 태블릿 최적화 모드",
    descEn: "Tight spacing and slim rows tailored for wall tablets",
  },
  {
    id: "single",
    nameKo: "1열 타임라인",
    nameEn: "Single Feed",
    descKo: "위에서 아래로 차분하게 읽는 클래식 1열 카드 스트림",
    descEn: "Calm centered single-column reading stream",
  },
];

export const AUTOMATION_RECIPES = [
  {
    id: "follow_me_babycam",
    tagKo: "안심 모니터링",
    tagEn: "Peace of Mind",
    titleKo: "설거지·샤워 중 안심 베이비캠 5분 자동 재생 (Follow-Me Cam)",
    titleEn: "Follow-Me Baby Cam When Washing Dishes or Showering",
    whyKo:
      "아기방 재실 카운터가 0명(방에 어른 없음)일 때 침대 모션·울음이 감지되면, 현재 사람이 있는 주방이나 욕실 화면/스피커로 아기 카메라와 소리를 5분간 자동 재생합니다. 물소리 때문에 아기 울음을 못 들을까 봐 불안해하지 않아도 됩니다.",
    whyEn:
      "When crib motion or crying triggers while the nursery occupancy counter is 0, automatically streams the nursery camera + audio for 5 minutes to whichever room (kitchen or bathroom) currently detects an adult.",
    devicesKo: ["카메라 모션/소음 센서", "방 재실 카운터(또는 재실 센서)", "주방·욕실 태블릿/네스트 허브"],
    devicesEn: ["Crib motion/sound sensor", "Room presence counter", "Kitchen/bathroom display or speaker"],
    yaml: (cid, ko = true) =>
      ko
        ? `alias: "육아 안심 — 방에 어른 없을 때 현재 위치로 베이비캠 5분 재생"
description: "설거지(주방)·샤워(욕실) 중에도 아기 움직임/울음을 놓치지 않도록 현재 사람이 있는 곳에서 5분간 재생"
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.nursery_cam_motion
      - binary_sensor.nursery_cry_detected
    from: "off"
    to: "on"
conditions:
  # 아기방에 어른이 함께 있지 않을 때만 실행 (재실 카운터 0명)
  - condition: numeric_state
    entity_id: number.nursery_people_count
    below: 1
actions:
  - parallel:
      # 1) 주방(싱크대/식탁)에 사람이 있으면 주방 화면·스피커로 5분 재생
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

      # 2) 욕실(샤워 중)에 사람이 있으면 볼륨을 높여 욕실 스피커/태블릿으로 5분 재생
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
max_exceeded: silent`
        : `alias: "Nursery Safety — 5-Min Follow-Me Baby Cam When Room Counter Is 0"
description: "Streams the crib camera and audio to the occupied room (kitchen or bathroom) for 5 minutes so you never miss crying over running water"
triggers:
  - trigger: state
    entity_id:
      - binary_sensor.nursery_cam_motion
      - binary_sensor.nursery_cry_detected
    from: "off"
    to: "on"
conditions:
  # Run only when no adult is currently inside the nursery (occupancy counter == 0)
  - condition: numeric_state
    entity_id: number.nursery_people_count
    below: 1
actions:
  - parallel:
      # 1) If someone is in the kitchen, cast the crib camera to the kitchen display for 5 minutes
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

      # 2) If someone is in the bathroom (showering), raise volume and announce on the bathroom speaker
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
max_exceeded: silent`,
  },
  {
    id: "motion_hold_sleep",
    tagKo: "수면 자동 판정",
    tagEn: "Auto Sleep",
    titleKo: "5분 무움직임 가상 센서로 실제 잠든 시각 자동 기록",
    titleEn: "5-Minute Motion-Hold Virtual Sensor for Auto Sleep Logging",
    whyKo:
      "일반 모션 센서는 몇 초 만에 꺼져서 수면 판정이 부정확합니다. '최근 5분 이내 움직임 여부' 가상 센서(delay_off: 5분)를 만들어 두면, 5분 연속 움직임이 멈춘 시점을 실제 입면으로 판단해 Baby Kit 수면 타이머를 자동으로 켜고 기상 시 자동 저장합니다.",
    whyEn:
      "Raw motion sensors flicker every few seconds. A 5-minute delay_off template sensor cleanly detects when the baby has truly settled asleep and automatically starts/stops the Baby Kit sleep timer.",
    devicesKo: ["침대 카메라 모션 센서", "HA Template 가상 센서", "Baby Kit 수면 타이머"],
    devicesEn: ["Crib motion sensor", "Template binary_sensor", "Baby Kit sleep timer"],
    yaml: (cid, ko = true) =>
      ko
        ? `# [1단계] configuration.yaml — 최근 5분 이내 움직임 유지 가상 센서
template:
  - binary_sensor:
      - name: "아기 침대 5분 내 움직임"
        unique_id: nursery_crib_active_within_5m
        device_class: moving
        state: "{{ is_state('binary_sensor.nursery_cam_motion', 'on') }}"
        delay_off: "00:05:00"

# [2단계] 자동화 — 5분간 움직임이 없으면 입면 타이머 시작, 깨어나면 수면 기록 저장
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
              child_id: "${cid}"
              kind: sleep
      - conditions:
          - condition: trigger
            id: woke_up
        sequence:
          - action: kr_baby_kit.stop_timer
            data:
              child_id: "${cid}"
              kind: sleep
              save_log: true`
        : `# [Step 1] configuration.yaml — Virtual sensor that stays ON for 5 minutes after crib motion
template:
  - binary_sensor:
      - name: "Nursery Crib Active Within 5m"
        unique_id: nursery_crib_active_within_5m
        device_class: moving
        state: "{{ is_state('binary_sensor.nursery_cam_motion', 'on') }}"
        delay_off: "00:05:00"

# [Step 2] Automation — Start Baby Kit sleep timer after 5 min stillness; stop & save on wake
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
              child_id: "${cid}"
              kind: sleep
      - conditions:
          - condition: trigger
            id: woke_up
        sequence:
          - action: kr_baby_kit.stop_timer
            data:
              child_id: "${cid}"
              kind: sleep
              save_log: true`,
  },
  {
    id: "formula_button_tts",
    tagKo: "맘마존 무선 버튼 + 음성",
    tagEn: "Wireless Button & Voice",
    titleKo: "분유통 옆 무선 버튼 원클릭 기록 & '분유 언제 먹었어?' 음성 안내",
    titleEn: "Formula Station Wireless Button & 'When Did Baby Last Eat?' TTS",
    whyKo:
      "분유 포트 옆 무선 버튼을 한 번 누르면 휴대폰을 열지 않아도 분유 수유가 즉시 기록됩니다. 두 번 누르거나 음성 비서(Assist)에게 '분유 언제 먹었어?'라고 물어보면 마지막 수유 시각과 경과 시간을 자연스러운 음성으로 알려줍니다.",
    whyEn:
      "Single-press a Zigbee/Matter button next to the formula kettle to log a bottle hands-free. Double-press (or ask Assist 'When did the baby last eat?') to hear how many hours and minutes ago the last feeding was.",
    devicesKo: ["지그비/Matter 무선 미니 스위치", "거실·주방 스마트 스피커", "Assist 음성 비서"],
    devicesEn: ["Zigbee/Matter wireless button", "Smart speaker (TTS)", "HA Assist voice"],
    yaml: (cid, ko = true) =>
      ko
        ? `alias: "육아 맘마존 — 무선 버튼 분유 기록(1클릭) · 마지막 수유 시간 방송(2클릭)"
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
      # 1클릭: 분유 140mL 즉시 기록 + 음성 확인
      - conditions:
          - condition: trigger
            id: log_formula
        sequence:
          - action: kr_baby_kit.log_care
            data:
              child_id: "${cid}"
              kind: feeding
              method: formula
              amount_ml: 140
          - action: tts.speak
            target:
              entity_id: tts.home_assistant_cloud
            data:
              media_player_entity_id: media_player.living_room_speaker
              message: "분유 140밀리 수유 시간을 기록했습니다."

      # 2클릭: 마지막 수유로부터 경과 시간 + 시각 음성 브리핑
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
                {% endif %}`
        : `alias: "Formula Station — Single Press to Log, Double Press for Voice Briefing"
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
      # Single press: log 140 mL formula feeding & confirm via speaker
      - conditions:
          - condition: trigger
            id: log_formula
        sequence:
          - action: kr_baby_kit.log_care
            data:
              child_id: "${cid}"
              kind: feeding
              method: formula
              amount_ml: 140
          - action: tts.speak
            target:
              entity_id: tts.home_assistant_cloud
            data:
              media_player_entity_id: media_player.living_room_speaker
              message: "Logged 140 milliliters of formula feeding."

      # Double press: announce elapsed time and exact time of last feeding
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
                {% endif %}`,
  },
  {
    id: "night_feeding_dim",
    tagKo: "새벽 수유 케어",
    tagEn: "Night Care",
    titleKo: "새벽 수유 시 눈부심 없는 8% 전구색 수유등 자동 점등",
    titleEn: "2 AM Night-Feeding Soft 8% Warm Light",
    whyKo:
      "새벽에 밝은 형광등을 켜면 아기와 부모 모두 잠이 완전히 깨버립니다. 심야 시간대에 수유 타이머가 시작되면 수유 무드등만 8% 밝기(2200K)로 은은하게 켜고 종료 후 서서히 소등합니다.",
    whyEn:
      "Bright overhead lights at 2 AM wake both baby and parent. Automatically turns on a warm 2200K nursery light at 8% brightness whenever a night feeding timer starts.",
    devicesKo: ["밝기·색온도 조절 무드등", "Baby Kit 실행 중 타이머 센서"],
    devicesEn: ["Dimmable warm nursery light", "Baby Kit active timers sensor"],
    yaml: (cid, ko = true) =>
      ko
        ? `alias: "육아 새벽케어 — 심야 수유 타이머 시작 시 눈부심 방지 수유등"
triggers:
  - trigger: state
    entity_id: sensor.kr_baby_kit_child_active_timers
conditions:
  - condition: time
    after: "22:00:00"
    before: "06:30:00"
  - condition: template
    value_template: >-
      {{ 'feeding' in (state_attr('sensor.kr_baby_kit_child_active_timers', 'running_kinds') or []) }}
actions:
  - action: light.turn_on
    target:
      entity_id: light.nursery_mood_lamp
    data:
      brightness_pct: 8
      color_temp_kelvin: 2200`
        : `alias: "Night Care — Dim 8% Warm Nursing Light When Feeding Timer Starts"
triggers:
  - trigger: state
    entity_id: sensor.kr_baby_kit_child_active_timers
conditions:
  - condition: time
    after: "22:00:00"
    before: "06:30:00"
  - condition: template
    value_template: >-
      {{ 'feeding' in (state_attr('sensor.kr_baby_kit_child_active_timers', 'running_kinds') or []) }}
actions:
  - action: light.turn_on
    target:
      entity_id: light.nursery_mood_lamp
    data:
      brightness_pct: 8
      color_temp_kelvin: 2200`,
  },
  {
    id: "fever_recheck_guard",
    tagKo: "발열 집중 케어",
    tagEn: "Fever Guard",
    titleKo: "37.8°C 이상 발열 기록 시 부부 즉시 알림 & 2시간 뒤 재측정 리마인더",
    titleEn: "Fever Alert (37.8°C+) & 2-Hour Recheck Reminder",
    whyKo:
      "아이에게 열이 나기 시작하면 당황해서 해열제 복용 시간과 재측정 시점을 놓치기 쉽습니다. 37.8°C 이상 기록 시 가족에게 즉시 알리고 2시간 뒤 체온 재측정 알림을 보내줍니다.",
    whyEn:
      "When a temperature of 37.8°C or higher is logged in Baby Kit, notifies family phones immediately and schedules a 2-hour follow-up temperature check reminder.",
    devicesKo: ["Baby Kit 최근 체온 센서", "스마트폰 HA 앱 알림"],
    devicesEn: ["Baby Kit last temperature sensor", "HA Companion App notifications"],
    yaml: (cid, ko = true) =>
      ko
        ? `alias: "육아 건강 — 37.8°C 이상 발열 기록 시 알림 및 2시간 뒤 재측정 안내"
triggers:
  - trigger: numeric_state
    entity_id: sensor.kr_baby_kit_child_last_temperature
    above: 37.7
actions:
  - action: notify.notify
    data:
      title: "아이 발열 감지 알림"
      message: "현재 기록된 체온은 {{ states('sensor.kr_baby_kit_child_last_temperature') }}°C 입니다. 수분 보충과 해열제 복용 간격을 확인하세요."
  - delay: "02:00:00"
  - action: notify.notify
    data:
      title: "체온 재측정 시간"
      message: "발열 기록 후 2시간이 지났습니다. 체온을 다시 측정해 Baby Kit에 기록해 주세요."`
        : `alias: "Baby Health — Fever Alert (37.8°C+) & 2-Hour Recheck Reminder"
triggers:
  - trigger: numeric_state
    entity_id: sensor.kr_baby_kit_child_last_temperature
    above: 37.7
actions:
  - action: notify.notify
    data:
      title: "Baby Fever Alert"
      message: "Recorded temperature is {{ states('sensor.kr_baby_kit_child_last_temperature') }}°C. Offer fluids and monitor closely."
  - delay: "02:00:00"
  - action: notify.notify
    data:
      title: "Temperature Recheck Reminder"
      message: "It has been 2 hours since the fever log. Please recheck and log the temperature in Baby Kit."`,
  },
  {
    id: "vaccine_d7_family_alert",
    tagKo: "접종·검진 알림",
    tagEn: "Schedule Alert",
    titleKo: "예방접종·영유아검진 시작 D-7 및 마감 임박 알림",
    titleEn: "Immunization & Checkup D-7 Family Notification",
    whyKo:
      "바쁜 일상 속에서도 인플루엔자 절기 접종이나 영유아 건강·구강검진 시기를 놓치지 않도록 시작 7일 전 오전 9시에 예약 알림을 보내줍니다.",
    whyEn:
      "Sends a morning reminder 7 days before the next immunization or well-child checkup window opens so you can book a pediatric appointment on time.",
    devicesKo: ["Baby Kit 다음 예방접종·검진 센서", "스마트폰 HA 앱 알림"],
    devicesEn: ["Baby Kit next vaccine/checkup sensors", "HA Companion App"],
    yaml: (cid, ko = true) =>
      ko
        ? `alias: "육아 일정 — 다음 예방접종 시작 7일 전 병원 예약 알림"
triggers:
  - trigger: time
    at: "09:00:00"
conditions:
  - condition: template
    value_template: >-
      {{ state_attr('sensor.kr_baby_kit_child_next_vaccine', 'days_until_start') == 7 }}
actions:
  - action: notify.notify
    data:
      title: "예방접종 D-7 예약 알림"
      message: >-
        {{ state_attr('sensor.kr_baby_kit_child_next_vaccine', 'name_ko') }}
        접종 기간이 7일 뒤 시작됩니다. 소아청소년과 예약을 확인해 보세요.`
        : `alias: "Schedule Reminder — 7 Days Before Next Immunization Window"
triggers:
  - trigger: time
    at: "09:00:00"
conditions:
  - condition: template
    value_template: >-
      {{ state_attr('sensor.kr_baby_kit_child_next_vaccine', 'days_until_start') == 7 }}
actions:
  - action: notify.notify
    data:
      title: "Upcoming Immunization (D-7)"
      message: >-
        {{ state_attr('sensor.kr_baby_kit_child_next_vaccine', 'name_en') }}
        window opens in 7 days. Consider booking a pediatric appointment.`,
  },
];

export function renderAutomationsSection(child, opts = {}) {
  const ko = Boolean(opts.ko);
  const t = opts.t || null;
  const openId = opts.openRecipeId || null;
  const copiedId = opts.copiedId || null;
  const wideClass = opts.wideClass || "";
  const cid = child?.child_id || "your_child_id";

  const title = t?.autoTitle ?? (ko ? "스마트 육아 자동화 가이드" : "Smart Nursery Automations");
  const sub =
    t?.autoSub ??
    (ko
      ? "실전 Home Assistant 육아 레시피 — 우리 아이 ID가 자동 반영된 YAML을 복사해 바로 활용하세요."
      : "Battle-tested Home Assistant parenting recipes — copy ready-to-use YAML with your child_id pre-filled.");
  const viewBtn = t?.autoView ?? (ko ? "샘플 코드 보기" : "View YAML");
  const hideBtn = t?.autoHide ?? (ko ? "접기" : "Hide");
  const copyBtn = t?.autoCopy ?? (ko ? "YAML 복사" : "Copy YAML");
  const copiedTxt = t?.autoCopied ?? (ko ? "복사됨!" : "Copied!");

  const cards = AUTOMATION_RECIPES.map((r) => {
    const isOpen = openId === r.id;
    const isCopied = copiedId === r.id;
    const tags = (ko ? r.devicesKo : r.devicesEn)
      .map((d) => `<span class="auto-dev-pill">${esc(d)}</span>`)
      .join("");
    const yamlCode = r.yaml(cid, ko);
    return `
      <div class="auto-card ${isOpen ? "open" : ""}">
        <div class="auto-top">
          <div class="auto-meta">
            <span class="badge status-upcoming">${esc(ko ? r.tagKo : r.tagEn)}</span>
            <strong class="auto-title">${esc(ko ? r.titleKo : r.titleEn)}</strong>
          </div>
          <button type="button" class="btn-outline small" data-toggle-recipe="${esc(r.id)}">
            ${esc(isOpen ? hideBtn : viewBtn)}
          </button>
        </div>
        <p class="auto-why">${esc(ko ? r.whyKo : r.whyEn)}</p>
        <div class="auto-devs">${tags}</div>
        ${
          isOpen
            ? `<div class="auto-yaml-wrap">
                 <div class="auto-yaml-bar">
                   <span class="small muted">child_id: <code>${esc(cid)}</code></span>
                   <button type="button" class="btn-primary small" data-copy-recipe="${esc(r.id)}">${esc(isCopied ? copiedTxt : copyBtn)}</button>
                 </div>
                 <pre class="auto-pre"><code>${esc(yamlCode)}</code></pre>
               </div>`
            : ""
        }
      </div>`;
  }).join("");

  return `
    <div class="card section-card ${wideClass}" data-section="automations">
      <div class="card-head">
        <div>
          <h3>${esc(title)}</h3>
          <div class="launcher-sub">${esc(sub)}</div>
        </div>
      </div>
      <div class="auto-list">${cards}</div>
    </div>`;
}
