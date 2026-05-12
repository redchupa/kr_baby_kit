# Data Sources / 데이터 출처

이 통합은 한국 공공 데이터만 사용합니다. 모든 출처와 라이선스는 아래와 같습니다.

## 1. 소아청소년 성장도표 (Growth Chart)

- **출처**: 질병관리청 (KDCA) · 대한소아청소년과학회 공동 — *2017 소아청소년 성장도표*
- **URL**:
  - 질병관리청 안내: <https://www.kdca.go.kr/kdca/5458/subview.do>
  - 개발 공지: <https://www.kdca.go.kr/board/board.es?mid=a20504000000&bid=0034&list_no=121891&act=view>
  - 공공데이터포털 (LMS 자료): <https://www.data.go.kr/data/15076588/fileData.do>
  - 영유아 LMS 기준 (국민건강보험공단, 2024년 갱신): <https://www.data.go.kr/data/15133061/fileData.do>
- **라이선스**: 공공누리 제1유형 (출처 표시) — 상업적 이용 및 변형 허용
- **사용 방식**: `custom_components/kr_baby_kit/data/growth_chart_kr.json` 으로 가공해 포함. WHO 권장 LMS 방식 (L=skewness, M=median, S=CV) 으로 백분위 계산.
- **버전**: 2017년판 (2024년 영유아 LMS 갱신 반영)
- **제한**: 0~18세. 19세 이상은 미지원.

### LMS 백분위 계산식

L≠0일 때:
```
Z = ((X / M) ^ L - 1) / (L × S)
```

L=0일 때:
```
Z = ln(X / M) / S
```

→ Z-score를 표준정규분포 누적함수로 변환하여 백분위 산출.

## 2. 표준 예방접종 일정 (National Immunization Program, NIP)

- **출처**: 질병관리청 예방접종도우미
- **URL**: <https://nip.kdca.go.kr/irhp/goMainInfo.do>
  - 어린이 국가예방접종사업 안내: <https://nip.kdca.go.kr/irhp/infm/goVcntInfo.do?menuLv=1&menuCd=131>
- **라이선스**: 공공누리 제1유형
- **사용 방식**: `data/nip_schedule.json` — 백신별 권장 접종 월령 목록.
- **포함 백신** (어린이 국가예방접종):
  BCG(피내), HepB, DTaP, IPV, Hib, PCV, RV, MMR, VAR, HepA, IJEV/LJEV, HPV, IIV
- **갱신 주기**: 매년 1~2월 질병관리청 갱신 시 본 레포 JSON 동기화 (CI에 일정 점검 작업 추가 예정).

## 3. 영유아 건강검진 일정 (보건복지부 표준 7회 검진)

- **출처**: 보건복지부·국민건강보험공단 영유아 건강검진
- **URL**: <https://www.nhis.or.kr/nhis/healthin/wbhabb02100m01.do>
- **라이선스**: 공공 정보 (공공누리 제1유형)
- **사용 방식**: `data/health_checkup_schedule.json` — 7회 표준 검진 시기 (4-6개월, 9-12개월, 18-24개월, 30-36개월, 42-48개월, 54-60개월, 66-71개월).
- **참고**: 시기는 권장 범위이며, 의료기관 예약은 별도.

## 4. 표준보육료 (Standard Childcare Tuition)

- **출처 (2026)**: 교육부 「2026년도 보육사업안내 부록 2」 — 영유아보육료 지원금액 (부록 96쪽)
  - 발간등록번호: 11-1342000-100026-10
  - 시행: 2026년 1월 1일
- **URL** (안정성 순):
  1. **KDI 경제정책정보센터** (영구 보관, SSL 안정): <https://eiec.kdi.re.kr/policy/materialView.do?num=275569> — 2026년도 개정사항 안내
  2. **교육부 누리집** (1차 출처, 게시판 URL 변동 가능): <https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=312> (정책 > 영유아 보육·교육)
  3. **중앙육아종합지원센터 자료실**: <https://central.childcare.go.kr/ccef/community/data/DataSlPL.jsp?BBSGB=385>
  4. **어린이집 정보공개포털**: <https://info.childcare.go.kr/>
  5. 대전광역시 자료실 미러 (현재 번들 source_url): <https://www.daejeon.go.kr/data/drh/sub05/2026_data_02.pdf>
