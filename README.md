# 한국 영유아 키트 (Korean Baby Kit)

[![Validate](https://github.com/your-github-username/kr_baby_kit/actions/workflows/hassfest.yml/badge.svg)](https://github.com/your-github-username/kr_baby_kit/actions/workflows/hassfest.yml)
[![Tests](https://github.com/your-github-username/kr_baby_kit/actions/workflows/test.yml/badge.svg)](https://github.com/your-github-username/kr_baby_kit/actions/workflows/test.yml)
[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Release](https://img.shields.io/github/v/release/your-github-username/kr_baby_kit?include_prereleases&label=release)](https://github.com/your-github-username/kr_baby_kit/releases)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> Home Assistant 통합 — 한국 영유아 데이터를 HA로. 성장곡선·예방접종·검진 일정.

## 무엇을 하나

- 📏 **성장곡선 백분위** — 질병관리청 2017 LMS 기반 키/몸무게/머리둘레 + BMI(만 2세부터) + 신장별 체중 (영유아 ≤ 2세 누운키, 2세+ 서서 잰 키)
- 💉 **예방접종 일정** — 표준 NIP 일정 기반 자동 캘린더 + 다음 접종 timestamp 센서 (D-day 카드용)
- 🩺 **영유아 건강검진** — 보건복지부 표준 7회 검진 일정 + 다음 검진 timestamp 센서
- 🏷️ **보육료** — 자녀 만 나이로 자동 매칭되는 **표준보육료 / 정부지원금 / 본인부담금** (단위: KRW). 교육부 「2026년도 보육사업안내 부록 2」 종일반 단가 번들. 출처·갱신 방법은 [docs/data-sources.md](docs/data-sources.md).
- ✍️ **간편 입력** — number 슬라이더로 키/몸무게/머리둘레 즉시 기록 (오늘 날짜 자동, 같은 날 다중 항목 자동 병합)
- 🎙️ **Assist (LLM) 연동** — 자녀별 별도 API: "다음 접종 언제?", "또래 평균 대비 키 백분위?", "이번 달 보육료?"
- 🌐 **오프라인 동작** — 모든 참조 데이터 번들. 외부 API 키 불필요.

## 데이터 출처 (모두 공공 무료)

- [질병관리청 2017 소아청소년 성장도표](https://www.kdca.go.kr/kdca/5458/subview.do)
- [질병관리청 예방접종도우미](https://nip.kdca.go.kr/irhp/goMainInfo.do)
- [국민건강보험공단 영유아 건강검진](https://www.nhis.or.kr/nhis/healthin/wbhabb02100m01.do)
- [공공데이터포털 LMS 자료](https://www.data.go.kr/data/15076588/fileData.do)
- [교육부 「2026년도 보육사업안내」 부록 2 — 영유아보육료 지원금액](https://www.daejeon.go.kr/data/drh/sub05/2026_data_02.pdf) (발간등록번호 11-1342000-100026-10)

라이선스: 공공누리 제1유형 (출처 표시). 상세는 [docs/data-sources.md](docs/data-sources.md).

## 설치

```yaml
HACS → Integrations → ⋮ → Custom repositories
URL: https://github.com/your-github-username/kr_baby_kit
Category: Integration
```

자세한 단계는 [docs/installation-ko.md](docs/installation-ko.md) (EN: [installation-en.md](docs/installation-en.md)).

## 빠른 시작

```yaml
설정 → 기기 및 서비스 → 추가 → "한국 영유아 키트"
→ 자녀 이름·생년월일·성별 입력
→ 대시보드의 number.<자녀>_키 / _몸무게 슬라이더로 측정 기록
```

자동화 예시: [docs/examples/automation-examples.yaml](docs/examples/automation-examples.yaml)

## 데이터 갱신

번들된 성장도표 JSON은 KDCA 갱신 시 `scripts/build_growth_chart.py` 로 재빌드합니다 ([scripts/README.md](scripts/README.md) 참고).

## 보안·프라이버시

- 자녀 측정값은 **HA Storage에만** 저장됩니다. 외부 전송 없음.
- 자녀 실명·생년월일 등은 본인 HA 인스턴스 내에서만 사용. 본 레포는 본인 정보 0건 (CI gate).

## ⚠️ 의학적 면책

본 정보는 **참고용**이며 의료기관 진료를 대체하지 않습니다. 자녀의 성장·건강 평가는 소아청소년과 전문의에게 의뢰하십시오.

## 후원

본 통합이 도움이 되셨다면:
- 카카오뱅크/토스 **1000-1261-7813** (우*만)
- 커피 한잔은 사랑입니다 ☕

---

<details>
<summary>English summary</summary>

Home Assistant integration exposing Korean infant/child reference data
as devices, sensors, calendars, and number-input entities.

**Features**
- LMS-based percentile sensors: height, weight, head, BMI, weight-for-length.
- Calendar entities for upcoming vaccines and the 7-stage infant health checkups.
- `number` platform for one-tap measurement input from any dashboard.
- Per-child LLM API for voice assistant queries.

**Data**
All reference tables come from KDCA, KDCA-NIP, and 보건복지부, redistributed
under KOGL Type 1 (attribution required). The integration runs entirely
offline — no API keys.

**Disclaimer**
Information only. Does not provide medical advice; always consult a pediatrician.

</details>
