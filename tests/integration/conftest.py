"""Integration-test conftest.

The HA-test plugin's entrypoint loads `fcntl`, so we keep it disabled by default
(see root pytest.ini) and re-enable it here only on POSIX. Windows runs of
`tests/integration/` collect zero tests, which is intended.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    # HA's runner.py imports fcntl, so integration tests can't even be collected
    # on Windows. CI uses Ubuntu — this is the documented limitation.
    collect_ignore_glob = ["*.py"]
else:
    pytest_plugins = ["pytest_homeassistant_custom_component.plugins"]

    @pytest.fixture(autouse=True)
    def auto_enable_custom_integrations(enable_custom_integrations):
        yield

    @pytest.fixture(autouse=True)
    async def _bootstrap_homeassistant_component(hass):
        # Our integration's LLM tool registration calls
        # `homeassistant.components.homeassistant.exposed_entities.async_should_expose`,
        # which only works after the `homeassistant` core integration is set up.
        from homeassistant.setup import async_setup_component

        await async_setup_component(hass, "homeassistant", {})
        yield
