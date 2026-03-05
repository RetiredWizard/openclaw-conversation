"""Conversation agent for OpenClaw."""

from __future__ import annotations

import json as json_mod
import logging
import time
from typing import Literal

import aiohttp

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.util import ulid

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_MODEL,
    CONF_SYSTEM_PROMPT,
    CONF_TIMEOUT,
    DEFAULT_MODEL,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class OpenClawConversationAgent(conversation.AbstractConversationAgent):
    """OpenClaw conversation agent."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, session: aiohttp.ClientSession
    ) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self._session = session
        self._base_url = entry.data[CONF_BASE_URL]
        self._api_key = entry.data[CONF_API_KEY]
        self._model = entry.options.get(CONF_MODEL, DEFAULT_MODEL)
        self._timeout = entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        self._system_prompt = entry.options.get(
            CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT
        )

    @property
    def attribution(self) -> dict[str, str]:
        """Return attribution."""
        return {"name": "Powered by OpenClaw", "url": "https://openclaw.ai"}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return "*"

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        conversation_id = user_input.conversation_id or ulid.ulid_now()

        try:
            start = time.monotonic()
            response_text = await self._call_openclaw(
                user_input.text, conversation_id
            )
            elapsed = time.monotonic() - start
            _LOGGER.info(
                "OpenClaw responded in %.1fs (%d chars)",
                elapsed,
                len(response_text),
            )
        except Exception as err:
            _LOGGER.error("Error calling OpenClaw: %s: %s", type(err).__name__, err)
            response_text = "Erreur de communication avec OpenClaw."

        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech(response_text)

        return conversation.ConversationResult(
            response=response,
            conversation_id=conversation_id,
        )

    async def _call_openclaw(
        self, text: str, conversation_id: str
    ) -> str:
        """Call OpenClaw chat completions API with streaming."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        api_messages = []
        if self._system_prompt:
            api_messages.append(
                {"role": "system", "content": self._system_prompt}
            )
        api_messages.append({"role": "user", "content": text})

        payload = {
            "model": self._model,
            "messages": api_messages,
            "stream": True,
            "user": conversation_id,
        }

        async with self._session.post(
            f"{self._base_url}/v1/chat/completions",
            json=payload,
            headers=headers,
        ) as resp:
            if resp.status != 200:
                body = await resp.text()
                raise RuntimeError(
                    f"OpenClaw returned {resp.status}: {body[:200]}"
                )

            # Read full response body then parse SSE lines
            raw = await resp.text()
            content = ""
            for line in raw.splitlines():
                line = line.strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json_mod.loads(data_str)
                    delta = chunk.get("choices", [{}])[0].get(
                        "delta", {}
                    )
                    content += delta.get("content", "")
                except (json_mod.JSONDecodeError, IndexError, KeyError):
                    continue

            # Fallback: try non-streaming response format
            if not content and raw:
                try:
                    data = json_mod.loads(raw)
                    choices = data.get("choices", [])
                    if choices:
                        content = choices[0]["message"]["content"]
                except (json_mod.JSONDecodeError, IndexError, KeyError):
                    pass

            if not content:
                raise RuntimeError(
                    f"No response from OpenClaw. Raw: {raw[:200]}"
                )

            return content
