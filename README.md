# 한국 영유아 키트 (Korean Baby Kit)

> **아이의 키·몸무게·예방접종·검진·보육료, 매일 잊고 살았던 것들.**
> 측정만 입력하면 나머지는 Home Assistant가 자동으로 챙겨드립니다.

[![Validate](https://github.com/redchupa/kr_baby_kit/actions/workflows/hassfest.yml/badge.svg)](https://github.com/redchupa/kr_baby_kit/actions/workflows/hassfest.yml)
[![Tests](https://github.com/redchupa/kr_baby_kit/actions/workflows/test.yml/badge.svg)](https://github.com/redchupa/kr_baby_kit/actions/workflows/test.yml)
[![HACS](https://raw.githubusercontent.com/redchupa/kr_baby_kit/main/images/hacs-custom-badge.png)](https://github.com/hacs/integration)
[![Release](https://img.shields.io/github/v/release/redchupa/kr_baby_kit?include_prereleases&label=release)](https://github.com/redchupa/kr_baby_kit/releases)
[![License](https://raw.githubusercontent.com/redchupa/kr_baby_kit/main/images/license-badge.png)](LICENSE)

---

## 👶 이런 부모님께 추천드려요

- 0~7세 자녀를 키우는 분
- Home Assistant를 이미 쓰고 계신 분 (없으면 ▶ [Home Assistant 시작하기](https://redchupa.com/entry/%ed%99%88%ec%96%b4%ec%8b%9c%ec%8a%a4%ed%84%b4%ed%8a%b8ha-%ec%9e%85%eb%ac%b8-%ea%b0%80%ec%9d%b4%eb%93%9c/))
- 아이 성장 기록, 어린이집 알림장, 정부 검진 일정, 보육료 정산… **한 화면에서 보고 싶으신 분**
- 의학 정보는 정확하게, 일상은 단순하게 만들고 싶으신 분

> 💡 **개발자나 IT 전문가가 아니어도 됩니다.** 코드 한 줄 만질 일 없이 마우스 클릭과 슬라이더 조작만으로 사용 가능합니다.

---

## ✨ 이런 순간에 도움돼요

### 🌙 새벽 2시, 아이 키 재고 나서

> "오늘 90.2cm 나왔는데… 또래 평균이야? 작은 거야?"

→ 슬라이더 한 번 움직이면 **"키: 또래 상위 23% (큰 편)"** 즉시 표시.
KDCA 2017 공식 성장표 기준이라 소아과 차트와 같은 결과.

### 📱 출근길, 어린이집 알림장 보다가

> "다음 접종 언제더라? 어린이집 문자에 있던 것 같은데…"

→ 핸드폰 HA 앱 열면 **"BCG 2차 — D-14"** 카드가 첫 화면에.
자녀 생일만 입력하면 질병관리청 표준 일정으로 자동 계산. **18종 백신 전부 무료 지원 (NIP)**.

### 🏥 28개월, 영유아 검진 시기 헷갈릴 때

> "30개월 검진은 만 30개월? 우리 애 이제 28개월인데 언제 가야 하지?"

→ **"다음 검진: 2026-08-15 (만 30개월~36개월)"** 명확히 노출.
보건복지부 표준 **8회 검진** (생후 14~35일 신생아 검진부터 만 6세까지) 모두 자동.

### 💰 매월 25일, 어린이집 결제 알림 받기 전

> "다음 달 본인부담금이 얼만지 미리 알 수 있을까?"

→ **"만 2세반 본인부담금: 0원 (무상보육)"** 자녀 만 나이 맞춰 자동.
교육부 **2026년도 실측 단가** (만 0세 584,000원 ~ 만 6세 280,000원) 번들.

### 🚨 BMI 검사 결과가 신경 쓰일 때

> "비만 경향이라고 들었는데… 매번 진료 받으러 가야 하나?"

→ **`BMI 양극단 주의`** binary 알림이 평소엔 OFF.
양극단(< 5% 저체중 또는 > 95% 비만 경향)일 때만 ON으로 바뀌어 빨간 알림. 진단은 의사에게, 신호는 자동으로.

### 🎙️ 손에 아이 안고 있을 때

> 손이 안 비면 음성으로 — *"하이 어시스턴트, 다음 접종 언제야?"*

→ Assist (Home Assistant 음성 비서) 자동 응답. 키 백분위·검진 일정·이번 달 보육료까지 자연어로 질문 가능.

---

## 🚀 30초 설치 (코드 한 줄 안 만져요)

### 1️⃣ HACS에 저장소 추가 (1번만)

Home Assistant 화면에서:

1. **HACS** 메뉴 클릭
2. **Integrations** 탭 → 우상단 **점 3개(⋮)** → **사용자 지정 저장소**
3. 저장소 칸에 붙여넣기:
   ```
   https://github.com/redchupa/kr_baby_kit
   ```
4. 카테고리 → **Integration** 선택 → **추가**

### 2️⃣ kr_baby_kit 다운로드 + 재시작

1. HACS Integrations 검색창에 **"한국 영유아 키트"** 입력
2. 클릭 → **DOWNLOAD** 버튼
3. **Home Assistant 재시작** (설정 → 시스템 → 재시작)

### 3️⃣ 자녀 등록

1. **설정 → 기기 및 서비스 → 통합 추가** 클릭
2. 검색창에 **"kr_baby_kit"** → 선택
3. 자녀 정보 입력:

   | 항목 | 입력 예시 |
   |---|---|
   | 자녀 이름 또는 별칭 | `첫째` · `둘째` · `Baby A` (실명 권장 안 함) |
   | 생년월일 | `2023-05-14` |
   | 성별 | 남아 / 여아 |

4. **제출** 클릭. 끝.

> 🎉 **자녀별로 device 1개와 sensor 14개가 자동으로 생성됩니다.**
>
> 자녀가 둘 이상이라면? 통합 추가를 한 번 더 하시면 됩니다.

---

## 📊 등록 후 대시보드에서 보이는 것들

자녀 device 안에 다음 entity들이 자동 생성됩니다:

### 📏 측정 입력 (number, 슬라이더)
- `키_입력` · `몸무게_입력` · `머리둘레_입력` — 한 손으로 슬라이더 움직이면 끝

### 📊 또래 위치 (sensor, %)
- `백분위_키_1퍼센트는_가장_큼` · `백분위_몸무게_1퍼센트는_가장_무거움`
- 한 줄 요약: *"키: 또래 상위 5.3% (큰 편)"*

### 🚨 양극단 주의 (binary_sensor, on/off)
- `양극단_주의_머리둘레` · `양극단_주의_BMI` · `양극단_주의_신장별_몸무게`
- 평소 OFF, 양극단(< 5% 또는 > 95%)일 때만 ON

### 💉 일정 (sensor + binary_sensor)
- `일정_다음_예방접종` · `일정_다음_검진` — D-day 형식 timestamp
- `일정_이번_달_예방접종` · `일정_이번_달_검진` — 이번 달 일정 유무

### 🗓️ 캘린더 (calendar)
- `캘린더_예방접종` · `캘린더_검진` — HA 캘린더 카드에 그대로 노출

### 🏷️ 보육료 (sensor, KRW)
- `보육료_표준` · `보육료_정부지원금` · `보육료_본인부담금`

### ℹ️ 부가 정보 (sensor)
- `정보_BMI_수치` (kg/m²) · `정보_월령_개월_수`

> 💡 **모든 entity 이름이 한국어**. HA UI에서 가나다순 정렬 시 카테고리별로 자연 묶임.

---

## 🎨 자동화 예시 (선택, 클릭 한 번이면 됩니다)

```yaml
# 예방접종 D-14에 모바일 알림
- alias: 접종 D-14 알림
  trigger:
    - platform: template
      value_template: >-
        {% set t = states('sensor.kr_baby_kit_<자녀>_next_vaccine') %}
        {{ t not in ('unknown','unavailable','') and
           (as_datetime(t) - now()).days == 14 }}
  action:
    - service: notify.mobile_app
      data:
        title: "예방접종 임박"
        message: "{{ state_attr('sensor.kr_baby_kit_<자녀>_next_vaccine', 'name_ko') }} 2주 남았어요"

# BMI 양극단 신호 시 모바일 알림
- alias: BMI 양극단 알림
  trigger:
    - platform: state
      entity_id: binary_sensor.kr_baby_kit_<자녀>_bmi_concern
      to: "on"
  action:
    - service: notify.mobile_app
      data:
        title: "성장 알림"
        message: >-
          {{ state_attr('binary_sensor.kr_baby_kit_<자녀>_bmi_concern', 'summary_ko') }}
          소아청소년과 진료를 한 번 받아보세요.
```

더 많은 예시 → [docs/examples/automation-examples.yaml](docs/examples/automation-examples.yaml)

---

## 📚 의학 데이터 — 출처 명확, 무료, 오프라인

| 데이터 | 출처 | 라이선스 |
|---|---|---|
| 소아청소년 성장도표 (LMS) | [질병관리청 2017](https://www.kdca.go.kr/kdca/5458/subview.do) | 공공누리 제1유형 |
| 표준 예방접종 일정 (NIP) | [질병관리청 예방접종도우미](https://nip.kdca.go.kr/irhp/goMainInfo.do) | 공공누리 제1유형 |
| 영유아 건강검진 (8회) | [국민건강보험공단](https://www.nhis.or.kr/nhis/healthin/wbhabb02100m01.do) · [2021 8회 확대 보도자료](https://www.mohw.go.kr/board.es?mid=a10503010100&bid=0027&act=view&list_no=362391) | 공공누리 제1유형 |
| 보육료 단가 (2026년) | [교육부 「2026년도 보육사업안내 부록 2」](https://www.daejeon.go.kr/data/drh/sub05/2026_data_02.pdf) | 공공누리 제1유형 |

> ✅ **모두 정부 공공 데이터**. 외부 API 키 필요 없음. 인터넷이 끊겨도 작동.
> 🤖 보육료 단가가 outdated 되면 GitHub Actions이 매월 1일 자동 점검 후 갱신 issue 생성 (사용자 별도 알림 불필요).

자세히 → [docs/data-sources.md](docs/data-sources.md)

---

## 🔒 자녀 데이터는 안전합니다

- 측정값은 **본인 Home Assistant Storage에만** 저장. 외부 서버 전송 0건.
- 외부 API 키 불필요. 인터넷 끊겨도 작동.
- 잘못된 값(`-5`, `99999`, `NaN`, `abc` 등) 입력 시 **3-layer 검증**으로 거부 → 잘못된 데이터로 percentile 계산되는 일 없음.
- 본 레포 코드에 어떤 자녀·가족 식별자도 포함되지 않음 (CI gate로 검증).

## ⚠️ 의학적 면책

본 통합이 제공하는 모든 백분위·접종·검진 정보는 **참고용**입니다.

- 의학적 진단·처방·치료를 대체하지 않습니다.
- 자녀의 성장·건강은 반드시 **소아청소년과 전문의의 진료**를 통해 평가하세요.
- 양극단 알림이 ON이 되었다고 즉시 병원으로 달려가실 필요는 없지만, **다음 검진 때 소아과 의사에게 한 번 더 확인**해보시길 권장합니다.

## 📜 라이선스

[MIT License](LICENSE). 데이터는 공공누리 제1유형으로 재배포되며 출처 표시 의무가 있습니다 (통합이 모든 사용자 노출 지점에 자동 표시).

---

## ⭐ 도움이 되셨다면

- **GitHub 저장소 페이지 우상단 ⭐ Star** — 다른 부모님들이 발견하기 쉬워집니다
- **이슈 / 개선 제안** → [Issues](https://github.com/redchupa/kr_baby_kit/issues)
- **번역·문서 기여 환영** → Pull Request

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

- 토스/카카오뱅크: **1000-1261-7813** (우*만) · *커피 한잔은 사랑입니다*

---

<details>
<summary><strong>🌐 English summary</strong></summary>

### Korean Baby Kit for Home Assistant

A HACS integration that turns three measurement inputs (height, weight, head circumference) into a full picture of your child's growth, vaccinations, checkups, and childcare-fee status — using only Korean public-sector data (KDCA, NIP, MOHW, MOE).

**Who is it for?**
Parents of children aged 0–7 who already use Home Assistant and want a single screen for their child's daily measurements, immunization reminders, checkup windows, and monthly childcare-fee figures.

**Key features**
- 📏 LMS-based percentile sensors for height / weight, with school-rank-style readouts ("1%=tallest"); BMI raw value
- 🚨 Bi-directional `*_concern` binary alerts for head circumference, BMI, and weight-for-length (fires when statistical percentile leaves the 5–95 normal band)
- 💉 Auto-computed vaccine calendar from KDCA NIP schedule + D-day `timestamp` sensors
- 🩺 8-stage infant health checkup schedule (보건복지부 — early 14–35 day visit included since 2021)
- 🏷️ Real 2026 childcare-tuition figures from the Ministry of Education, refreshed annually via a `data-stale` GitHub Issue cron
- 🛡️ Three-layer measurement input validation rejects NaN / Inf / non-numeric / out-of-range values with Korean error messages
- 🎙️ Per-child LLM API (Assist) for natural-language queries
- 🌐 Fully offline — no API keys, all reference tables bundled
- ✅ `hassfest`, HACS validation, pytest matrix (3.11 / 3.12 / 3.13), privacy-grep CI gates

**Setup time:** under a minute through HACS Custom Repositories.

**Data licence:** KOGL Type 1 (attribution required, redistribution OK). The integration surfaces the citation automatically.

**Medical disclaimer:** Reference only. Does not replace pediatrician care. The `*_concern` binary sensors are signals, not diagnoses.

</details>
