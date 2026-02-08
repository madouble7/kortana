# Kor'tana Voice Chat

This document describes the new voice chat pipeline and API endpoints.

## Overview

Voice chat is now handled by a modular pipeline in `src/kortana/voice/`:

- `stt_service.py` - validates audio and performs speech-to-text
- `tts_service.py` - synthesizes response audio
- `voice_session.py` - tracks voice session state and turns
- `orchestrator.py` - coordinates STT -> ChatEngine -> TTS

The API layer is exposed in `src/kortana/main.py`.

## Endpoints

### `POST /voice/transcribe`

Transcribes base64-encoded audio into text.

Request JSON:

```json
{
  "audio_base64": "<base64-audio>",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id"
}
```

### `POST /voice/chat`

Processes a full voice turn and returns transcript, response text, optional response audio, and metrics.

Request JSON:

```json
{
  "audio_base64": "<base64-audio>",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id",
  "user_name": "optional-user-name",
  "return_audio": true
}
```

## Config

Voice settings are available under `settings.voice`:

- `enabled`
- `max_audio_bytes`
- `min_audio_seconds`
- `return_audio_by_default`

## Reliability and Metrics

Responses include per-stage latency and payload metrics:

- `stt_ms`
- `llm_ms`
- `tts_ms` (if synthesis runs)
- `total_ms`

If TTS fails, the system gracefully falls back to text while returning TTS fallback metadata.
