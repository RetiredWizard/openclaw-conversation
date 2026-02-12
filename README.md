# OpenClaw Conversation for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Use [OpenClaw](https://openclaw.ai) as a conversation agent in Home Assistant. Talk to your AI assistant through Home Assistant Voice, the Assist UI, or any voice pipeline.

## Prerequisites

- A running OpenClaw Gateway with the Chat Completions endpoint enabled
- Home Assistant 2024.1+
- HACS installed

## OpenClaw Setup

Enable the OpenAI-compatible endpoint in your `openclaw.json`:

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

Restart your gateway after the config change.

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add this repository URL with category **Integration**
4. Search for "OpenClaw Conversation" and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/openclaw_conversation` folder to your Home Assistant `config/custom_components/` directory.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "OpenClaw Conversation"
3. Enter:
   - **OpenClaw Gateway URL**: e.g. `http://192.168.1.100:18789`
   - **API Token**: your gateway auth token
   - **Model**: `openclaw` (default)
4. Go to **Settings → Voice Assistants**
5. Edit your assistant and select **OpenClaw** as the conversation agent

## How it works

```
Wake word → Whisper (STT) → OpenClaw Gateway → Piper (TTS) → Speaker
```

The integration calls OpenClaw's OpenAI-compatible `/v1/chat/completions` endpoint. Your full OpenClaw agent (with all its tools, memory, and personality) processes the request and responds.

## License

MIT
