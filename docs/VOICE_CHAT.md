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
  "audio_base64": "<base64-audio-or-data-uri>",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id"
}
```

### `POST /voice/chat`

Processes a full voice turn and returns transcript, response text, optional response audio, and metrics.

Request JSON:

```json
{
  "audio_base64": "<base64-audio-or-data-uri>",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id",
  "user_name": "optional-user-name",
  "return_audio": true
}
```

Supported audio payload formats:

- Plain base64 encoded audio bytes
- Browser style data URI payloads (for example: `data:audio/wav;base64,<...>`)

### `GET /voice/sessions/{session_id}`

Returns live voice session state (`turn_count`, timestamps, interruption flag, idle/age stats).

### `POST /voice/sessions/{session_id}/interrupt`

Marks a session interrupted or resumed.

Request JSON:

```json
{
  "interrupted": true
}
```

### `DELETE /voice/sessions/{session_id}`

Ends and removes an active voice session.

## Config

Voice settings are available under `settings.voice`:

- `enabled`
- `max_audio_bytes`
- `min_audio_seconds`
- `return_audio_by_default`
- `session_idle_seconds`
- `max_active_sessions`
- `stt_provider` / `stt_fallback_provider` (`openai`, `heuristic`)
- `tts_provider` / `tts_fallback_provider` (`pyttsx3`, `tone`)
- `openai_stt_model`
- `tts_voice_name`, `tts_rate`, `tts_volume`

### Provider behavior

- STT defaults to `openai` and falls back to `heuristic` if provider call fails.
- TTS defaults to `pyttsx3` and falls back to `tone` if synthesis fails.
- If `OPENAI_API_KEY` is missing, STT automatically falls back when configured.

## Reliability and Metrics

Responses include per-stage latency and payload metrics:

- `stt_ms`
- `llm_ms`
- `tts_ms` (if synthesis runs)
- `total_ms`
- `sessions_reaped`

If TTS fails, the system gracefully falls back to text while returning TTS fallback metadata.
