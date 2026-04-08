# OpenClaw Conversation for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange?style=flat-square)](https://hacs.xyz/)
[![GitHub Release](https://img.shields.io/github/v/release/nicolasglg/openclaw-conversation?style=flat-square)](https://github.com/nicolasglg/openclaw-conversation/releases)
[![License](https://img.shields.io/github/license/nicolasglg/openclaw-conversation?style=flat-square)](LICENSE)
[![Buy Me A Beer](https://img.shields.io/badge/Buy%20Me%20A%20Beer-support-yellow?style=flat-square&logo=buy-me-a-coffee)](https://buymeacoffee.com/nicolasglg)

**Turn your [OpenClaw](https://openclaw.ai) agent into a Home Assistant voice assistant.**

This fork keeps the standard `POST /v1/chat/completions` integration flow, but also forwards stable Home Assistant identity metadata when available:

- `conversation_id`
- `user_id`
- `device_id`
- `language`
- `local_date`

The goal is to let OpenClaw apply its own routing, session, and context policy with better identity continuity, without breaking existing installations that already use the stock chat completions endpoint.

Say a wake word, ask a question, get a spoken answer — powered by your own OpenClaw agent with all its tools, memory, and personality.

```
"Hey Nabu" → Whisper STT → OpenClaw Agent → Piper TTS → Speaker
```

## What you get

- Your full OpenClaw agent as a HA conversation agent
- Voice control through HA Voice PE, phone app, or browser
- Works with any STT/TTS engine (Whisper, Piper, HA Cloud...)
- Simple setup: just point it at your OpenClaw Gateway
- Stable HA identity metadata forwarding for backends that support identity-aware routing or session handling

## What this fork changes

- Keeps using the standard OpenClaw endpoint: `/v1/chat/completions`
- Preserves backward compatibility for existing users
- Forwards `conversation_id`, `user_id`, `device_id`, `language`, and `local_date` as extra request fields
- Does not force any new session policy in the Home Assistant plugin
- Lets the OpenClaw backend decide how identity continuity should be used

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the 3 dots menu > **Custom repositories**
3. Add `nicolasglg/openclaw-conversation` as **Integration**
4. Search for and install **OpenClaw Conversation**
5. Restart Home Assistant
6. Go to **Settings** > **Integrations** > **Add Integration** > **OpenClaw Conversation**

### Manual

Copy `custom_components/openclaw_conversation` into your HA `config/custom_components/` directory and restart.

## Configuration

### 1. Add the integration

**Settings > Devices & Services > Add Integration > OpenClaw Conversation**

| Field | Value |
|-------|-------|
| Name | Display name (e.g. "OpenClaw") |
| Gateway URL | `http://<gateway-ip>:<port>` (e.g. `http://192.168.1.100:18789`) |
| API Token | Your gateway auth token |
| Model | `openclaw` (default) |
| Timeout | `30` seconds |

### 2. Set up a Voice Assistant

**Settings > Voice Assistants** > create or edit an assistant:

- **Conversation agent**: select **OpenClaw**
- **Speech-to-Text**: Whisper, Faster Whisper, or HA Cloud
- **Text-to-Speech**: Piper, Google Translate, or HA Cloud
- **Wake word**: e.g. "Ok Nabu" via openWakeWord

### 3. Assign to a voice device

For HA Voice PE or other satellites: set **Preferred Assistant** to your OpenClaw assistant in the device settings.

### 4. Test it

Say the wake word and speak, or use **Voice Assistants > Start a conversation** to test via text.

## Prerequisites

- [OpenClaw Gateway](https://openclaw.ai) with Chat Completions endpoint enabled
- Home Assistant 2024.1+
- HACS installed

### Enable Chat Completions on your gateway

Add this to your `openclaw.json` inside the `gateway` block:

```json
{
  "gateway": {
    "http": {
      "endpoints": {
        "chatCompletions": { "enabled": true }
      }
    }
  }
}
```

Restart your gateway after the change.

### Identity metadata

This fork still uses the normal chat completions endpoint, but it also forwards extra Home Assistant request metadata when available:

- `conversation_id`
- `user_id`
- `device_id`
- `language`
- `local_date`

OpenClaw backends that understand these fields can use them for routing or session continuity. Backends that ignore unknown fields should continue to work as before.

### Network notes

- HA must reach your OpenClaw Gateway over HTTP
- If they're on different machines, use the gateway's LAN IP (not `127.0.0.1`)
- Open port `18789` (default) if needed
- Docker users: `127.0.0.1` refers to the container, use the host's LAN IP instead

## STT / TTS recommendations

### Speech-to-Text

| Engine | Speed | Notes |
|--------|-------|-------|
| **HA Cloud** | Fast | Requires subscription |
| **Faster Whisper** (Wyoming) | Good | Separate machine with decent CPU/GPU |
| **Whisper** (local add-on) | Slow on weak HW | Not ideal on HA Green / Pi |

### Text-to-Speech

| Engine | Quality | Notes |
|--------|---------|-------|
| **Piper** (local) | Good, natural | Lightweight, runs anywhere |
| **HA Cloud** | Excellent | Requires subscription |
| **Google Translate TTS** | Decent | Needs internet |

> **Tip**: On HA Green or Raspberry Pi, local Whisper will be slow. Use Faster Whisper on a separate machine or HA Cloud.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Cannot connect to gateway | Check URL: `curl http://<ip>:<port>/v1/chat/completions`. Check firewall. Don't use `127.0.0.1` across machines. |
| Endpoint disabled (405) | Enable `chatCompletions` in `openclaw.json`, restart gateway |
| Invalid auth (401) | Check token. Ensure `gateway.auth.mode` is `"token"` |
| Red flashing light (Voice PE) | STT failed — check your STT engine config |
| Agent not in dropdown | Restart HA after installing. Check logs for errors |

## Known limitations

- **Response latency**: Full pipeline (STT > LLM > TTS) takes a few seconds. Local Whisper on low-powered devices adds delay.
- **No continuous conversation**: Wake word needed after each response (HA pipeline limitation).
- **No audio streaming**: Responses are fully generated before being spoken.

## Support the project

Like it? Found it useful?

[![Buy Me A Beer](https://img.shields.io/badge/Buy%20Me%20A%20Beer-☕%20Support%20this%20project-yellow?style=for-the-badge&logo=buy-me-a-coffee)](https://buymeacoffee.com/nicolasglg)

## Links

- [OpenClaw](https://openclaw.ai) — AI assistant framework
- [OpenClaw Documentation](https://docs.openclaw.ai)
- [Home Assistant Voice](https://www.home-assistant.io/voice_control/)
- [HACS](https://hacs.xyz/)

## License

MIT
