"""Pytest configuration.

The custom_component package imports `homeassistant`. When HA isn't installed
(unit-only job), we load the pure-Python modules as stubs under the
`custom_components.kr_baby_kit.*` namespace. When HA *is* installed (the
integration job), we add the project root to `sys.path` and let the real
package import normally, so `tests/integration/` can pull in `const`,
`sensor`, etc.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT_DIR = ROOT / "custom_components" / "kr_baby_kit"


def _homeassistant_available() -> bool:
    return importlib.util.find_spec("homeassistant") is not None


if _homeassistant_available():
    # Integration mode: make the real package importable and stop here.
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
else:
    # Unit-only mode: stub the package namespace and pre-load the modules
    # that don't depend on homeassistant.
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

    import importlib  # noqa: E402
    _growth = importlib.import_module("custom_components.kr_baby_kit.growth")
    _growth.__all__ = list(getattr(_growth, "__all__", [])) + ["_wfl_band", "_lookup"]
