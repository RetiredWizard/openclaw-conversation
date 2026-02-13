# OpenClaw Conversation for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Use [OpenClaw](https://openclaw.ai) as a conversation agent in Home Assistant. Talk to your AI assistant through Home Assistant Voice, the Assist UI, or any voice pipeline.

Your full OpenClaw agent — with all its tools, memory, personality, and integrations — becomes your voice assistant.

## How it works

```
Wake word → Speech-to-Text → OpenClaw → Text-to-Speech → Speaker
```

The integration calls OpenClaw's OpenAI-compatible `/v1/chat/completions` endpoint. Your OpenClaw agent processes the request with full context (tools, memory, smart home control) and responds.

## Prerequisites

- **OpenClaw Gateway** running with the Chat Completions endpoint enabled
- **Home Assistant** 2024.1+
- **HACS** installed
- **Speech-to-Text** engine: Whisper (local), Faster Whisper, or Home Assistant Cloud
- **Text-to-Speech** engine: Piper (local), Google Translate TTS, or Home Assistant Cloud
- A voice device: Home Assistant Voice PE, phone with HA app, or browser

## OpenClaw Gateway Setup

### 1. Enable the Chat Completions endpoint

Add the following to your `openclaw.json` inside the `gateway` block:

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

### 2. Firewall / Network

The Home Assistant instance must be able to reach your OpenClaw Gateway over the network (HTTP).

**Common issues:**
- **Firewall blocking the port**: If your gateway runs on a separate machine, make sure the gateway port (default `18789`) is open. Example with UFW:
  ```bash
  sudo ufw allow from 192.168.1.0/24 to any port 18789 proto tcp
  ```
- **Using `127.0.0.1`**: This only works if HA and OpenClaw run on the same machine. If they're on separate devices, use the gateway machine's LAN IP (e.g., `http://192.168.1.100:18789`).
- **Docker networking**: If HA runs in Docker, `127.0.0.1` refers to the container, not the host. Use the host's LAN IP or Docker network gateway.

### 3. Authentication

Make sure your gateway has auth configured (`gateway.auth.mode: "token"`). You'll need this token during the integration setup.

## Installation

### HACS (recommended)

1. Open **HACS** in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add this repository URL with category **Integration**
4. Search for **"OpenClaw Conversation"** and install
5. Restart Home Assistant

### Manual

Copy the `custom_components/openclaw_conversation` folder into your Home Assistant `config/custom_components/` directory and restart.

## Configuration

### 1. Add the integration

Go to **Settings → Devices & Services → Add Integration** → search for **"OpenClaw Conversation"**

Enter:
- **Name**: display name (e.g., "OpenClaw")
- **OpenClaw Gateway URL**: `http://<gateway-ip>:<port>` (e.g., `http://192.168.1.100:18789`)
- **API Token**: your gateway auth token
- **Model**: `openclaw` (default, leave as-is)
- **Timeout**: `30` seconds (increase if needed for complex responses)

### 2. Create or edit a Voice Assistant

Go to **Settings → Voice Assistants** and create a new assistant (or edit an existing one):

- **Conversation agent**: select **OpenClaw**
- **Speech-to-Text**: select your STT engine (Whisper, Faster Whisper, or HA Cloud)
- **Text-to-Speech**: select your TTS engine (Piper, Google Translate, or HA Cloud)
- **Wake word**: select a wake word engine (e.g., openWakeWord with "Ok Nabu")

### 3. Assign to your voice device

If using Home Assistant Voice PE or another satellite:
- Go to the device's entity settings
- Set the **Preferred Assistant** to the one you configured above

### 4. Test

- Say the wake word, then speak
- Or go to **Voice Assistants** → three dots → **Start a conversation** to test via text

## STT and TTS notes

You need **both** a Speech-to-Text and Text-to-Speech engine for voice to work.

### Speech-to-Text options

| Engine | Speed | Quality | Requirements |
|--------|-------|---------|-------------|
| **Home Assistant Cloud** | Fast | Excellent | HA Cloud subscription |
| **Faster Whisper** (Wyoming) | Good | Excellent | Separate server with decent CPU/GPU |
| **Whisper** (local add-on) | Slow on weak hardware | Good | CPU-intensive, not ideal on HA Green/Pi |

> **Tip**: If running on HA Green or Raspberry Pi, local Whisper will be slow. Consider running Faster Whisper on a separate machine or using HA Cloud.

### Text-to-Speech options

| Engine | Quality | Requirements |
|--------|---------|-------------|
| **Piper** (local) | Good, natural voices | Lightweight, runs on any hardware |
| **Home Assistant Cloud** | Excellent | HA Cloud subscription |
| **Google Translate TTS** | Decent | Internet connection |

## Known limitations

- **Response latency**: The full pipeline (STT → OpenClaw LLM → TTS) takes a few seconds. Local Whisper on low-powered devices (HA Green, Raspberry Pi) adds significant delay. This will be improved in future versions.
- **No continuous conversation**: After the assistant responds, you need to say the wake word again. This is a Home Assistant pipeline limitation, not specific to OpenClaw.
- **No audio streaming**: Responses are generated fully before being spoken (no streaming TTS).

## Roadmap

- [ ] Custom STT component using Groq Whisper for faster transcription
- [ ] Reduced latency through streaming responses
- [ ] Continuous conversation mode
- [ ] Direct HA entity control through OpenClaw tools
- [ ] HACS default repository submission

## Troubleshooting

### "Cannot connect to OpenClaw Gateway"
- Check the URL is reachable from your HA machine: `curl http://<ip>:<port>/v1/chat/completions`
- Check firewall rules on the gateway machine
- Don't use `127.0.0.1` unless HA and OpenClaw are on the same machine

### "Endpoint disabled" (405 error)
- Enable `chatCompletions` in your `openclaw.json` (see setup above)
- Restart the gateway

### "Invalid auth" (401 error)
- Double-check your gateway auth token
- Make sure `gateway.auth.mode` is `"token"` in your config

### Red flashing light on HA Voice PE
- Usually means STT failed. Check that you have a working STT engine configured
- Check HA logs: **Settings → System → Logs**

### Agent not appearing in conversation agent dropdown
- Make sure HA was restarted after installing the integration
- Check logs for setup errors

## License

MIT

## Links

- [OpenClaw](https://openclaw.ai) — AI assistant framework
- [OpenClaw Documentation](https://docs.openclaw.ai)
- [Home Assistant Voice](https://www.home-assistant.io/voice_control/)
- [HACS](https://hacs.xyz/)
