# 설치 가이드 (한국어)

## 1. 사전 준비

- Home Assistant 2024.6 이상
- HACS 설치 완료
- 자녀의 생년월일·성별 정보

## 2. HACS 통해 설치

1. HACS → 통합 → 우상단 ⋮ → **사용자 지정 저장소 (Custom repositories)**
2. URL: `https://github.com/redchupa/kr_baby_kit`
3. 카테고리: **Integration**
4. **추가** → 목록에서 *한국 영유아 키트* 검색 → 다운로드
5. Home Assistant 재시작

## 3. 자녀 등록 (Config Flow)

1. **설정 → 기기 및 서비스 → 통합 추가**
2. *kr_baby_kit* 선택
3. 입력:
   - **자녀 이름 또는 별칭** (예: `첫째`, `아들`, `Baby A`)
   - **생년월일**: YYYY-MM-DD
   - **성별**: 남아 / 여아
4. 자녀별로 별도 device가 생성됩니다. 두 명 이상이면 통합을 다시 추가해서 등록하세요.

## 4. 측정 기록

### 권장: 대시보드에서 직접 입력

각 자녀 device에 자동 생성되는 **number** 엔티티 3종:

- `number.<자녀>_키` (cm)
- `number.<자녀>_몸무게` (kg)
- `number.<자녀>_머리둘레` (cm)

값을 변경하면 자동으로 **오늘 날짜**로 기록되고 백분위가 즉시 갱신됩니다.
같은 날 여러 항목을 갱신하면 한 record로 합쳐집니다.

### 과거 측정 백필 (배치 입력)

개발자 도구 → 작업 → `kr_baby_kit.record_measurement` (날짜 명시):

```yaml
service: kr_baby_kit.record_measurement
data:
  child_id: "ab12cd34ef56"   # 한 명만 등록 시 생략 가능
  date: "2025-08-15"
  height: 75.4
  weight: 9.2
  head: 46.0
```

기록 후 `sensor.<자녀>_키_백분위` 등이 자동 갱신됩니다.

## 5. 캘린더 확인

- `calendar.kr_baby_kit_<이름>_예방접종_일정`
- `calendar.kr_baby_kit_<이름>_영유아_검진_일정`

각 일정은 질병관리청·보건복지부 표준 일정에 따라 자녀 생년월일을 기준으로 자동 계산됩니다.

## 5-1. 보육료 센서 (v0.4.0a 알파)

자녀 만 나이에 자동 매칭되는 보육료 센서가 자녀 device에 함께 생성됩니다:

- `sensor.<자녀>_표준보육료` (단위: KRW)
- `sensor.<자녀>_보육료_정부지원금` (단위: KRW)
- `sensor.<자녀>_보육료_본인부담금` (단위: KRW)

⚠️ 번들된 보육료 JSON(`custom_components/kr_baby_kit/data/care_tuition_kr.json`)은
**placeholder 데이터(`data_year: 0`, 모든 값 `0`)**로 출시됩니다. 통합을
설치하기 전에 이 파일을 매년 보건복지부 표준보육료 고시로 갱신하세요.
placeholder 상태일 때 센서는 `Unknown`(None)을 반환하며, `is_placeholder`
속성이 `true`로 표시됩니다.

JSON 스키마는 안정적이며 다음 필드만 갱신하면 됩니다:
- `_meta.data_year` → 해당 연도 (예: `2025`)
- 각 `tiers[].standard_tuition` / `government_subsidy` / `parent_share` → 고시 금액

## 6. 음성 비서 (Assist) 연동

자녀 등록 시 LLM API가 자동 등록되므로 Assist 파이프라인에서 활성화:

1. 설정 → 음성 비서 → 사용 중인 파이프라인 편집
2. **LLM API** 항목에서 `kr_baby_kit · <자녀 이름>` 체크
3. 예시 질의: "다음 예방접종 언제야?", "또래 평균 대비 키 백분위 알려줘", "이번 달 보육료 얼마야?"

## ⚠️ 주의

- 본 정보는 **참고용**이며 의료기관 진료를 대체하지 않습니다.
- 측정값은 HA Storage에만 저장되며 외부로 전송되지 않습니다.
- 본 통합은 인터넷 연결 없이 동작합니다 (모든 데이터 번들 포함).
