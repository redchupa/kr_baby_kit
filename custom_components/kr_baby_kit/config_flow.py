"""Config flow for kr_baby_kit — registers one child per entry.

The options flow (통합 → 구성) lets parents fix the child's name, birthdate,
or sex after registration. ``child_id`` never changes, so measurement records
and completion marks survive the edit; the entry reloads so every schedule
and percentile is recomputed against the new values.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_CHILD_BIRTHDATE,
    CONF_CHILD_ID,
    CONF_CHILD_NAME,
    CONF_CHILD_SEX,
    DOMAIN,
    SEX_FEMALE,
    SEX_MALE,
    TZ_ASIA_SEOUL,
)


_SEX_OPTIONS = [
    SelectOptionDict(value=SEX_MALE, label="남아 / Male"),
    SelectOptionDict(value=SEX_FEMALE, label="여아 / Female"),
]


def _child_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}

    def _key(name: str) -> vol.Required:
        if name in d:
            return vol.Required(name, default=d[name])
        return vol.Required(name)

    return vol.Schema(
        {
            _key(CONF_CHILD_NAME): TextSelector(
                TextSelectorConfig(type=TextSelectorType.TEXT)
            ),
            _key(CONF_CHILD_BIRTHDATE): TextSelector(
                TextSelectorConfig(type=TextSelectorType.DATE)
            ),
            _key(CONF_CHILD_SEX): SelectSelector(
                SelectSelectorConfig(
                    options=_SEX_OPTIONS,
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
        }
    )


def _validate_child(
    user_input: dict[str, Any],
) -> tuple[dict[str, str], dict[str, str]]:
    """Return (cleaned values, errors)."""
    errors: dict[str, str] = {}
    name = (user_input.get(CONF_CHILD_NAME) or "").strip()
    bd = (user_input.get(CONF_CHILD_BIRTHDATE) or "").strip()
    sex = user_input.get(CONF_CHILD_SEX)
    if not name:
        errors[CONF_CHILD_NAME] = "required"
    try:
        if date.fromisoformat(bd) > datetime.now(TZ_ASIA_SEOUL).date():
            errors[CONF_CHILD_BIRTHDATE] = "future_date"
    except ValueError:
        errors[CONF_CHILD_BIRTHDATE] = "invalid_date"
    if sex not in (SEX_MALE, SEX_FEMALE):
        errors[CONF_CHILD_SEX] = "required"
    return (
        {CONF_CHILD_NAME: name, CONF_CHILD_BIRTHDATE: bd, CONF_CHILD_SEX: sex},
        errors,
    )


class BabyKitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow — one entry per child."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "BabyKitOptionsFlow":
        return BabyKitOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            values, errors = _validate_child(user_input)
            if not errors:
                child_id = uuid.uuid4().hex[:12]
                await self.async_set_unique_id(child_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=values[CONF_CHILD_NAME],
                    data={CONF_CHILD_ID: child_id, **values},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_child_schema(user_input),
            errors=errors,
        )


class BabyKitOptionsFlow(config_entries.OptionsFlow):
    """Edit name / birthdate / sex of an existing child."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        entry = self.config_entry
        errors: dict[str, str] = {}
        if user_input is not None:
            values, errors = _validate_child(user_input)
            if not errors:
                new_data = {**entry.data, **values}
                if new_data != dict(entry.data):
                    # The update listener in __init__ reloads the entry.
                    self.hass.config_entries.async_update_entry(
                        entry, data=new_data, title=values[CONF_CHILD_NAME]
                    )
                return self.async_create_entry(title="", data=dict(entry.options))

        defaults = user_input or {
            CONF_CHILD_NAME: entry.data.get(CONF_CHILD_NAME, ""),
            CONF_CHILD_BIRTHDATE: entry.data.get(CONF_CHILD_BIRTHDATE, ""),
            CONF_CHILD_SEX: entry.data.get(CONF_CHILD_SEX, SEX_MALE),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=_child_schema(defaults),
            errors=errors,
        )
