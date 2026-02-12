"""Conversation agent for OpenClaw."""

from __future__ import annotations

import json
import logging
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
    CONF_TIMEOUT,
    DEFAULT_MODEL,
    DEFAULT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class OpenClawConversationAgent(conversation.AbstractConversationAgent):
    """OpenClaw conversation agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self._base_url = entry.data[CONF_BASE_URL]
        self._api_key = entry.data[CONF_API_KEY]
        self._model = entry.data.get(CONF_MODEL, DEFAULT_MODEL)
        self._timeout = entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        self._conversations: dict[str, list[dict]] = {}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return "*"

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        conversation_id = user_input.conversation_id or ulid.ulid_now()

        # Get or create conversation history
        messages = self._conversations.get(conversation_id, [])

        # Add user message
        messages.append({"role": "user", "content": user_input.text})

        # Call OpenClaw
        try:
            response_text = await self._call_openclaw(messages)
        except Exception as err:
            _LOGGER.error("Error calling OpenClaw: %s", err)
            response_text = f"Désolé, erreur de communication avec OpenClaw: {err}"

        # Add assistant response to history
        messages.append({"role": "assistant", "content": response_text})

        # Keep conversation history (limit to last 20 messages)
        self._conversations[conversation_id] = messages[-20:]

        # Build response
        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech(response_text)

        return conversation.ConversationResult(
            response=response,
            conversation_id=conversation_id,
        )

    async def _call_openclaw(self, messages: list[dict]) -> str:
        """Call OpenClaw chat completions API."""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self._model,
            "messages": messages,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(
                        f"OpenClaw returned {resp.status}: {body}"
                    )

                data = await resp.json()
                choices = data.get("choices", [])
                if not choices:
                    raise RuntimeError("No response from OpenClaw")

                return choices[0]["message"]["content"]
