"""OpenClaw Conversation integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .conversation import OpenClawConversationAgent

_LOGGER = logging.getLogger(__name__)

PLATFORMS = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenClaw Conversation from a config entry."""
    agent = OpenClawConversationAgent(hass, entry)

    conversation.async_set_agent(hass, entry, agent)

    _LOGGER.info("OpenClaw Conversation agent registered")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload OpenClaw Conversation."""
    conversation.async_unset_agent(hass, entry)
    return True
