"""Smoke test for scripts/build_growth_chart.py."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = ROOT / "scripts" / "build_growth_chart.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("build_growth_chart", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_growth_chart"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_build_chart_from_synthetic_csv(tmp_path: Path) -> None:
    script = _load_script()

    csv_file = tmp_path / "synthetic.csv"
    csv_file.write_text(
        "sex,kind,age_months,L,M,S\n"
        "male,height,0,1.0,50.0,0.038\n"
        "male,height,12,1.0,75.0,0.034\n"
        "female,weight,0,0.38,3.2,0.142\n",
        encoding="utf-8",
    )

    out = tmp_path / "out.json"
    rc = script.main([str(csv_file), "--out", str(out)])
    assert rc == 0

    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["samples"]["male"]["height"][0]["M"] == 50.0
    assert data["samples"]["female"]["weight"][0]["L"] == pytest.approx(0.38)


def test_build_chart_rejects_bad_columns(tmp_path: Path) -> None:
    script = _load_script()
    bad = tmp_path / "bad.csv"
    bad.write_text("sex,kind,age_months,M\nmale,height,0,50\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        script.main([str(bad), "--out", str(tmp_path / "out.json")])
