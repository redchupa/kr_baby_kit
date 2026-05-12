"""Coverage for scripts/check_care_tuition.py.

The script is a release-blocking gate, so the failure modes need their own
fixture-driven assertions — relying on the bundled JSON only exercises the
happy placeholder path.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_care_tuition.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "kr_baby_kit_scripts.check_care_tuition", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


check = _load_module()


def _write(tmp_path: Path, table: dict) -> Path:
    path = tmp_path / "care_tuition.json"
    path.write_text(json.dumps(table, ensure_ascii=False), encoding="utf-8")
    return path


def _good_tiers(values: dict[int, tuple[int, int, int]] | None = None) -> list[dict]:
    """Build a complete 0..6 tier list. `values` overrides per-class amounts."""
    spans = [
        (0, 11), (12, 23), (24, 35), (36, 47), (48, 59), (60, 71), (72, 83),
    ]
    tiers = []
    for cls, (lo, hi) in enumerate(spans):
        std, sub, share = (values or {}).get(cls, (300_000, 290_000, 10_000))
        tiers.append({
            "age_class": cls,
            "label_ko": f"만 {cls}세반",
            "label_en": f"Age {cls}",
            "age_months_min": lo,
            "age_months_max": hi,
            "standard_tuition": std,
            "government_subsidy": sub,
            "parent_share": share,
        })
    return tiers


def test_bundled_table_passes_default_mode(capsys):
    rc = check.main([])
    out = capsys.readouterr().out
    assert rc == 0
    # With the 2026 figures shipped, the script reports REAL mode.
    assert "REAL" in out


def test_bundled_table_passes_strict_mode(capsys):
    rc = check.main(["--strict"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "REAL" in out


def test_real_values_pass(tmp_path, capsys):
    path = _write(tmp_path, {
        "_meta": {"data_year": datetime.now().year, "currency": "KRW"},
        "tiers": _good_tiers(),
    })
    assert check.main(["--path", str(path)]) == 0
    assert "REAL" in capsys.readouterr().out


def test_missing_tier_class_fails(tmp_path, capsys):
    tiers = _good_tiers()
    tiers.pop()  # remove 만 6세반
    path = _write(tmp_path, {
        "_meta": {"data_year": datetime.now().year},
        "tiers": tiers,
    })
    assert check.main(["--path", str(path)]) == 1
    out = capsys.readouterr().out
    assert "age_class set" in out


def test_age_coverage_gap_fails(tmp_path, capsys):
    tiers = _good_tiers()
    tiers[1]["age_months_min"] = 13  # gap at month 12
    path = _write(tmp_path, {
        "_meta": {"data_year": datetime.now().year},
        "tiers": tiers,
    })
    assert check.main(["--path", str(path)]) == 1
    assert "age coverage gap or overlap" in capsys.readouterr().out


def test_subsidy_plus_share_must_equal_standard(tmp_path, capsys):
    tiers = _good_tiers({3: (300_000, 280_000, 10_000)})  # 280+10 != 300
    path = _write(tmp_path, {
        "_meta": {"data_year": datetime.now().year},
        "tiers": tiers,
    })
    assert check.main(["--path", str(path)]) == 1
    assert "!= standard_tuition" in capsys.readouterr().out


def test_zero_tier_in_real_year_fails(tmp_path, capsys):
    tiers = _good_tiers({4: (0, 0, 0)})  # forgot to fill 만 4세반
    path = _write(tmp_path, {
        "_meta": {"data_year": datetime.now().year},
        "tiers": tiers,
    })
    assert check.main(["--path", str(path)]) == 1
    assert "all-zero" in capsys.readouterr().out


def test_implausible_year_fails(tmp_path, capsys):
    path = _write(tmp_path, {
        "_meta": {"data_year": 1999},
        "tiers": _good_tiers(),
    })
    assert check.main(["--path", str(path)]) == 1
    assert "implausible" in capsys.readouterr().out


def test_missing_path_returns_two(tmp_path, capsys):
    rc = check.main(["--path", str(tmp_path / "does-not-exist.json")])
    assert rc == 2
