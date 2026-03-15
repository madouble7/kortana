import base64
from datetime import UTC, datetime, timedelta

import pytest

from kortana.voice.errors import VoiceProcessingError
from kortana.voice.orchestrator import VoiceChatOrchestrator
from kortana.voice.stt_service import STTService
from kortana.voice.tts_service import TTSService
from kortana.voice.voice_session import VoiceSessionManager


class DummyChatEngine:
    async def process_message(self, user_message: str, **kwargs) -> str:
        return f"echo: {user_message}"


def test_stt_heuristic_text_prefix():
    service = STTService()
    result = service.transcribe(b"TEXT: hello from unit test")
    assert result["text"] == "hello from unit test"
    assert "stt_ms" in result["metrics"]


def test_stt_empty_audio_raises():
    service = STTService()
    with pytest.raises(VoiceProcessingError) as exc:
        service.transcribe(b"")
    assert exc.value.code == "empty_audio"


def test_tts_generates_audio_bytes():
    service = TTSService()
    result = service.synthesize("hello")
    assert isinstance(result["audio_bytes"], bytes)
    assert len(result["audio_bytes"]) > 40


@pytest.mark.asyncio
async def test_voice_orchestrator_full_turn():
    orchestrator = VoiceChatOrchestrator(chat_engine=DummyChatEngine())
    result = await orchestrator.process_voice_turn(
        audio_bytes=b"TEXT: keep going", user_id="test-user", return_audio=True
    )

    assert result["transcript"] == "keep going"
    assert result["response"].startswith("echo:")
    assert result["response_audio_base64"] is not None
    assert result["session"]["turn_count"] == 1
    assert result["session"]["user_id"] == "test-user"
    assert "sessions_reaped" in result["metrics"]

    # sanity check base64 decodes
    decoded = base64.b64decode(result["response_audio_base64"])
    assert isinstance(decoded, bytes)
    assert len(decoded) > 40


def test_voice_session_manager_reuses_session():
    manager = VoiceSessionManager()
    s1 = manager.get_or_create(session_id=None, user_id="u1")
    s2 = manager.get_or_create(session_id=s1.session_id, user_id="u1")
    assert s1.session_id == s2.session_id


def test_voice_session_cleanup_inactive_removes_stale():
    manager = VoiceSessionManager()
    session = manager.get_or_create(session_id=None, user_id="u1")
    session.last_activity_at = datetime.now(UTC) - timedelta(seconds=120)

    removed = manager.cleanup_inactive(max_idle_seconds=10)
    assert removed == 1
    assert manager.get_snapshot(session.session_id) is None


@pytest.mark.asyncio
async def test_orchestrator_reaps_stale_sessions():
    manager = VoiceSessionManager()
    stale = manager.get_or_create(session_id=None, user_id="old-user")
    stale.last_activity_at = datetime.now(UTC) - timedelta(seconds=120)

    orchestrator = VoiceChatOrchestrator(
        chat_engine=DummyChatEngine(),
        session_manager=manager,
        session_idle_seconds=5,
    )
    result = await orchestrator.transcribe_only(
        audio_bytes=b"TEXT: hello",
        user_id="new-user",
    )
    assert result["metrics"]["sessions_reaped"] >= 1
