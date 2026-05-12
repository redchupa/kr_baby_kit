# kr_baby_kit — 영유아 성장·예방접종·검진 HACS 통합

## 1. 목적

> 영유아 자녀가 있는 Home Assistant 사용자가 **성장곡선·예방접종·검진 일정**을 HA 센서/캘린더로 받을 수 있게 한다.

**왜?**
- 한국 육아 데이터를 HA에 가져오는 HACS 통합 부재.
- 본인이 자녀 데이터를 매주 기록하는 워크플로(`kidsnote-diary-suite`)를 가지고 있어 사용자 1호.
- 질병관리청·보건복지부·NIP 공공 데이터 무료. 공공데이터포털 키만 있으면 됨.
- `kr_component_kit`의 학교 메뉴와 자연스럽게 연결 (어린이집 → 학교).
- LLM tool: "다음 영유아 검진 언제야?", "우리 아이 또래 평균 키랑 비교하면?" 같은 자연어 쿼리.

## 2. 타겟 사용자

- 0~7세 자녀가 있는 HA 사용자
- 어린이집·유치원 다니는 자녀 부모
- 예방접종 일정 잊어버리는 부모 (대부분)
- 성장곡선 추적하는 부모 (수기 기록 vs 시각화)

## 3. 범위

**IN (v1)**
- ✅ 성장곡선 센서 — 자녀 측정값 입력 → 또래 ±백분위 자동 계산 (질병관리청 표준)
- ✅ 예방접종 일정 캘린더 — 자녀 생년월일 기준 NIP 일정 자동 산출
- ✅ 영유아 검진 일정 — 보건복지부 표준 **8회** 검진 시기 (생후 14~35일, 4개월, 9개월, 18개월, 30개월, 42개월, 54개월, 66개월 — 2021-01-01 시행 초기 검진 포함)
- ✅ 어린이집 보육료 변동 (정부 보조금 매년 인상분 — 공공데이터)
- ✅ Config Flow — 자녀 여러 명 등록 가능 (이름·생년월일·성별·키·몸무게)
- ✅ LLM tool: 자연어 쿼리

**OUT (v1)**
- ❌ 의료기관 예약 직연동
- ❌ 키즈노트 등 사설 서비스 연동 (`kidsnote-diary-suite`가 맡음)
- ❌ AI 진단·의학 조언

## 4. 아키텍처

```
custom_components/kr_baby_kit/
├── __init__.py
├── manifest.json
├── config_flow.py            # 자녀 등록 UI (이름·생년월일·성별)
├── const.py
├── coordinator.py
├── sensor.py                 # 키 백분위, 몸무게 백분위, BMI 등
├── calendar.py               # 예방접종·검진 일정 캘린더
├── binary_sensor.py          # 이번 달 예방접종 있음 등
├── llm_tool.py
├── services.yaml             # action: record_measurement
├── translations/
└── data/
    ├── growth_chart_kr.json  # 질병관리청 표준 (공개 데이터)
    └── nip_schedule.json     # 표준 예방접종 일정

데이터 소스 (모두 무료):
- 질병관리청 소아청소년 성장도표 (공개 JSON/PDF — 정적)
- NIP 표준 예방접종 일정 (공개)
- 보건복지부 영유아 검진 일정 (공개)
- 공공데이터포털 보육료 (data.go.kr 무료 키)
```

## 5. 파일 구조 (v1 골격)

```
kr_baby_kit/
├── README.md               # 한·영
├── LICENSE
├── PLAN.md
├── CLAUDE.md
├── hacs.json
├── .gitignore
├── .env.example
├── custom_components/
│   └── kr_baby_kit/        # (위 §4 구조)
├── tests/
│   ├── fixtures/
│   │   ├── child_synthetic_36m.yaml   # 합성 36개월 아동
│   │   └── growth_chart_sample.json
│   └── test_*.py
├── docs/
│   ├── installation-ko.md
│   ├── installation-en.md
│   ├── data-sources.md          # 출처·라이선스 명시
│   └── examples/
│       └── automation-examples.yaml
└── .github/workflows/
    ├── test.yml
    └── hassfest.yml
```

## 6. 마일스톤

### M0 — 데이터 수집 + 골격 (1 세션)
- [ ] 질병관리청 소아청소년 성장도표 (2017년판 + 최신) 입수 → `data/growth_chart_kr.json` 가공
- [ ] NIP 표준 예방접종 일정 → `data/nip_schedule.json`
- [ ] 출처·라이선스 docs/data-sources.md 명기
- [ ] manifest.json + config_flow 스켈레톤
- [ ] hassfest CI

### M1 — 성장곡선 + 측정 (1~2 세션)
- [ ] sensor.py — 키/몸무게/머리둘레 백분위 계산
- [ ] config_flow.py — 자녀 등록 마법사 (이름·생년월일·성별)
- [ ] services.yaml: `record_measurement` (날짜·키·몸무게)
- [ ] 측정 기록 저장 (input_number 또는 별도 storage)
- [ ] LLM tool: "키 백분위 알려줘"

