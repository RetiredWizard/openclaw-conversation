"""Config flow for OpenClaw Conversation."""

from __future__ import annotations

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_MODEL,
    CONF_STRIP_EMOJI,
    CONF_SYSTEM_PROMPT,
    CONF_TIMEOUT,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_STRIP_EMOJI,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TIMEOUT,
    DOMAIN,
)


class OpenClawConversationConfigFlow(
    config_entries.ConfigFlow, domain=DOMAIN
):
    """Handle a config flow for OpenClaw Conversation."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OpenClawOptionsFlowHandler:
        """Get the options flow handler."""
        return OpenClawOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            api_key = user_input[CONF_API_KEY]

            try:
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "model": user_input.get(CONF_MODEL, DEFAULT_MODEL),
                        "messages": [
                            {"role": "user", "content": "ping"}
                        ],
                    }
                    async with session.post(
                        f"{base_url}/v1/chat/completions",
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status == 401:
                            errors["base"] = "invalid_auth"
                        elif resp.status == 405:
                            errors["base"] = "endpoint_disabled"
                        elif resp.status not in (200,):
                            errors["base"] = "cannot_connect"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"

            if not errors:
                name = user_input.get(CONF_NAME, "OpenClaw")
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_API_KEY: api_key,
                        CONF_MODEL: user_input.get(
                            CONF_MODEL, DEFAULT_MODEL
                        ),
                        CONF_TIMEOUT: user_input.get(
                            CONF_TIMEOUT, DEFAULT_TIMEOUT
                        ),
                        CONF_SYSTEM_PROMPT: user_input.get(
                            CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT
                        ),
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_NAME, default="OpenClaw"
                    ): str,
                    vol.Required(
                        CONF_BASE_URL, default=DEFAULT_BASE_URL
                    ): str,
                    vol.Required(CONF_API_KEY): str,
                    vol.Optional(
                        CONF_MODEL, default=DEFAULT_MODEL
                    ): str,
                    vol.Optional(
                        CONF_TIMEOUT, default=DEFAULT_TIMEOUT
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_SYSTEM_PROMPT, default=DEFAULT_SYSTEM_PROMPT
                    ): str,
                }
            ),
            errors=errors,
        )


class OpenClawOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options for OpenClaw Conversation."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MODEL,
                        default=self.config_entry.options.get(
                            CONF_MODEL,
                            self.config_entry.data.get(
                                CONF_MODEL, DEFAULT_MODEL
                            ),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_TIMEOUT,
                        default=self.config_entry.options.get(
                            CONF_TIMEOUT,
                            self.config_entry.data.get(
                                CONF_TIMEOUT, DEFAULT_TIMEOUT
                            ),
                        ),
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_SYSTEM_PROMPT,
                        default=self.config_entry.options.get(
                            CONF_SYSTEM_PROMPT,
                            self.config_entry.data.get(
                                CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT
                            ),
                        ),
                    ): str,
                    vol.Optional(
                        CONF_STRIP_EMOJI,
                        default=self.config_entry.options.get(
                            CONF_STRIP_EMOJI, DEFAULT_STRIP_EMOJI
                        ),
                    ): bool,
                }
            ),
        )
