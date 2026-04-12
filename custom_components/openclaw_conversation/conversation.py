"""Conversation agent for OpenClaw."""

from __future__ import annotations

import asyncio
import json as json_mod
import logging
import re
import time
from typing import Any, Literal

import aiohttp

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.util import dt as dt_util
from homeassistant.util import ulid

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    CONF_MODEL,
    CONF_SESSION_KEY,
    CONF_STRIP_EMOJI,
    CONF_SYSTEM_PROMPT,
    CONF_TIMEOUT,
    DEFAULT_MODEL,
    DEFAULT_SESSION_KEY,
    DEFAULT_STRIP_EMOJI,
    DEFAULT_SYSTEM_PROMPT,
    DEFAULT_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

_EMOJI_PATTERN = re.compile("[\U00010000-\U0010ffff\u2600-\u26ff]", flags=re.UNICODE)


class OpenClawConversationAgent(conversation.AbstractConversationAgent):
    """OpenClaw conversation agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        config = {**entry.data, **entry.options}
        self._base_url = config[CONF_BASE_URL]
        self._api_key = config[CONF_API_KEY]
        self._model = entry.options.get(CONF_MODEL, DEFAULT_MODEL)
        self._timeout = self._normalize_timeout(
            config.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
        )
        self._system_prompt = entry.options.get(
            CONF_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT
        )
        self._strip_emoji = entry.options.get(CONF_STRIP_EMOJI, DEFAULT_STRIP_EMOJI)
        self._session_key = config.get(CONF_SESSION_KEY, DEFAULT_SESSION_KEY)

        # Ensure a consistent persistent session for HA voice use.
        self._initial_welcome_sent = False

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
        principal = self._resolve_principal(user_input)

        try:
            start = time.monotonic()
            response_text = await self._call_openclaw(
                user_input.text, conversation_id, principal
            )
            elapsed = time.monotonic() - start
            _LOGGER.info(
                "OpenClaw responded in %.1fs (%d chars)",
                elapsed,
                len(response_text),
            )
        except asyncio.TimeoutError:
            _LOGGER.error("OpenClaw request timed out after %ds", self._timeout)
            response_text = "OpenClaw request timed out."
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error calling OpenClaw: %s", err)
            response_text = "Network error calling OpenClaw."
        except asyncio.CancelledError:
            _LOGGER.warning("OpenClaw request was cancelled by Home Assistant")
            response_text = "OpenClaw request was cancelled by Home Assistant."
        except Exception as err:
            _LOGGER.error("Error calling OpenClaw: %s: %s", type(err).__name__, err)
            response_text = "Error calling OpenClaw."

        # Normalize temperature notation and strip colons
        response_text = response_text.replace("°F", "°Fahrenheit")
        response_text = response_text.replace(":", "")
        response_text = response_text.replace("*", "")
        response_text = response_text.replace("#", "")
        response_text = response_text.replace("OFF", "off")

        if self._strip_emoji:
            response_text = _EMOJI_PATTERN.sub("", response_text)

        response = intent.IntentResponse(language=user_input.language)
        response.async_set_speech(response_text)

        return conversation.ConversationResult(
            response=response,
            conversation_id=conversation_id,
        )

    def _resolve_principal(
        self, user_input: conversation.ConversationInput
    ) -> dict[str, str]:
        """Extract stable HA identity fields when available."""
        context = getattr(user_input, "context", None)
        user_id = getattr(context, "user_id", None) if context else None
        device_id = getattr(user_input, "device_id", None)
        return {
            "user_id": user_id or "",
            "device_id": device_id or "",
        }

    def _normalize_timeout(self, value: Any) -> int:
        """Normalize the configured timeout to a non-negative integer."""
        try:
            return max(int(value), 0)
        except (TypeError, ValueError):
            return DEFAULT_TIMEOUT

    def _build_timeout(self) -> aiohttp.ClientTimeout:
        """Build the request timeout configuration."""
        connect_timeout = 10
        if self._timeout <= 0:
            return aiohttp.ClientTimeout(
                total=None,
                connect=connect_timeout,
                sock_connect=connect_timeout,
                sock_read=None,
            )

        total_timeout = max(int(self._timeout), 1)
        return aiohttp.ClientTimeout(
            total=total_timeout,
            connect=min(connect_timeout, total_timeout),
            sock_connect=min(connect_timeout, total_timeout),
            sock_read=None,
        )

    async def _call_openclaw(
        self, text: str, conversation_id: str, principal: dict[str, str]
    ) -> str:
        """Call OpenClaw chat completions API with streaming."""
        # OpenClaw OpenAI-compatible endpoint is stateless by default.
        # Use a stable `user` and/or `x-openclaw-session-key` to keep session context.
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "x-openclaw-session-key": self._session_key,
            "x-openclaw-message-channel": "homeassistant",
        }

        api_messages = []

        # Global system prompt always at the top (if configured).
        if self._system_prompt:
            api_messages.append(
                {"role": "system", "content": self._system_prompt}
            )

        # One-time welcome/context priming on first HA startup.
        if not self._initial_welcome_sent:
            welcome_text = (
                "You should read the following files in your workspace folder"
                "for context and answers to who you are: SOUL.md, USER.md, AGENT.md and MEMORY.md."
            )
            text = welcome_text + " " + text
            self._initial_welcome_sent = True

        api_messages.append({"role": "user", "content": text})

        payload = {
            "model": self._model,
            "messages": api_messages,
            "stream": True,
            "user": "homeassistant",
            "language": self.hass.config.language,
            "local_date": dt_util.now().date().isoformat(),
            "conversation_id": conversation_id,
            "user_id": principal["user_id"],
            "device_id": principal["device_id"],
        }

        timeout = self._build_timeout()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{self._base_url}/v1/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(
                        f"OpenClaw returned {resp.status}: {body[:200]}"
                    )

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
