"""Config flow for kr_baby_kit — registers one child per entry."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
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
)


_SEX_OPTIONS = [
    SelectOptionDict(value=SEX_MALE, label="남아 / Male"),
    SelectOptionDict(value=SEX_FEMALE, label="여아 / Female"),
]


class BabyKitConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow — one entry per child."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            name = (user_input.get(CONF_CHILD_NAME) or "").strip()
            bd = (user_input.get(CONF_CHILD_BIRTHDATE) or "").strip()
            sex = user_input.get(CONF_CHILD_SEX)
            if not name:
                errors[CONF_CHILD_NAME] = "required"
            try:
                bd_parsed = date.fromisoformat(bd)
                if bd_parsed > date.today():
                    errors[CONF_CHILD_BIRTHDATE] = "future_date"
            except ValueError:
                errors[CONF_CHILD_BIRTHDATE] = "invalid_date"
            if sex not in (SEX_MALE, SEX_FEMALE):
                errors[CONF_CHILD_SEX] = "required"

            if not errors:
                child_id = uuid.uuid4().hex[:12]
                await self.async_set_unique_id(child_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_CHILD_ID: child_id,
                        CONF_CHILD_NAME: name,
                        CONF_CHILD_BIRTHDATE: bd,
                        CONF_CHILD_SEX: sex,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_CHILD_NAME): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.TEXT)
                ),
                vol.Required(CONF_CHILD_BIRTHDATE): TextSelector(
                    TextSelectorConfig(type=TextSelectorType.DATE)
                ),
                vol.Required(CONF_CHILD_SEX): SelectSelector(
                    SelectSelectorConfig(
                        options=_SEX_OPTIONS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
