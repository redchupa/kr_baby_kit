# Claude 세션 부트스트랩 — kr_baby_kit

> 이 파일은 새 Claude Code 세션이 이 프로젝트 폴더를 열 때 자동으로 읽는 컨텍스트입니다.

## 🚨 보안 가드 최강 — 영유아 데이터 프로젝트

레포 어디에도 다음을 평문으로 포함하지 말 것:
- **자녀 실명** (`하린`, `우하린`, `WooRin`), 출생일, 성별
- 본인 자녀의 실제 키·몸무게·머리둘레 측정값 (fixture에도 X)
- 어린이집명, 어린이집 주소
- 본인 가족 실명
- 본인 HA URL, IP, 도메인
- 의료기관·소아과 의사명·실제 검진 일자

대신: `child_a`, `child_b`, 생년월일 `2020-03-15`, 합성 측정값.

**예외 (의도적 공개)**: 후원 메타 (HA device entry + README)

## 프로젝트 한 줄

영유아 성장곡선·예방접종·검진 일정을 HA 센서/캘린더로 노출하는 HACS 통합. 질병관리청/NIP 공공 데이터 기반.

## 작업 시작 시

1. **`PLAN.md` 정독** — §7 자녀 데이터 가드, §8 자산 참조
2. **`../MASTER_PLAN.md` 정독** — 공통 규칙
3. **`../kr_component_kit/custom_components/kr_component_kit/`** 패턴 참고
4. 현재 마일스톤 확인 (M0/M1/M2 완료, M3 옵션 기능만 남음)

## 데이터 소스 (모두 무료·공개)

- 질병관리청 소아청소년 성장도표 (2017년판 등)
- NIP 표준 예방접종 일정 (질병관리청)
- 보건복지부 영유아 검진 일정
- 공공데이터포털 보육료 (옵션, data.go.kr 무료 키)

→ 모든 출처 URL과 라이선스는 `docs/data-sources.md`에 명기.

## 코드 원칙

- Python 3.12+, HA custom_component 표준
- Config Flow로 자녀 다중 등록
- 측정 기록은 HA Storage(암호화)에 저장
- AI 호출 인라인 유지
- 의학·진단 책임 회피 면책 명시

## 본인 자산 (재활용 워크플로)

PLAN.md §8 참고. `kr_component_kit`의 Config Flow + 캘린더 + LLM tool 패턴을 그대로 차용. 본인 자녀 데이터·가족 메모는 **참조 X**.

## 발행 전 체크리스트

```bash
grep -rE "하린|우하린|WooRin|redchupa|jerry|예린|제리|192\.168\.|ha\.redchupa|2024-..-..|harin-" . --exclude-dir=__pycache__
```

자녀·본인 정보 0건 확인 후 커밋·릴리스.

## 다음 단계

PLAN.md §10 "다음 세션 시작 프롬프트" 를 첫 메시지로 사용.