- **정책 변경 안내 (유보통합)**: 2026년부터 어린이집·유치원 보육·교육 업무가 보건복지부에서 교육부로 이관되었습니다. 2025년 이전 자료는 보건복지부 고시(`www.mohw.go.kr`)에서, 2026년 이후 자료는 교육부 누리집에서 확인하십시오.
- **라이선스**: 공공누리 제1유형 (출처 표시)
- **사용 방식**: `data/care_tuition_kr.json` — 만 0~6세반 7개 연령구간에 대해 표준보육료 / 정부지원금 / 본인부담금(KRW)을 보유.
- **번들 데이터 (2026)**:
  | 연령 | 표준보육료 | 정부지원금 | 본인부담금 |
  |---|---|---|---|
  | 만 0세반 | 584,000 | 584,000 | 0 |
  | 만 1세반 | 515,000 | 515,000 | 0 |
  | 만 2세반 | 426,000 | 426,000 | 0 |
  | 만 3~5세반 (누리공통과정) | 280,000 | 280,000 | 0 |
  | 만 6세반 (취학유예 시) | 280,000 | 280,000 | 0 |

  *모든 연령 종일반(기본보육) 기준. 무상보육 대상이므로 본인부담금 0원. 연장보육료·24시간·다문화·장애아 가산은 미포함.*
- **갱신 주기**: 매년 1월 (교육부 차년도 보육사업안내 발표 직후 — 통상 12월 말 게시).
- **자동 알림**: `.github/workflows/care_tuition_stale_check.yml` 이 매월 1일 cron 으로 `_meta.data_year` 가 현재 연도 미만이면 GitHub Issue를 자동 생성합니다 (라벨 `data-stale`). 동일 라벨 issue가 이미 열려있으면 중복 생성하지 않습니다.
- **갱신 절차**:
  1. 위 URL 우선순위에 따라 차년도 「보육사업안내 부록」 PDF 또는 KDI 개정사항 안내 입수
  2. "❙보육료 지원금액❙" 표 7행 (만 0~6세반) 확인
  3. `data/care_tuition_kr.json` 의 `_meta.data_year`, `_meta.source_url`, `_meta.publication_number`, `_meta.effective_from` 갱신 + 각 tier의 3개 숫자 필드 교체
  4. **단가가 전년과 동일하면** `_meta` 메타데이터만 갱신해도 OK (tier 숫자 그대로)
  5. `python scripts/check_care_tuition.py --strict` 통과 확인
  6. `python -m pytest tests/test_care_tuition.py` 의 `data_year` assertion 도 차년도로 동기화
  7. release-checklist.md §1~§6 워크플로로 release/vX.Y.Z 브랜치 + tag publish

---

## ⚠️ 의학적 면책 (Medical Disclaimer)

> 본 통합이 제공하는 모든 성장 백분위·예방접종·검진 정보는 **참고용**이며, 의학적 진단·처방·치료를 대체하지 않습니다.
> 자녀의 성장·건강 상태는 반드시 소아청소년과 전문의의 진료를 통해 평가하시기 바랍니다.
> 본 소프트웨어는 정보 표시 도구이며, 사용자가 본 정보를 근거로 한 의학적 결정에 대한 책임을 지지 않습니다.

> All growth percentile, immunization, and health checkup information provided by this integration is **for reference only** and does not replace medical diagnosis, prescription, or treatment.
> The growth and health status of children must be evaluated by a pediatrician.
> This software is an information display tool, and the authors assume no liability for medical decisions made based on this information.

---

## 출처 표시 (Attribution)

본 데이터를 활용하는 모든 UI / API / 자동화 노출 지점에는 다음 출처 표시가 포함됩니다 (공공누리 제1유형 준수):

- 성장도표: `질병관리청 2017 소아청소년 성장도표`
- 예방접종: `질병관리청 표준 예방접종 일정`
- 영유아 검진: `보건복지부 영유아 건강검진`
- 보육료: `교육부 「YYYY년도 보육사업안내」 부록 — 영유아보육료 지원금액` (2026년부터 유보통합으로 보건복지부 → 교육부)
