# Release checklist — kr_baby_kit

> 본 레포는 다음 두 가지를 의도적으로 **placeholder**로 출시합니다:
>
> 1. **`@your-github-username`** (보안 가드 — `manifest.json`, `README.md`, 설치 문서, LICENSE)
> 2. **보육료 데이터 zero 값** (`data/care_tuition_kr.json`)
>
> 이 체크리스트는 사용자가 본인 fork를 release할 때 두 placeholder를
> 안전하게 치환하고 검증하는 절차입니다.

---

## 0. 사전

```bash
git checkout -b release/v<version>
```

## 1. GitHub username placeholder 치환 (모든 fork 공통)

다음 4개 파일에서 `your-github-username`을 본인 GitHub 핸들로 일괄 치환:

```bash
git grep -l "your-github-username"
# Expected matches (정확히 4개):
#   custom_components/kr_baby_kit/manifest.json   (codeowners + documentation + issue_tracker)
#   README.md                                     (배지 3개 + 설치 URL 1개)
#   docs/installation-ko.md
#   docs/installation-en.md
```

PowerShell 일괄 치환 예시:

```powershell
$me = "<your-github-handle>"   # ← 본인 GitHub 핸들로 교체 후 따옴표만 남기기
Get-ChildItem -Recurse -Include "*.md","*.json" |
    ForEach-Object { (Get-Content $_ -Raw).Replace("your-github-username", $me) |
        Set-Content $_ -Encoding UTF8 -NoNewline }
```

검증:

```bash
git grep "your-github-username"   # → 결과 없어야 함
```

> ⚠️ 사용자 본인의 보안 가드에 따라 release 브랜치에서만 이 치환을 적용하고,
> `main` 브랜치는 placeholder 상태를 유지하는 워크플로를 권장합니다.
> CI(`test.yml`)의 privacy grep은 본인 핸들이 들어있어도 통과하지 않으므로
> release 브랜치는 그 grep을 우회하거나, 본인 핸들을 grep 화이트리스트에
> 추가해야 합니다.

## 2. 보육료 데이터 (매년 1월 갱신)

v0.4.0부터 「2026년도 보육사업안내」 실측 단가가 번들됩니다. 매년
1월 차년도 단가 발표 시 다음 절차:

### 출처 우선순위 (안정성 순)

1. **KDI 경제정책정보센터** (영구 보관, SSL 안정) — <https://eiec.kdi.re.kr/policy/materialView.do?num=275569> 또는 차년도 동등 게시물
2. **교육부 누리집** (1차 출처) — <https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=312>
3. **중앙육아종합지원센터** — <https://central.childcare.go.kr/ccef/community/data/DataSlPL.jsp?BBSGB=385>
4. 어린이집 정보공개포털: <https://info.childcare.go.kr/>
5. 지자체 자료실 미러 (대전·인천 등 — 현재 번들 source_url이 여기 해당)

### 갱신 절차

1. 위 1~3 출처에서 차년도 「보육사업안내 부록」 PDF 또는 개정사항 안내 입수.
2. `custom_components/kr_baby_kit/data/care_tuition_kr.json` 편집:
   - `_meta.data_year` → 해당 연도 (예: `2027`)
   - `_meta.source_url` → 위 출처 URL (KDI 영구보관 권장)
   - `_meta.publication_number` → 발간등록번호
   - `_meta.effective_from` → 해당 연도 1월 1일
   - 각 `tiers[].standard_tuition` / `government_subsidy` / `parent_share` 갱신
3. **단가가 전년 대비 동일하면** `_meta` 만 갱신해도 OK (tier 숫자 변경 없음).
4. **검증**:

   ```bash
   python scripts/check_care_tuition.py --strict
   ```

   기대 출력:

   ```
   care_tuition sanity check OK - 7 tiers, data_year=2027 (REAL).
   ```

   `--strict` 플래그는 placeholder 모드(`data_year == 0`)와 zero amount를 실패로
   취급합니다. 추가로:
   - 만 0~6세반 7개 tier 모두 존재
   - 월령 범위 `0..83` 빈틈 없이 커버
   - `parent_share + government_subsidy == standard_tuition` (차액 있다면 `_meta._note` 에 사유 기재)
