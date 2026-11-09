"""Unit tests for the storage merge logic.

We hit `async_append_measurement` without a real Home Assistant by stubbing
the Store: only the storage.py module is reloaded with a fake `Store` so the
test stays a pure-Python smoke test.
"""
from __future__ import annotations

import asyncio
import copy
import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
COMPONENT_DIR = ROOT / "custom_components" / "kr_baby_kit"


class _FakeStore:
    """Behaves like an on-disk Store: yields to the loop and returns copies,
    so missing locking in storage.py shows up as lost updates."""

    def __init__(self) -> None:
        self._data: dict | None = None

    async def async_load(self):
        await asyncio.sleep(0)
        return copy.deepcopy(self._data)

    async def async_save(self, data):
        await asyncio.sleep(0)
        self._data = copy.deepcopy(data)


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
    const.STORAGE_KEY_COMPLETIONS = "completions"
    const.STORAGE_VERSION = 1
    sys.modules["custom_components.kr_baby_kit.const"] = const

    spec = importlib.util.spec_from_file_location(
        "custom_components.kr_baby_kit.storage", COMPONENT_DIR / "storage.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["custom_components.kr_baby_kit.storage"] = module
    spec.loader.exec_module(module)
    return module


class _FakeHass:
    def __init__(self) -> None:
        self.data: dict = {}


HASS = _FakeHass()


@pytest.fixture()
def storage_mod():
    """Load a fresh storage module with shared fake Stores per test."""
    mod = _build_storage_module()
    shared_store = _FakeStore()
    completions_store = _FakeStore()
    mod._store = lambda hass: shared_store  # type: ignore[attr-defined]
    mod._completions_store = lambda hass: completions_store  # type: ignore[attr-defined]
    HASS.data.clear()
    return mod


@pytest.mark.asyncio
async def test_same_date_merges_fields(storage_mod) -> None:
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12", height=75.0
    )
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12", weight=9.0
    )
    records = await storage_mod.async_load_records(hass=HASS)
    assert len(records["c1"]) == 1
    assert records["c1"][0] == {
        "date": "2025-05-12",
        "height": 75.0,
        "weight": 9.0,
    }


@pytest.mark.asyncio
async def test_different_dates_create_separate_records(storage_mod) -> None:
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12", height=75.0
    )
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-06-12", height=76.0
    )
    records = await storage_mod.async_load_records(hass=HASS)
    assert [r["date"] for r in records["c1"]] == ["2025-05-12", "2025-06-12"]


@pytest.mark.asyncio
async def test_overwriting_same_field_same_date(storage_mod) -> None:
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12", height=75.0
    )
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12", height=75.5
    )
    records = await storage_mod.async_load_records(hass=HASS)
    assert len(records["c1"]) == 1
    assert records["c1"][0]["height"] == 75.5


@pytest.mark.asyncio
async def test_missing_value_raises(storage_mod) -> None:
    with pytest.raises(ValueError):
        await storage_mod.async_append_measurement(
            hass=HASS, child_id="c1", measurement_date="2025-05-12"
        )


@pytest.mark.asyncio
async def test_missing_child_id_raises(storage_mod) -> None:
    with pytest.raises(ValueError):
        await storage_mod.async_append_measurement(
            hass=HASS, child_id="", measurement_date="2025-05-12", height=75.0
        )


@pytest.mark.asyncio
async def test_invalid_date_raises(storage_mod) -> None:
    with pytest.raises(ValueError):
        await storage_mod.async_append_measurement(
            hass=HASS, child_id="c1", measurement_date="not-a-date", height=75.0
        )


@pytest.mark.asyncio
async def test_out_of_range_height_rejected_at_storage_layer(storage_mod) -> None:
    # storage.py is the last line of defence — even if a bad value bypasses
    # the service-call schema and the dashboard number entity, it must not
    # be persisted.
    with pytest.raises(ValueError, match="허용 범위"):
        await storage_mod.async_append_measurement(
            hass=HASS, child_id="c1", measurement_date="2025-05-12", height=999.0
        )


@pytest.mark.asyncio
async def test_negative_weight_rejected_at_storage_layer(storage_mod) -> None:
    with pytest.raises(ValueError, match="허용 범위"):
        await storage_mod.async_append_measurement(
            hass=HASS, child_id="c1", measurement_date="2025-05-12", weight=-3.0
        )


@pytest.mark.asyncio
async def test_non_numeric_height_rejected_at_storage_layer(storage_mod) -> None:
    with pytest.raises(ValueError, match="숫자로 읽지 못했습니다"):
        await storage_mod.async_append_measurement(
            hass=HASS, child_id="c1", measurement_date="2025-05-12", height="abc"
        )


