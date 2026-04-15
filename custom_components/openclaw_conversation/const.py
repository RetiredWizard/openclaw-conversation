"""Constants for OpenClaw Conversation."""

DOMAIN = "openclaw_conversation"

CONF_BASE_URL = "base_url"
CONF_API_KEY = "api_key"
CONF_MODEL = "model"
CONF_TIMEOUT = "timeout"
CONF_SYSTEM_PROMPT = "system_prompt"
CONF_STRIP_EMOJI = "strip_emoji"
CONF_SESSION_KEY = "session_key"

DEFAULT_MODEL = "openclaw:main"
DEFAULT_TIMEOUT = 0
DEFAULT_STRIP_EMOJI = True
DEFAULT_SESSION_KEY = "agent:main:homeassistant"
DEFAULT_BASE_URL = "http://127.0.0.1:18789"
DEFAULT_SYSTEM_PROMPT = (
    "You are a voice assistant. Keep responses short and conversational "
    "(1-3 sentences max). Do not use markdown, lists, or formatting. "
    "Speak naturally as if talking to someone."
)