5. `tests/test_care_tuition.py` 의 `data_year` assertion 을 차년도로 동기화.

### 자동 알림

`.github/workflows/care_tuition_stale_check.yml` 이 매월 1일 cron 으로
`_meta.data_year` 가 현재 연도보다 작으면 GitHub Issue 를 자동 생성합니다
(라벨 `data-stale`). 동일 라벨 이슈가 이미 열려있으면 중복 생성하지 않으니
사용자는 issue 알림만 보고 위 갱신 절차를 따르면 됩니다.

## 3. 로컬 검증

```bash
# 단위 테스트
python -m pytest -q --ignore=tests/integration

# 통합 테스트 (Linux 또는 WSL — HA test harness 필요)
python -m pytest -q tests/integration

# 코드 품질
python -m ruff check .

# 보안 grep — 본인 GitHub 핸들이 placeholder 자리에 들어갔는지 확인
# (main 브랜치는 0건이어야 하고, release 브랜치는 본인 핸들만 존재)
grep -rE "your-github-username" --exclude-dir=.git --exclude-dir=__pycache__ . || echo "ok"
```

## 4. CHANGELOG / version bump

- `custom_components/kr_baby_kit/manifest.json` → `"version": "<new>"` (PEP 440)
- `CHANGELOG.md` 상단에 새 버전 entry 추가 (Keep a Changelog 형식)
- 알파에서 정식으로 갈 때: `0.4.0a0` → `0.4.0`

## 5. CI 통과 확인

```bash
git push origin release/v<version>
```

- **hassfest** — manifest.json 구조 검증. `@<github-handle>` 형식만 보고
  실제 GitHub API 호출은 하지 않으므로, format이 valid한 핸들이면 통과합니다.
- **HACS validation** — `hacs.json` + `info.md` + `README.md` 존재 + 도메인 일치.
- **pytest 매트릭스** — Python 3.11/3.12/3.13.
- **privacy grep** — `.github/workflows/test.yml`의 패턴이 본인 핸들/도메인을
  잡지 않도록 확인. 잡힌다면 release 브랜치에서만 패턴 화이트리스트 또는
  `if: github.ref != 'refs/heads/release/*'` 조건 추가.

## 6. Git tag + GitHub Release

```bash
git tag -a v<version> -m "Release v<version> — <one-liner>"
git push origin v<version>
# Then on GitHub: Releases → Draft new release → pick the tag
```

릴리스 노트는 CHANGELOG의 해당 버전 섹션을 그대로 복사. HACS Custom
Repository 사용자에게 자동으로 노출됩니다.

## 7. HACS Custom Repository 안내 (해당 시)

- `hacs.json`의 `homeassistant`, `country`, `name` 필드 확인.
- 본 레포는 PLAN.md §M3에서 **HACS Default PR을 스킵** 결정: 한국 전용
  데이터 도메인이라 Custom Repository로만 배포합니다. 본인 정책을 바꾸려면
  먼저 `hacs/integration` 의 contribution 가이드를 확인하세요.

---

## 부록: placeholder 모드를 main에 유지하는 이유

- **GitHub username**: 본인의 보안 가드(`CLAUDE.md` §보안가드)가 본인
  실명·핸들 노출을 금지. main이 placeholder이면 fork 사용자나 다른
  부모도 본인 fork에 자기 username만 채워 사용 가능.
- **보육료 zero**: 매년 보건복지부 고시가 갱신되므로 영구 유효한 값이
  존재하지 않음. zero placeholder를 두면 잘못된 옛 수치를 노출할 위험이
  사라지고, 사용자가 갱신을 잊으면 sensor가 명시적으로 `Unknown`을
  반환하여 silent 실패를 방지.

두 placeholder 모두 `is_placeholder` 같은 명시적 신호로 surface합니다
(보육료) 또는 release 워크플로 1단계에서 강제로 치환됩니다 (username).