@pytest.mark.asyncio
async def test_nan_height_rejected_at_storage_layer(storage_mod) -> None:
    with pytest.raises(ValueError, match="NaN"):
        await storage_mod.async_append_measurement(
            hass=HASS, child_id="c1", measurement_date="2025-05-12", height=float("nan")
        )


@pytest.mark.asyncio
async def test_concurrent_writes_do_not_lose_fields(storage_mod) -> None:
    """v0.9.0: height + weight set back-to-back must both persist."""
    import asyncio

    await asyncio.gather(
        storage_mod.async_append_measurement(
            hass=HASS, child_id="c1", measurement_date="2025-05-12", height=75.0
        ),
        storage_mod.async_append_measurement(
            hass=HASS, child_id="c1", measurement_date="2025-05-12", weight=9.0
        ),
        storage_mod.async_append_measurement(
            hass=HASS, child_id="c1", measurement_date="2025-05-12", head=45.0
        ),
    )
    records = await storage_mod.async_load_records(hass=HASS)
    assert records["c1"] == [
        {"date": "2025-05-12", "height": 75.0, "weight": 9.0, "head": 45.0}
    ]


@pytest.mark.asyncio
async def test_delete_whole_record(storage_mod) -> None:
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12", height=75.0
    )
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-06-12", height=76.0
    )
    result = await storage_mod.async_delete_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12"
    )
    assert result["removed"] == ["height"]
    assert result["remaining"] is None
    records = await storage_mod.async_get_child_records(HASS, "c1")
    assert [r["date"] for r in records] == ["2025-06-12"]


@pytest.mark.asyncio
async def test_delete_single_field_keeps_others(storage_mod) -> None:
    await storage_mod.async_append_measurement(
        hass=HASS,
        child_id="c1",
        measurement_date="2025-05-12",
        height=75.0,
        weight=9.0,
    )
    result = await storage_mod.async_delete_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12", kinds=["weight"]
    )
    assert result["removed"] == ["weight"]
    assert result["remaining"] == {"date": "2025-05-12", "height": 75.0}


@pytest.mark.asyncio
async def test_delete_last_field_drops_record(storage_mod) -> None:
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12", height=75.0
    )
    await storage_mod.async_delete_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12", kinds=["height"]
    )
    assert await storage_mod.async_get_child_records(HASS, "c1") == []


@pytest.mark.asyncio
async def test_delete_missing_date_raises(storage_mod) -> None:
    with pytest.raises(ValueError, match="측정 기록이 없습니다"):
        await storage_mod.async_delete_measurement(
            hass=HASS, child_id="c1", measurement_date="2025-01-01"
        )


@pytest.mark.asyncio
async def test_delete_unknown_kind_raises(storage_mod) -> None:
    with pytest.raises(ValueError, match="알 수 없는 측정 항목"):
        await storage_mod.async_delete_measurement(
            hass=HASS, child_id="c1", measurement_date="2025-01-01", kinds=["bmi"]
        )


@pytest.mark.asyncio
async def test_mark_and_unmark_completion(storage_mod) -> None:
    marked = await storage_mod.async_mark_completed(
        HASS, "c1", ["DTaP_1", "IPV_1"], "2020-05-15"
    )
    assert marked == {
        "DTaP_1": {"date": "2020-05-15"},
        "IPV_1": {"date": "2020-05-15"},
    }
    assert set(await storage_mod.async_get_child_completions(HASS, "c1")) == {
        "DTaP_1",
        "IPV_1",
    }
    removed = await storage_mod.async_unmark_completed(
        HASS, "c1", ["DTaP_1", "nope"]
    )
    assert removed == ["DTaP_1"]
    assert set(await storage_mod.async_get_child_completions(HASS, "c1")) == {"IPV_1"}


@pytest.mark.asyncio
async def test_mark_completion_rejects_bad_date(storage_mod) -> None:
    with pytest.raises(ValueError, match="완료일"):
        await storage_mod.async_mark_completed(HASS, "c1", ["DTaP_1"], "2020/05/15")


@pytest.mark.asyncio
async def test_remove_child_data_clears_both_stores(storage_mod) -> None:
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c1", measurement_date="2025-05-12", height=75.0
    )
    await storage_mod.async_append_measurement(
        hass=HASS, child_id="c2", measurement_date="2025-05-12", height=80.0
    )
    await storage_mod.async_mark_completed(HASS, "c1", ["BCG_1"], "2020-03-20")
    await storage_mod.async_remove_child_data(HASS, "c1")
    records = await storage_mod.async_load_records(HASS)
    assert "c1" not in records and "c2" in records
    assert await storage_mod.async_get_child_completions(HASS, "c1") == {}
