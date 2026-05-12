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

## 2. 보육료 데이터 (v0.4.0a → v0.4.0 정식)

본 레포는 `_meta.data_year: 0` + 모든 amount `0`으로 출시됩니다. 정식 사용
전 다음을 수행:

1. 보건복지부 공식 발표 또는
   [어린이집 정보공개포털](https://info.childcare.go.kr/) 에서 해당 연도
   표준보육료 / 정부지원 보육료 / 본인부담금 확인.
2. `custom_components/kr_baby_kit/data/care_tuition_kr.json` 편집:
   - `_meta.data_year` → 해당 연도 (예: `2025`)
   - 각 `tiers[].standard_tuition` / `government_subsidy` / `parent_share` → 고시 금액 (단위 원)
3. **검증**:

   ```bash
   python scripts/check_care_tuition.py --strict
   ```

   기대 출력:

   ```
   care_tuition sanity check OK - 7 tiers, data_year=2025 (REAL).
   ```

   `--strict` 플래그는 placeholder 모드(`data_year == 0`)를 실패로
   취급하므로, 실 수치 정확성을 보장합니다. 추가로:
   - 만 0~6세반 7개 tier 모두 존재
   - 월령 범위 `0..83` 빈틈 없이 커버
   - `parent_share + government_subsidy == standard_tuition` (차액이 있다면 `_meta._note`에 사유 기재)

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
