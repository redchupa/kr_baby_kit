"""Unit tests for the storage merge logic.

We hit `async_append_measurement` without a real Home Assistant by stubbing
the Store: only the storage.py module is reloaded with a fake `Store` so the
test stays a pure-Python smoke test.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
COMPONENT_DIR = ROOT / "custom_components" / "kr_baby_kit"


class _FakeStore:
    def __init__(self) -> None:
        self._data: dict | None = None

    async def async_load(self):
        return self._data

    async def async_save(self, data):
        self._data = data


def _build_storage_module() -> types.ModuleType:
    """Load storage.py with stubbed HA imports."""
    # Stub homeassistant.helpers.storage.Store
    fake_store_module = types.ModuleType("homeassistant.helpers.storage")
    fake_store_module.Store = lambda hass, version, key: _FakeStore()
    sys.modules["homeassistant"] = types.ModuleType("homeassistant")
    sys.modules["homeassistant.core"] = types.ModuleType("homeassistant.core")
    sys.modules["homeassistant.core"].HomeAssistant = object
    sys.modules["homeassistant.helpers"] = types.ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers.storage"] = fake_store_module

    # Stub const (storage imports a few symbols)
    const = types.ModuleType("custom_components.kr_baby_kit.const")
    const.DOMAIN = "kr_baby_kit"
    const.MEASUREMENT_KINDS = ["height", "weight", "head", "bmi"]
    const.STORAGE_KEY_RECORDS = "records"
    const.STORAGE_VERSION = 1
    sys.modules["custom_components.kr_baby_kit.const"] = const

    spec = importlib.util.spec_from_file_location(
        "custom_components.kr_baby_kit.storage", COMPONENT_DIR / "storage.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["custom_components.kr_baby_kit.storage"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def storage_mod():
    """Load a fresh storage module with a single shared fake Store per test."""
    mod = _build_storage_module()
    shared_store = _FakeStore()
    mod._store = lambda hass: shared_store  # type: ignore[attr-defined]
    return mod


@pytest.mark.asyncio
async def test_same_date_merges_fields(storage_mod) -> None:
    await storage_mod.async_append_measurement(
        hass=None, child_id="c1", measurement_date="2025-05-12", height=75.0
    )
    await storage_mod.async_append_measurement(
        hass=None, child_id="c1", measurement_date="2025-05-12", weight=9.0
    )
    records = await storage_mod.async_load_records(hass=None)
    assert len(records["c1"]) == 1
    assert records["c1"][0] == {
        "date": "2025-05-12",
        "height": 75.0,
        "weight": 9.0,
    }


@pytest.mark.asyncio
async def test_different_dates_create_separate_records(storage_mod) -> None:
    await storage_mod.async_append_measurement(
        hass=None, child_id="c1", measurement_date="2025-05-12", height=75.0
    )
    await storage_mod.async_append_measurement(
        hass=None, child_id="c1", measurement_date="2025-06-12", height=76.0
    )
    records = await storage_mod.async_load_records(hass=None)
    assert [r["date"] for r in records["c1"]] == ["2025-05-12", "2025-06-12"]


@pytest.mark.asyncio
async def test_overwriting_same_field_same_date(storage_mod) -> None:
    await storage_mod.async_append_measurement(
        hass=None, child_id="c1", measurement_date="2025-05-12", height=75.0
    )
    await storage_mod.async_append_measurement(
        hass=None, child_id="c1", measurement_date="2025-05-12", height=75.5
    )
    records = await storage_mod.async_load_records(hass=None)
    assert len(records["c1"]) == 1
    assert records["c1"][0]["height"] == 75.5


@pytest.mark.asyncio
async def test_missing_value_raises(storage_mod) -> None:
    with pytest.raises(ValueError):
        await storage_mod.async_append_measurement(
            hass=None, child_id="c1", measurement_date="2025-05-12"
        )


@pytest.mark.asyncio
async def test_missing_child_id_raises(storage_mod) -> None:
    with pytest.raises(ValueError):
        await storage_mod.async_append_measurement(
            hass=None, child_id="", measurement_date="2025-05-12", height=75.0
        )


@pytest.mark.asyncio
async def test_invalid_date_raises(storage_mod) -> None:
    with pytest.raises(ValueError):
        await storage_mod.async_append_measurement(
            hass=None, child_id="c1", measurement_date="not-a-date", height=75.0
        )


@pytest.mark.asyncio
async def test_out_of_range_height_rejected_at_storage_layer(storage_mod) -> None:
    # storage.py is the last line of defence — even if a bad value bypasses
    # the service-call schema and the dashboard number entity, it must not
    # be persisted.
    with pytest.raises(ValueError, match="허용 범위"):
        await storage_mod.async_append_measurement(
            hass=None, child_id="c1", measurement_date="2025-05-12", height=999.0
        )


@pytest.mark.asyncio
async def test_negative_weight_rejected_at_storage_layer(storage_mod) -> None:
    with pytest.raises(ValueError, match="허용 범위"):
        await storage_mod.async_append_measurement(
            hass=None, child_id="c1", measurement_date="2025-05-12", weight=-3.0
        )


@pytest.mark.asyncio
async def test_non_numeric_height_rejected_at_storage_layer(storage_mod) -> None:
    with pytest.raises(ValueError, match="숫자로 읽지 못했습니다"):
        await storage_mod.async_append_measurement(
            hass=None, child_id="c1", measurement_date="2025-05-12", height="abc"
        )


@pytest.mark.asyncio
async def test_nan_height_rejected_at_storage_layer(storage_mod) -> None:
    with pytest.raises(ValueError, match="NaN"):
        await storage_mod.async_append_measurement(
            hass=None, child_id="c1", measurement_date="2025-05-12", height=float("nan")
        )
