`custom_components/kr_baby_kit/data/care_tuition_kr.json` 의 `_meta.data_year` 가
**${DATA_YEAR}** 인데 현재 연도는 **${CURRENT_YEAR}** 입니다.

교육부 「${CURRENT_YEAR}년도 보육사업안내」가 발표됐는지 확인하고
`docs/release-checklist.md` §2 절차로 갱신해주세요.

### 출처 후보 (안정성 순)

1. KDI 경제정책정보센터 — https://eiec.kdi.re.kr/policy/materialView.do
2. 교육부 누리집 — https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=312
3. 중앙육아종합지원센터 — https://central.childcare.go.kr/ccef/community/data/DataSlPL.jsp?BBSGB=385

### 빠른 점검

```bash
python scripts/check_care_tuition.py --strict
python -m pytest tests/test_care_tuition.py
```

자동 알림: `.github/workflows/care_tuition_stale_check.yml` 매월 1일 실행.
이슈를 닫으려면 데이터 갱신 후 PR 머지 또는 수동 close.
