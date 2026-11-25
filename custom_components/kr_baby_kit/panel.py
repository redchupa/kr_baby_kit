"""Sidebar panel registration for kr_baby_kit."""
from __future__ import annotations

from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER

PANEL_URL_PATH = "kr_baby_kit"
STATIC_URL_PATH = "/kr_baby_kit_static"
FRONTEND_DIR = Path(__file__).parent / "frontend"
PANEL_VERSION = "0.15.1"


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the static JS bundle and Home Assistant sidebar panel once."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("_panel_registered"):
        return

    http = getattr(hass, "http", None)
    if http is None:
        # Headless unit/integration test harness without HTTP component.
        return

    try:
        from homeassistant.components import panel_custom
        from homeassistant.components.http import StaticPathConfig
    except Exception as err:  # pragma: no cover
        LOGGER.debug("Skipping sidebar panel registration: %s", err)
        return

    if not domain_data.get("_static_registered"):
        await http.async_register_static_paths(
            [
                StaticPathConfig(
                    STATIC_URL_PATH,
                    str(FRONTEND_DIR),
                    cache_headers=False,
                )
            ]
        )
        domain_data["_static_registered"] = True

    title = "Baby Kit"
    try:
        await panel_custom.async_register_panel(
            hass,
            webcomponent_name="kr-baby-kit-panel",
            frontend_url_path=PANEL_URL_PATH,
            sidebar_title=title,
            sidebar_icon="mdi:baby-face-outline",
            module_url=f"{STATIC_URL_PATH}/panel.js?v={PANEL_VERSION}",
            embed_iframe=False,
            require_admin=False,
            update=True,
        )
    except TypeError:
        # Compatibility with HA versions where `update` kwarg is absent.
        await panel_custom.async_register_panel(
            hass,
            webcomponent_name="kr-baby-kit-panel",
            frontend_url_path=PANEL_URL_PATH,
            sidebar_title=title,
            sidebar_icon="mdi:baby-face-outline",
            module_url=f"{STATIC_URL_PATH}/panel.js?v={PANEL_VERSION}",
            embed_iframe=False,
            require_admin=False,
        )
    domain_data["_panel_registered"] = True


def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar panel when the last child entry is unloaded."""
    domain_data = hass.data.get(DOMAIN) or {}
    has_children = any(
        isinstance(v, dict) and "coordinator" in v for v in domain_data.values()
    )
    if has_children or not domain_data.get("_panel_registered"):
        return
    try:
        from homeassistant.components import frontend

        frontend.async_remove_panel(hass, PANEL_URL_PATH)
    except Exception as err:  # pragma: no cover
        LOGGER.debug("Error removing sidebar panel: %s", err)
    domain_data["_panel_registered"] = False
