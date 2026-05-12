"""Pytest configuration.

The custom_component package imports `homeassistant`, which is not installed in
the unit-test environment. We therefore load `growth.py` and `schedule.py` as
standalone modules and re-export them under the
`custom_components.kr_baby_kit.*` namespace expected by the tests.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT_DIR = ROOT / "custom_components" / "kr_baby_kit"


def _stub_package(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__path__ = []  # mark as package
    sys.modules[name] = mod
    return mod


_stub_package("custom_components")
_stub_package("custom_components.kr_baby_kit")


def _load(rel_name: str, file_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(rel_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[rel_name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)


_load("custom_components.kr_baby_kit.growth", COMPONENT_DIR / "growth.py")
_load("custom_components.kr_baby_kit.schedule", COMPONENT_DIR / "schedule.py")
_load("custom_components.kr_baby_kit.care_tuition", COMPONENT_DIR / "care_tuition.py")
_load("custom_components.kr_baby_kit.validation", COMPONENT_DIR / "validation.py")

# Re-export private helpers used by tests.
import importlib  # noqa: E402
_growth = importlib.import_module("custom_components.kr_baby_kit.growth")
_growth.__all__ = list(getattr(_growth, "__all__", [])) + ["_wfl_band", "_lookup"]
