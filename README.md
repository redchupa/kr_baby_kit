# 한국 영유아 키트 (Korean Baby Kit)

> **우리 아이 키·몸무게·예방접종·검진·보육료 — Home Assistant 하나로.**
> 질병관리청·교육부·보건복지부 공공 데이터 기반, 100% 무료·오프라인.

[![Validate](https://github.com/redchupa/kr_baby_kit/actions/workflows/hassfest.yml/badge.svg)](https://github.com/redchupa/kr_baby_kit/actions/workflows/hassfest.yml)
[![Tests](https://github.com/redchupa/kr_baby_kit/actions/workflows/test.yml/badge.svg)](https://github.com/redchupa/kr_baby_kit/actions/workflows/test.yml)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Release](https://img.shields.io/github/v/release/redchupa/kr_baby_kit?include_prereleases&label=release)](https://github.com/redchupa/kr_baby_kit/releases)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 😩 이런 경험, 익숙하지 않으세요?

- 📏 **"오늘 키 잰 거, 또래 평균이랑 비교하면 어디쯤이지?"** → 손으로 KDCA 표 찾기
- 💉 **"다음 접종 언제더라?"** → 어린이집 알림장·문자·앱 3군데 확인
- 🩺 **"영유아 검진 — 30개월? 42개월? 헷갈려…"** → 매번 검색
- 💰 **"이번 달 보육료 본인부담금이 얼만지…"** → 어린이집 정산 기다림
- 📈 **"우리 아이 체형, 또래보다 마른 편? 비만 경향?"** → 모호한 직감

이 모든 걸 **Home Assistant 통합 하나로**. 매일 키·몸무게만 입력하면 나머지는 자동입니다.

---

## ✨ 무엇을 해주나요

### 📏 성장 측정 — 입력 한 번이면 끝
- `number` 슬라이더로 키·몸무게·머리둘레 한 손 입력 (오늘 날짜 자동)
- 입력 즉시 **또래 백분위** 자동 계산 — KDCA 2017 LMS 표준 공식
- 같은 날 여러 항목 입력 → 한 record로 자동 병합

### 📊 또래 등수 한 눈에
- **`백분위 · 키 (1%=가장 큼)`** · **`백분위 · 몸무게 (1%=가장 무거움)`** — 학교 등수 직관 그대로
- 카드 한 줄 요약: *"키: 또래 상위 5.3% (큰 편)"*
- 통계학적 percentile도 attribute로 보존 (power user 용)

### 🚨 양극단 자동 감지
- **머리둘레 / BMI / 신장별 체중** — 양극단(< 5%, > 95%)일 때 binary 알림 on
- `device_class: problem` → 대시보드 카드에서 빨간색으로 즉시 인지
- 진단은 의사에게, 신호는 자동으로

### 💉 예방접종 캘린더 — 자녀 생일만 입력하면
- 질병관리청 NIP 표준 일정 → 자녀 생년월일 기준 자동 산출
- **D-day timestamp sensor** — Lovelace 카드에서 "D-14" 표시
- "이번 달 접종 있음" binary_sensor → 월요일 아침 알림 자동화 1줄

### 🩺 영유아 건강검진 8회
- 보건복지부 표준 검진 시기 (**생후 14~35일** + 4·9·18·30·42·54·66개월) 자동 노출
- 2021-01-01 시행 초기 검진(생후 14~35일) 포함 — 신생아 부모도 놓치지 않음
- 임박 시 알림 자동화 — 날짜 까먹을 일 없음

### 🏷️ 보육료 자동 매칭 (2026년)
- 자녀 만 나이 → 표준보육료 / 정부지원금 / 본인부담금 자동
- **교육부 「2026년도 보육사업안내」 실측 단가** 번들 (만 0세 584,000원 ~ 만 6세 280,000원)
- 매년 1월 차년도 단가로 자동 갱신 알림 (GitHub Issue cron)

### 🎙️ Assist 음성 비서 연동
자녀별 LLM API 자동 등록. 자연어로 질문:
- *"다음 접종 언제야?"* / *"이번 달 검진 일정 알려줘"*
- *"또래 상위 몇 %야?"* / *"BMI 정상 범위야?"*
- *"이번 달 보육료 얼마야?"*

### 🌐 100% 오프라인
참조 데이터 모두 번들. **외부 API 키 불필요**. 자녀 측정값은 HA Storage에만 저장, 외부 전송 0건.

---

## 🚀 30초 설치

### 1. HACS Custom Repository로 추가

```yaml
HACS → Integrations → ⋮ → Custom repositories
URL:      https://github.com/redchupa/kr_baby_kit
Category: Integration
```

→ 추가 후 검색 *한국 영유아 키트* → 다운로드 → HA 재시작

### 2. 자녀 등록 (Config Flow)

`설정 → 기기 및 서비스 → 통합 추가 → kr_baby_kit`

- **자녀 이름 또는 별칭** (예: `첫째`, `Baby A`)
- **생년월일** (YYYY-MM-DD)
- **성별** (남아 / 여아)

→ 자녀별로 device 1개 + sensor 14개가 자동 생성됩니다.

### 3. 측정값 입력

대시보드의 `키 입력` / `몸무게 입력` / `머리둘레 입력` 슬라이더 한 번 움직이면 백분위가 즉시 갱신됩니다.

자녀가 둘 이상이면 통합을 한 번 더 추가하세요.

📖 자세한 설치 가이드: [docs/installation-ko.md](docs/installation-ko.md) (EN: [installation-en.md](docs/installation-en.md))

---

## 🎨 자동화 예시 (가장 자주 쓰는 것들)

```yaml
# 다음 접종 D-14에 모바일 알림
- alias: 접종 D-14 알림
  trigger:
    - platform: template
      value_template: >-
        {% set t = states('sensor.kr_baby_kit_baby_a_next_vaccine') %}
        {{ t not in ('unknown','unavailable','') and
           (as_datetime(t) - now()).days == 14 }}
  action:
    - service: notify.mobile_app
      data:
        message: "{{ state_attr('sensor.kr_baby_kit_baby_a_next_vaccine', 'name_ko') }} D-14"

# BMI 양극단 신호 시 진료 알림
- alias: BMI 양극단 알림
  trigger:
    - platform: state
      entity_id: binary_sensor.kr_baby_kit_baby_a_bmi_concern
      to: "on"
  action:
    - service: notify.mobile_app
      data:
        message: >-
          {{ state_attr('binary_sensor.kr_baby_kit_baby_a_bmi_concern', 'summary_ko') }}.
          소아청소년과 진료를 통해 확인하세요.
```

더 많은 예시 → [docs/examples/automation-examples.yaml](docs/examples/automation-examples.yaml)

---

## 📚 데이터 출처 — 모두 공공 무료

| 데이터 | 출처 | 라이선스 |
|---|---|---|
| 소아청소년 성장도표 (LMS) | [질병관리청 2017](https://www.kdca.go.kr/kdca/5458/subview.do) | 공공누리 제1유형 |
| 예방접종 일정 | [질병관리청 예방접종도우미](https://nip.kdca.go.kr/irhp/goMainInfo.do) | 공공누리 제1유형 |
| 영유아 건강검진 | [국민건강보험공단](https://www.nhis.or.kr/nhis/healthin/wbhabb02100m01.do) | 공공누리 제1유형 |
| 보육료 단가 | [교육부 「2026년도 보육사업안내 부록 2」](https://www.daejeon.go.kr/data/drh/sub05/2026_data_02.pdf) | 공공누리 제1유형 |

자세히 → [docs/data-sources.md](docs/data-sources.md)

---

## 🔒 보안·프라이버시

- 자녀 측정값은 **HA Storage에만** 저장. 외부 전송 0건.
- 외부 API 키 불필요 — 인터넷 끊겨도 작동.
- CI gate로 본 레포에 자녀·가족 식별자 0건 검증.

## ⚠️ 의학적 면책

본 통합이 제공하는 모든 백분위·접종·검진 정보는 **참고용**이며, 의학적 진단·처방·치료를 대체하지 않습니다. 자녀의 성장·건강 상태는 반드시 **소아청소년과 전문의의 진료**를 통해 평가하시기 바랍니다.

## 📜 라이선스

[MIT License](LICENSE). 데이터는 공공누리 제1유형으로 재배포되며 출처 표시 의무가 있습니다 (통합이 모든 사용자 노출 지점에 자동 표시).

---

## ☕ 후원

본 통합이 도움이 되셨다면 커피 한 잔으로 응원해주세요! 🙏

<table>
  <tr>
    <td align="center">
      <b>토스</b><br/>
      <img src="https://raw.githubusercontent.com/redchupa/kr_baby_kit/main/images/toss-donation.png" alt="Toss 후원 QR" width="200"/>
    </td>
    <td align="center">
      <b>PayPal</b><br/>
      <img src="https://raw.githubusercontent.com/redchupa/kr_baby_kit/main/images/paypal-donation.png" alt="PayPal 후원 QR" width="200"/>
    </td>
  </tr>
</table>

- 토스/카카오뱅크: **1000-1261-7813** (우*만) · 커피 한잔은 사랑입니다

---

<details>
<summary><strong>English summary</strong></summary>

### Korean Baby Kit for Home Assistant

A HACS integration that turns three measurement inputs (height, weight, head) into a full picture of your child's growth, vaccinations, checkups, and childcare-fee status — using only Korean public data (KDCA, NIP, MOHW, MOE).

**Key features**
- 📏 LMS-based percentile sensors (height, weight) + BMI raw value
- 🚨 Bi-directional `*_concern` binary alerts for head circumference, BMI, and weight-for-length (fires when statistical percentile leaves the 5–95 normal band)
- 💉 Auto-computed vaccine calendar from KDCA NIP schedule + D-day `timestamp` sensors
- 🩺 8-stage infant health checkup schedule (보건복지부 — early 14–35 day visit included since 2021)
- 🏷️ Real 2026 childcare-tuition figures from the Ministry of Education
- 🎙️ Per-child LLM API (Assist) for natural-language queries
- 🌐 Fully offline — no API keys, all reference tables bundled
- ✅ `hassfest`, HACS validation, pytest matrix (3.11/3.12/3.13), privacy-grep CI gates

**Data licence:** KOGL Type 1 (attribution required, redistribution OK). The integration surfaces the citation automatically.

**Disclaimer:** Reference only. Does not replace pediatrician care.

</details>