### M2 — 예방접종 + 검진 캘린더 (1~2 세션)
- [ ] calendar.py — 자녀 생년월일 기준 예방접종/검진 다가오는 일정 노출
- [ ] binary_sensor.py — "이번 달 예방접종 있음"
- [ ] 자동화 예시 — 일정 임박 시 알림 (HA notify)
- [ ] LLM tool: "다음 검진 언제?"

### M3 — 보육료 + 문서 + 릴리스
- [x] docs/ 한·영 완성
- [x] 후원 섹션
- [x] 보육료 통합 (v0.4.0 — 번들 JSON + sensor 3종 + LLM tool. 교육부 「2026년도 보육사업안내 부록 2」 실측 단가 적용. 매년 1월 교육부 갱신본으로 JSON 동기화 필요)
- [ ] HACS Default PR (스킵 — 한국 전용. Custom Repository로만 배포)
- [x] GitHub 릴리스 v0.2.0
- [x] v0.3.0 BMI/timestamp 센서
- [x] v0.4.0 보육료 실측 단가 + 릴리스 게이트 스크립트

## 7. 무료/보안 가드 (본 레포 특화) — 자녀 데이터 가드 최강

### 자녀 정보
- ❌ `하린`, `우하린`, `WooRin`, 출생일, 어린이집명 절대 코드/README/fixture 노출 X
- ✅ 모든 예시·테스트는 합성 (`baby_a`, `child_b`, 생년월일 `2020-03-15` 같은 일반 값 — 자녀 실제 출생 연도 회피)
- ✅ Config Flow에 저장된 자녀 정보는 HA Storage(`async_get_data` 암호화)에 보관

### 성장 데이터
- 본인 자녀의 실제 측정값 절대 fixture 사용 X
- 합성 데이터로 백분위 계산 검증

### 데이터 출처
- 질병관리청·보건복지부 데이터의 정확한 출처 URL을 `docs/data-sources.md`에 명기
- 라이선스 (공공누리 등) 확인 후 README에 표시
- 의학·진단 책임 회피 면책 ("참고용이며 의료기관 진료를 대체하지 않습니다")

### 레포명
- 확정: `kr_baby_kit`. 폴더명·GitHub 레포명·HA domain 모두 동일.

### 후원 메타
- HA device entry에 후원 메타:
  ```python
  manufacturer="우*만",
  model="토스 1000-1261-7813",
  sw_version="커피 한잔은 사랑입니다",
  ```

## 8. 본인 자산 참조 (재활용 가능 경로)

| 자산 | 위치 | 어떻게 쓰나 |
|---|---|---|
| HA 통합 구조 | `github_auto_development/kr_component_kit/custom_components/kr_component_kit/` | Config Flow + LLM tool 패턴 동일 |
| 캘린더 패턴 | `kr_component_kit` 학교 캘린더 부분 | 검진·예방접종 캘린더에 적용 |
| 의료 휴먼팩터 메모 | `homeassistant_mcp/memory/automation_baby_sleep_ai.md` | 알림 톤·시각 결정 |
| 가족 구성 메타 | `homeassistant_mcp/memory/family_members.md` | 가족 데이터 모델 (단, **내용은 참조만**, 코드 포함 X) |

## 9. 수락 기준 (v1.0 DoD)

- [ ] HACS 설치 → Config Flow로 가상 자녀 등록 → sensor.kr_baby_kit_*_percentile 정상
- [ ] calendar.kr_baby_kit_*_immunization 정상 (다가오는 일정 노출)
- [ ] LLM tool: "다음 검진 언제?" 답변 정상
- [ ] hassfest CI 그린
- [ ] 합성 fixture로 테스트 전부 그린
- [ ] docs/data-sources.md 출처·라이선스 완비
- [x] 보안 grep: `하린`, `WooRin`, 본인 자녀 생년월일, 어린이집명, IP, 본인 정보 0건
- [x] 레포명 확정 (`kr_baby_kit`)

## 10. 다음 세션 시작 프롬프트

```
이 폴더는 kr_baby_kit 영유아 HACS 통합 프로젝트입니다.
PLAN.md, CLAUDE.md, ../MASTER_PLAN.md 를 먼저 읽으세요.

⚠️ 자녀 데이터 관련 — PLAN.md §7 보안 가드 최강 수준 준수.

현재 상태: M0/M1/M2/M3 완료 (성장곡선·BMI·접종·검진·신장별체중·timestamp 센서·number 입력·LLM tool·보육료 2026년 단가).
남은 작업:
1. GitHub 릴리스 태깅 (v0.4.0)·HACS Custom Repository 안내 정비
2. `your-github-username` placeholder → 실제 GitHub 계정 교체
3. 2027년 1월: 교육부 차년도 「보육사업안내」 PDF 입수 후 `care_tuition_kr.json` 갱신 + 테스트의 `data_year` 동기화

본인 자녀 실명·생년월일·측정값 어디에도 포함 금지.
끝나면 진행사항 요약 + 다음 단계 제안.
```
