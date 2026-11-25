"""Authenticated HTTP media view for child avatars and diary photos.

Photos live under ``<config>/.storage/kr_baby_kit_media/<child_id>/<filename>``
(with legacy fallback to ``<config>/www/kr_baby_kit_media/`` for photos saved
in v0.13-v0.16) and are served through ``/api/kr_baby_kit/media/...`` with
``requires_auth = True``. The WebSocket overview signs URLs via Home
Assistant's ``async_sign_path`` so ``<img src="...">`` tags render natively
without exposing unauthenticated files under ``/local/``.
"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN, MEDIA_SUBDIR

MEDIA_API_PREFIX = f"/api/{DOMAIN}/media"
LEGACY_LOCAL_PREFIX = f"/local/{MEDIA_SUBDIR}"
_SIGN_TTL = timedelta(hours=6)

_EXT_CONTENT_TYPE: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def private_media_root(hass: HomeAssistant) -> Path:
    return Path(hass.config.path(".storage", MEDIA_SUBDIR))


def legacy_media_root(hass: HomeAssistant) -> Path:
    return Path(hass.config.path("www", MEDIA_SUBDIR))


def _is_safe_segment(seg: str, *, allow_dot: bool = False) -> bool:
    if not seg or seg in (".", ".."):
        return False
    for ch in seg:
        if ch.isalnum() or ch in ("_", "-"):
            continue
        if allow_dot and ch == ".":
            continue
        return False
    return True


def normalize_media_url(stored_url: str | None) -> str | None:
    """Convert legacy ``/local/kr_baby_kit_media/...`` URLs to the auth API path."""
    if not stored_url:
        return None
    if stored_url.startswith(f"{MEDIA_API_PREFIX}/"):
        return stored_url
    if stored_url.startswith(f"{LEGACY_LOCAL_PREFIX}/"):
        rel = stored_url[len(LEGACY_LOCAL_PREFIX) + 1 :]
        return f"{MEDIA_API_PREFIX}/{rel}"
    return stored_url


def sign_media_url(hass: HomeAssistant, stored_url: str | None) -> str | None:
    """Return a short-lived signed URL suitable for browser ``<img>`` tags."""
    api_url = normalize_media_url(stored_url)
    if not api_url or not api_url.startswith(f"{MEDIA_API_PREFIX}/"):
        return api_url
    try:
        from homeassistant.components.http.auth import async_sign_path

        return async_sign_path(hass, api_url, _SIGN_TTL)
    except Exception:
        # Headless unit-test harness without HTTP auth initialized.
        return api_url


class BabyKitMediaView(HomeAssistantView):
    """Serve child photos only to authenticated / signed requests."""

    url = f"{MEDIA_API_PREFIX}/{{child_id}}/{{filename}}"
    name = f"api:{DOMAIN}:media"
    requires_auth = True

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def get(
        self, request: web.Request, child_id: str, filename: str
    ) -> web.StreamResponse:
        if not _is_safe_segment(child_id) or not _is_safe_segment(
            filename, allow_dot=True
        ):
            raise web.HTTPBadRequest()

        ext = Path(filename).suffix.lower()
        content_type = _EXT_CONTENT_TYPE.get(ext)
        if content_type is None:
            raise web.HTTPNotFound()

        def _read_bytes() -> bytes | None:
            for root in (
                private_media_root(self._hass),
                legacy_media_root(self._hass),
            ):
                candidate = (root / child_id / filename).resolve()
                try:
                    candidate.relative_to(root.resolve())
                except ValueError:
                    continue
                if candidate.is_file():
                    return candidate.read_bytes()
            return None

        payload = await self._hass.async_add_executor_job(_read_bytes)
        if payload is None:
            raise web.HTTPNotFound()

        return web.Response(
            body=payload,
            content_type=content_type,
            headers={"Cache-Control": "private, max-age=3600"},
        )


def async_register_media_view(hass: HomeAssistant) -> None:
    """Register the authenticated media endpoint once per HA instance."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("_media_view_registered"):
        return
    http = getattr(hass, "http", None)
    if http is None:
        return
    http.register_view(BabyKitMediaView(hass))
    domain_data["_media_view_registered"] = True
