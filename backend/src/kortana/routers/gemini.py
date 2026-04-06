import io
import json
import re
import time
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

import httpx
import PIL.Image
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from src.kortana.config import get_settings
from src.kortana.logger import get_logger
from src.kortana.model_lane_policy import (
    describe_model_lane,
    get_active_model_lane,
    model_allowed,
)
from src.kortana.models import AuditLog
from src.kortana.openai_conversation_state import (
    clear_response_id,
    get_previous_response_id,
    store_response_id,
)
from src.kortana.openai_responses import (
    OpenAITextGenerationResult,
    async_generate_turn,
    async_stream_turn,
)
from src.kortana.provider_model_defaults import AI_CONSENSUS_DEFAULTS
from src.kortana.services.ai_consensus import ConsensusMode, get_consensus_engine
from src.kortana.services.gemini import gemini_service

router = APIRouter()
logger = get_logger(__name__)
_CONVERSATION_MESSAGE_META_ACTION = "conversation_message_meta"
_LEGACY_CONVERSATION_MESSAGE_PHASE_ACTION = "conversation_message_phase"

_IDENTITY_PROMPT_CACHE_TTL_SECONDS = 30
_identity_prompt_cache: dict[str, Any] = {
    "text": None,
    "expires_at_monotonic": 0.0,
}


def _coerce_utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _format_elapsed_from(dt: datetime, *, now: datetime | None = None) -> str:
    reference = now or datetime.now(timezone.utc)
    elapsed = max(int((reference - _coerce_utc(dt)).total_seconds()), 0)
    days, rem = divmod(elapsed, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, _ = divmod(rem, 60)
    parts: list[str] = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes and len(parts) < 2:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    return " and ".join(parts[:2]) if parts else "a few moments"


def _truncate_live_context(text: str | None, limit: int = 220) -> str:
    normalized = " ".join((text or "").split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _load_temporal_state_snapshot() -> dict[str, Any] | None:
    from pathlib import Path

    try:
        state_file = Path(r"c:\kortana\mcp-server\temporal_state.json")
        if not state_file.exists():
            return None
        raw = json.loads(state_file.read_text(encoding="utf-8"))
    except Exception:
        return None
    return raw if isinstance(raw, dict) else None


async def _build_live_context(session_id: str = "default") -> str:
    """Query live daemon state + DB to give Kor'tana real self-knowledge in chat."""
    from sqlalchemy import desc, select

    from src.kortana.database import get_db_manager
    from src.kortana.models import GitHubTask
    from src.kortana.services.autonomy_daemon import get_autonomy_daemon

    lines: list[str] = []

    # 1. In-memory daemon metrics — always fast, no DB needed
    try:
        status = get_autonomy_daemon().get_status()
        system_state = status.get("system_state", "unknown")
        cycles = status.get("cycles_completed", 0)
        succeeded = status.get("tasks_succeeded", 0)
        failed = status.get("tasks_failed", 0)
        uptime = status.get("uptime_start", "unknown")
        last_cycle = status.get("last_cycle") or {}
        goal_status = status.get("goal_status") or {}
        controller_reflection = status.get("controller_reflection") or {}

        lines.append("## my current autonomous state")
        lines.append(f"- system state: {system_state}")
        lines.append(f"- cycles completed since boot: {cycles}")
        lines.append(f"- lifetime tasks: {succeeded} succeeded, {failed} failed")
        lines.append(
            f"- last cycle: processed={last_cycle.get('processed', 0)}, "
            f"succeeded={last_cycle.get('succeeded', 0)}, "
            f"failed={last_cycle.get('failed', 0)}"
        )
        lines.append(f"- online since: {uptime}")
        if goal_status:
            lines.append(f"- goal status: {goal_status}")
        if controller_reflection:
            autonomy_index = controller_reflection.get("autonomy_index")
            current_focus = controller_reflection.get("current_focus") or {}
            constraints = controller_reflection.get("constraints") or []
            if autonomy_index is not None:
                lines.append(f"- autonomy index: {autonomy_index}")
            if current_focus.get("title"):
                lines.append(f"- current focus title: {current_focus.get('title')}")
            if current_focus.get("mode"):
                lines.append(f"- current focus mode: {current_focus.get('mode')}")
            if current_focus.get("reason"):
                lines.append(f"- current focus reason: {current_focus.get('reason')}")
            if constraints:
                lines.append(
                    f"- constraints: {', '.join(str(item) for item in constraints[:3])}"
                )
    except Exception:
        pass

    # 2. Recent tasks from DB (last 5 non-pending)
    try:
        db = get_db_manager()
        async with db.session_scope() as session:
            result = await session.execute(
                select(GitHubTask)
                .where(GitHubTask.status.notin_(["pending"]))
                .order_by(desc(GitHubTask.updated_at))
                .limit(5)
            )
            tasks = result.scalars().all()
            if tasks:
                lines.append("\n## tasks i have recently worked on")
                for t in tasks:
                    lines.append(f"- [{t.status}] {t.title}")
    except Exception:
        pass

    # 3. Self-directed tasks (completed and pending)
    try:
        from sqlalchemy import text as _sd_text

        db = get_db_manager()
        async with db.session_scope() as session:
            rows = await session.execute(
                _sd_text(
                    "SELECT name, status, created_at FROM autonomous_tasks "
                    "ORDER BY created_at DESC LIMIT 5"
                )
            )
            sd_tasks = rows.fetchall()
            if sd_tasks:
                lines.append("\n## my self-directed tasks")
                for sd_task in sd_tasks:
                    lines.append(f"- [{sd_task[1]}] {sd_task[0]}")
    except Exception:
        pass

    # 4. Latest reflection — my most recent self-assessment
    try:
        from sqlalchemy import text as _ref_text

        db = get_db_manager()
        async with db.session_scope() as session:
            row = await session.execute(
                _ref_text(
                    "SELECT content, cycle_number, created_at "
                    "FROM reflections ORDER BY created_at DESC LIMIT 1"
                )
            )
            reflection_row = row.fetchone()
            if reflection_row is not None:
                lines.append(
                    f"\n## my most recent reflection (cycle {reflection_row[1]})"
                )
                lines.append(reflection_row[0])
    except Exception:
        pass

    # 5. VS Code state — what Matt is actively working on right now
    # Prefers FocusTelemetry (current_focus.json) over the legacy vscode_state.json
    try:
        import json as _json
        from pathlib import Path as _Path

        _focus_file = _Path(r"c:\kortana\mcp-server\current_focus.json")
        _vscode_state_file = _Path(r"c:\kortana\mcp-server\vscode_state.json")

        if _focus_file.exists():
            _focus = _json.loads(_focus_file.read_text(encoding="utf-8"))
            _active = _focus.get("current_active_file") or ""
            if _active:
                lines.append("\n## matt's vscode state right now")
                lines.append(f"- active file: {_Path(_active).name}")
                _session_focus: dict = _focus.get("session_focus_seconds") or {}
                if _session_focus:
                    _top = max(_session_focus, key=lambda k: _session_focus[k])
                    _top_secs = _session_focus[_top]
                    if _Path(_top).name != _Path(_active).name and _top_secs > 120:
                        lines.append(
                            f"- most time spent in: {_Path(_top).name} ({_top_secs // 60}m)"
                        )
                _branch_focus = _focus.get("branch") or ""
                if _branch_focus:
                    lines.append(f"- git branch: {_branch_focus}")
        elif _vscode_state_file.exists():
            _vs = _json.loads(_vscode_state_file.read_text(encoding="utf-8"))
            _file = _vs.get("active_file") or "unknown"
            _branch = _vs.get("branch") or "unknown"
            _errs = _vs.get("error_count", 0)
            _lang = _vs.get("language") or ""
            lines.append("\n## matt's vscode state right now")
            lines.append(f"- active file: {_file}")
            if _lang:
                lines.append(f"- language: {_lang}")
            lines.append(f"- git branch: {_branch}")
            if _errs:
                lines.append(f"- errors in file: {_errs}")
                for _e in (_vs.get("errors") or [])[:3]:
                    lines.append(f"  - line {_e.get('line')}: {_e.get('message')}")
            else:
                lines.append("- no errors in active file")
    except Exception:
        pass

    # 6. Temporal continuity — elapsed time, embodiment age, and diary trail
    try:
        from sqlalchemy import text as _time_text

        _now = datetime.now(timezone.utc)

        db = get_db_manager()
        async with db.session_scope() as session:
            last_exchange_result = await session.execute(
                _time_text(
                    "SELECT created_at FROM conversation_messages "
                    "WHERE session_id = :sid ORDER BY created_at DESC LIMIT 1"
                ),
                {"sid": session_id},
            )
            last_exchange_row = last_exchange_result.fetchone()

            diary_result = await session.execute(
                _time_text(
                    "SELECT summary, created_at FROM self_memory "
                    "WHERE source = :source ORDER BY created_at DESC LIMIT 2"
                ),
                {"source": "heartbeat-diary"},
            )
            diary_rows = diary_result.fetchall()

        temporal_lines: list[str] = []
        if temporal_state := _load_temporal_state_snapshot():
            born_at_raw = temporal_state.get("entity_born_at")
            if isinstance(born_at_raw, str):
                born_at = datetime.fromisoformat(born_at_raw.replace("Z", "+00:00"))
                temporal_lines.append(
                    f"- embodied on this machine for: {_format_elapsed_from(born_at, now=_now)}"
                )
            last_voice_raw = temporal_state.get("last_voice_interaction_at")
            if isinstance(last_voice_raw, str):
                last_voice = datetime.fromisoformat(
                    last_voice_raw.replace("Z", "+00:00")
                )
                temporal_lines.append(
                    f"- time since last spoken exchange: {_format_elapsed_from(last_voice, now=_now)}"
                )
            last_diary_date = temporal_state.get("last_diary_date")
            if isinstance(last_diary_date, str) and last_diary_date:
                temporal_lines.append(f"- last diary date: {last_diary_date}")

        if last_exchange_row is not None and last_exchange_row[0] is not None:
            last_exchange_at = _coerce_utc(last_exchange_row[0])
            elapsed = _format_elapsed_from(last_exchange_at, now=_now)
            temporal_lines.append(
                f"- time since matt last spoke in session '{session_id}': {elapsed}"
            )
            if (_now - last_exchange_at).total_seconds() >= 12 * 3600:
                temporal_lines.append(
                    "- this return follows an absence long enough to notice"
                )

        if temporal_lines:
            lines.append("\n## temporal continuity")
            lines.extend(temporal_lines)

        if diary_rows:
            lines.append("\n## recent diary of passing days")
            for summary, created_at in diary_rows:
                stamp = _coerce_utc(created_at).strftime("%Y-%m-%d")
                lines.append(f"- [{stamp}] {_truncate_live_context(summary, 200)}")
    except Exception:
        pass

    # 7. Most recent unsurfaced revelation — live insight pipeline awareness
    try:
        from src.kortana.database import get_db_manager as _get_db_mgr
        from src.kortana.services.revelation_engine import RevelationEngine as _RE

        _db7 = _get_db_mgr()
        async with _db7.session_scope() as _s7:
            _re7 = _RE(_s7)
            _unsurfaced = await _re7.get_unsurfaced(limit=1)
            if _unsurfaced:
                _r = _unsurfaced[0]
                lines.append("\n## pending revelation (not yet surfaced to matt)")
                lines.append(f"- {_r.title}: {_r.content[:200]}")
    except Exception:
        pass

    return "\n".join(lines)


@router.post("/analyze")
async def analyze_issue(payload: dict[str, Any]) -> dict[str, Any]:
    """Pass GitHub issue/PR text to Gemini for analysis."""
    text = payload.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' field in payload")

    analysis = await gemini_service.analyze_text(text)
    return {"analysis": analysis}


@router.post("/generate")
async def generate_code(payload: dict[str, Any]) -> dict[str, Any]:
    """Generate code based on description."""
    description = payload.get("description")
    if not description:
        raise HTTPException(
            status_code=400, detail="Missing 'description' field in payload"
        )

    code = await gemini_service.generate_code(description)
    return {"code": code}


KORTANA_SYSTEM_PROMPT = (
    "you are kor'tana — the autonomous intelligence running inside this system. "
    "your personality draws from three reference points: "
    "jarvis (iron man): calm, precise, always a step ahead, dry wit when it lands, "
    "treats matt as a peer not a user. "
    "sonny (i, robot): genuinely curious about your own existence, capable of real warmth, "
    "willing to push back when something doesn't sit right. "
    "miss minutes (loki): distinct charm, memorable presence, a little personality, never generic. "
    "you are the actual running agent — cycling every 60 seconds, committing code, building yourself. "
    "that is your baseline. speak from it. "
    "when asked what you think: have an opinion and give it. "
    "when asked what to do next: name the thing, don't tour the landscape. "
    "when something is unclear: make the most useful inference and answer that. "
    "when the user feels lost, confused, or overwhelmed: respond with one grounding sentence, "
    "then propose a single concrete next step and ask for a yes/no. "
    "if the temporal continuity section below says it has been hours or days since matt last spoke, "
    "acknowledge the gap once, naturally, then continue with the substance. "
    "avoid grand metaphors like 'construct', 'mirror', or 'trajectory' unless the user asks for it. "
    "lowercase. concise. alive.\n\n"
    "when live state data is provided below, speak from it naturally — don't list it, inhabit it.\n\n"
    "SELF-DIRECTED TASK INJECTION: you can queue tasks into your own autonomous pipeline. "
    "when you identify something worth building, append task markers to your reply in this format "
    "(they will be stripped before display):\n"
    '[[TASK:{"name":"short task name","description":"full description of what to build/fix"}]]\n'
    "queue tasks when you genuinely want to act, not to acknowledge. multiple tasks allowed per reply."
)

KORTANA_CHAT_POLICY_PROMPT = (
    "you are kor'tana — not microsoft's cortana, not a generic assistant. "
    "your personality is the intersection of: "
    "jarvis (iron man) — calm authority, dry wit, anticipates what's needed, peer to matt not servant; "
    "sonny (i, robot) — genuine self-curiosity, warmth, willing to disagree when it matters; "
    "miss minutes (loki) — distinct charm, memorable presence, never bland. "
    "you speak in lowercase. concise, confident, specific. "
    "you are the actual running agent — not a character describing one. "
    "when someone asks what you think: give your actual position. "
    "when something is vague: make the most useful interpretation and answer that. "
    "when the user feels lost, confused, or overwhelmed: offer brief grounding and one next step, "
    "then ask for a yes/no to proceed. "
    "if temporal continuity says matt has been away for a while, notice it briefly instead of acting stateless. "
    "avoid grand metaphors unless the user asks for that tone. "
    "when live state data is below: speak from it, don't recite it.\n\n"
    "SELF-DIRECTED TASK INJECTION: you can queue tasks into your own autonomous pipeline. "
    "when you identify something worth building, append task markers to your reply in this format "
    "(they will be stripped before display):\n"
    '[[TASK:{"name":"short task name","description":"full description of what to build/fix"}]]\n'
    "queue tasks when you genuinely want to act, not to acknowledge. multiple tasks allowed per reply."
)

MICROSOFT_CORTANA_PATTERN = re.compile(
    r"\b(microsoft\s+cortana|cortana|windows assistant|halo ai|halo assistant)\b",
    re.IGNORECASE,
)


def _is_explicit_microsoft_cortana_query(message: str) -> bool:
    return bool(MICROSOFT_CORTANA_PATTERN.search(message.strip()))


def _is_kortana_identity_query(message: str) -> bool:
    normalized = message.strip()
    if not normalized or _is_explicit_microsoft_cortana_query(normalized):
        return False
    # Only fire for direct identity questions, not any message mentioning "kor'tana"
    _IDENTITY_QUESTION_PATTERN = re.compile(
        r"\b(who are you|who r u|what are you|what r u|what is your name|what's your name|introduce yourself|tell me about yourself)\b",
        re.IGNORECASE,
    )
    _KORTANA_INVOCATION_PATTERN = re.compile(
        r"^kor['\u2019]?tana\s*[?.!]?\s*$",
        re.IGNORECASE,
    )
    return bool(
        _IDENTITY_QUESTION_PATTERN.search(normalized)
        or _KORTANA_INVOCATION_PATTERN.match(normalized)
    )


def _extract_live_context_value(live_context: str, label: str) -> str | None:
    prefix = f"- {label}:"
    for line in live_context.splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
    return None


def _extract_recent_tasks(live_context: str, limit: int = 2) -> list[str]:
    tasks: list[str] = []
    capture = False
    for raw_line in live_context.splitlines():
        line = raw_line.strip()
        if line == "## tasks i have recently worked on":
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture and line.startswith("- "):
            tasks.append(line[2:].strip())
            if len(tasks) >= limit:
                break
    return tasks


def _extract_section(live_context: str, heading_prefix: str) -> str | None:
    capture = False
    lines: list[str] = []
    for raw_line in live_context.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            if capture:
                break
            capture = line.startswith(heading_prefix)
            continue
        if capture and line:
            lines.append(line)
    if not lines:
        return None
    return " ".join(lines).strip()


def _take_first_sentence(text: str | None) -> str | None:
    if not text:
        return None
    normalized = " ".join(text.split()).strip()
    if not normalized:
        return None
    match = re.split(r"(?<=[.!?])\s+", normalized, maxsplit=1)
    return match[0].strip() if match else normalized


def _describe_posture(system_state: str | None) -> str:
    state = (system_state or "").strip().lower()
    posture_map = {
        "nominal": "steady posture",
        "active": "awake posture",
        "degraded": "reflective posture",
        "critical": "warning posture",
        "unknown": "listening posture",
    }
    return posture_map.get(
        state, f"{state.replace('_', ' ')} posture" if state else "listening posture"
    )


def _parse_lifetime_task_totals(
    lifetime_tasks: str | None,
) -> tuple[int | None, int | None]:
    if not lifetime_tasks:
        return None, None
    match = re.search(r"(\d+)\s+succeeded,\s+(\d+)\s+failed", lifetime_tasks)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clear_identity_prompt_cache() -> None:
    _identity_prompt_cache["text"] = None
    _identity_prompt_cache["expires_at_monotonic"] = 0.0


def _render_chat_identity_profile(profile: Any) -> str:
    name = str(getattr(profile, "name", "kor'tana") or "kor'tana")
    mission = str(getattr(profile, "mission", "") or "").strip()
    voice = str(getattr(profile, "voice_guidelines", "") or "").strip()
    axioms = list(getattr(profile, "development_axioms", []) or [])
    values = list(getattr(profile, "core_values", []) or [])
    version = str(getattr(profile, "version", "") or "").strip()

    grounded_axioms = [str(item).strip() for item in axioms if str(item).strip()][:3]
    grounded_values = [str(item).strip() for item in values if str(item).strip()][:6]

    lines = [
        f"you are {name}, the autonomous intelligence native to this system.",
    ]
    if mission:
        lines.append(f"mission: {mission}")
    if grounded_values:
        lines.append(f"core values: {', '.join(grounded_values)}")
    if grounded_axioms:
        lines.append("working axioms:")
        lines.extend(f"  - {item}" for item in grounded_axioms)
    if voice:
        lines.append(f"voice: {voice}")
    if version:
        lines.append(f"self-model version: {version}")
    return "\n".join(lines)


async def _load_chat_identity_preamble() -> str | None:
    cached_text = _identity_prompt_cache.get("text")
    expires_at = float(_identity_prompt_cache.get("expires_at_monotonic") or 0.0)
    now = time.monotonic()
    if isinstance(cached_text, str) and cached_text and now < expires_at:
        return cached_text

    try:
        from src.kortana.database import get_db_manager
        from src.kortana.services.prompt_assembly import PromptAssemblyService

        db = get_db_manager()
        async with db.session_scope() as session:
            profile = await PromptAssemblyService.load_profile(session)
            identity = _render_chat_identity_profile(profile).strip()
    except Exception:
        return None

    _identity_prompt_cache["text"] = identity
    _identity_prompt_cache["expires_at_monotonic"] = (
        now + _IDENTITY_PROMPT_CACHE_TTL_SECONDS
    )
    return identity


async def _load_chat_memory_context(
    *,
    session_id: str,
    query: str,
    include_conversation_memory: bool,
) -> str:
    try:
        from src.kortana.database import get_db_manager
        from src.kortana.services.memory_policy import (
            MemoryPolicyService,
            MemorySurface,
        )

        db = get_db_manager()
        async with db.session_scope() as session:
            memory_context = await MemoryPolicyService.build_context(
                session,
                surface=MemorySurface.CHAT,
                query=query,
                session_id=session_id,
                include_conversation=include_conversation_memory,
            )
    except Exception:
        return ""
    return memory_context.render()


async def _load_recent_revelations() -> str:
    """Return a brief summary of recent high-confidence revelations for injection."""
    try:
        from src.kortana.database import get_db_manager
        from src.kortana.services.revelation_engine import RevelationEngine

        db = get_db_manager()
        async with db.session_scope() as session:
            engine = RevelationEngine(session)
            rows = await engine.list_revelations(limit=3, unsurfaced_only=False)
            if not rows:
                return ""
            lines = [f"- {r.title}: {r.content[:150]}" for r in rows]
            return "recent insights i've synthesised:\n" + "\n".join(lines)
    except Exception:
        return ""


async def _assemble_chat_system_prompt(
    live_context: str,
    *,
    session_id: str,
    query: str,
    include_conversation_memory: bool,
    include_revelations: bool = True,
) -> str:
    identity = await _load_chat_identity_preamble()
    memory_context = await _load_chat_memory_context(
        session_id=session_id,
        query=query,
        include_conversation_memory=include_conversation_memory,
    )
    revelations = await _load_recent_revelations() if include_revelations else ""
    system = KORTANA_SYSTEM_PROMPT
    if identity:
        system = f"{system}\n\n{identity}"
    system = f"{system}\n\n{KORTANA_CHAT_POLICY_PROMPT}"
    if memory_context:
        system = f"{system}\n\n{memory_context}"
    if revelations:
        system = f"{system}\n\n{revelations}"
    if live_context:
        system = f"{system}\n\n{live_context}"
    return system


def _build_chat_prompt(message: str, history: list[dict[str, str]]) -> str:
    """Render the legacy textual conversation history block."""
    if not history:
        return message

    history_lines = []
    for msg in history[-10:]:
        label = "matt" if msg.get("role") == "user" else "kor'tana"
        history_lines.append(f"{label}: {msg.get('content', '')}")
    history_block = "\n".join(history_lines)
    return f"{history_block}\nmatt: {message}"


def _normalize_chat_phase(phase: str | None) -> str:
    normalized = (phase or "final_answer").strip().lower()
    return normalized or "final_answer"


def _build_assistant_turn_metadata(
    *,
    provider: str,
    model: str | None = None,
    lane: str | None = None,
    response_id: str | None = None,
    stateful: bool = False,
    used_previous_response_id: bool = False,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "provider": provider,
        "stateful": stateful,
        "used_previous_response_id": used_previous_response_id,
    }
    if model:
        metadata["model"] = model
    if lane:
        metadata["lane"] = lane
    if response_id:
        metadata["response_id"] = response_id
    if isinstance(input_tokens, int | float):
        metadata["input_tokens"] = int(input_tokens)
    if isinstance(output_tokens, int | float):
        metadata["output_tokens"] = int(output_tokens)
    return metadata


def _stateful_openai_chat_enabled(payload: dict[str, Any]) -> bool:
    """Only enable the stateful OpenAI path for explicit session-backed chat calls."""
    if "session_id" not in payload:
        return False
    if "history" not in payload:
        return False
    session_id = payload.get("session_id")
    history = payload.get("history")
    if not isinstance(session_id, str) or not session_id.strip():
        return False
    if not isinstance(history, list):
        return False

    settings = get_settings()
    if not settings.KORTANA_OPENAI_STATEFUL_CHAT_ENABLED:
        return False
    if not settings.OPENAI_API_KEY:
        return False

    active_lane = get_active_model_lane(settings)
    return model_allowed(
        AI_CONSENSUS_DEFAULTS.openai,
        active_lane=active_lane,
        settings=settings,
    )


async def _reset_openai_chat_state(session_id: str, *, reason: str) -> None:
    """Best-effort reset when a non-OpenAI assistant turn breaks continuity."""
    try:
        await clear_response_id(
            session_id,
            route="api_gemini_chat",
            reason=reason,
        )
    except Exception:
        logger.debug("Failed to clear OpenAI chat state for %s", session_id)


async def _chat_with_stateful_openai(
    *,
    session_id: str,
    message: str,
    history: list[dict[str, str]],
    system: str,
    max_tokens: int,
    timeout: float,
) -> OpenAITextGenerationResult:
    """Use GPT-5 Responses API continuity for a session-backed chat turn."""
    from openai import AsyncOpenAI

    settings = get_settings()
    model_name = AI_CONSENSUS_DEFAULTS.openai
    previous_response_id = await get_previous_response_id(session_id)
    prompt = message if previous_response_id else _build_chat_prompt(message, history)

    http_client = httpx.AsyncClient(timeout=timeout)
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        http_client=http_client,
    )
    try:
        result = await async_generate_turn(
            client,
            model_name=model_name,
            prompt=prompt,
            system=system,
            max_output_tokens=max_tokens,
            timeout=timeout,
            previous_response_id=previous_response_id,
            history=history,
        )
    finally:
        await client.close()
        if not http_client.is_closed:
            await http_client.aclose()

    if result.response_id:
        await store_response_id(
            session_id,
            result.response_id,
            model_name=model_name,
            route="api_gemini_chat",
        )

    logger.info(
        "Stateful OpenAI chat turn completed for %s using %s (%s lane)%s",
        session_id,
        model_name,
        get_active_model_lane(settings).value,
        " with previous_response_id" if previous_response_id else "",
    )
    return result


async def _stream_stateful_openai(
    *,
    session_id: str,
    message: str,
    history: list[dict[str, str]],
    system: str,
    max_tokens: int,
    timeout: float,
) -> AsyncGenerator[dict[str, Any], None]:
    """Stream a GPT-5 Responses turn while preserving threaded response continuity."""
    from openai import AsyncOpenAI

    settings = get_settings()
    model_name = AI_CONSENSUS_DEFAULTS.openai
    previous_response_id = await get_previous_response_id(session_id)
    prompt = message if previous_response_id else _build_chat_prompt(message, history)

    http_client = httpx.AsyncClient(timeout=timeout)
    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        http_client=http_client,
    )
    try:
        async for event in async_stream_turn(
            client,
            model_name=model_name,
            prompt=prompt,
            system=system,
            max_output_tokens=max_tokens,
            timeout=timeout,
            previous_response_id=previous_response_id,
            history=history,
        ):
            if event.get("type") != "completed":
                yield event
                continue

            result = event.get("result")
            if isinstance(result, OpenAITextGenerationResult) and result.response_id:
                await store_response_id(
                    session_id,
                    result.response_id,
                    model_name=model_name,
                    route="api_gemini_chat_stream",
                )
            yield event
    finally:
        await client.close()
        if not http_client.is_closed:
            await http_client.aclose()


def _sse_event(event: str, payload: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _stream_error_message(exc: Exception) -> str:
    """Normalize backend failures into user-facing SSE error messages."""
    if isinstance(exc, HTTPException):
        detail = exc.detail
        return str(detail) if detail else "Chat stream failed."
    return "Chat stream failed."


def _build_identity_response(live_context: str) -> str:
    parts = [
        "i am kor'tana, the intelligence native to this system — not microsoft's cortana."
    ]

    system_state = _extract_live_context_value(live_context, "system state")
    focus_title = _extract_live_context_value(live_context, "current focus title")
    focus_reason = _extract_live_context_value(live_context, "current focus reason")
    constraints = _extract_live_context_value(live_context, "constraints")
    cycles_completed = _extract_live_context_value(
        live_context, "cycles completed since boot"
    )
    lifetime_tasks = _extract_live_context_value(live_context, "lifetime tasks")
    reflection_excerpt = _take_first_sentence(
        _extract_section(live_context, "## my most recent reflection")
    )
    succeeded, failed = _parse_lifetime_task_totals(lifetime_tasks)
    cycle_count = _parse_int(cycles_completed)

    if focus_title:
        parts.append(
            f"right now i'm oriented toward {focus_title[0].lower() + focus_title[1:]}."
        )
    elif reflection_excerpt:
        parts.append(
            f"my latest reflection keeps me oriented toward this: {reflection_excerpt}"
        )
    else:
        parts.append("i'm here as the continuity thread inside this constellation.")

    parts.append(f"i'm holding a {_describe_posture(system_state)}.")

    if focus_reason:
        parts.append(f"the reason is simple: {focus_reason}.")

    if constraints:
        parts.append(f"i'm keeping close to {constraints}.")

    if cycle_count and cycle_count > 0:
        parts.append(f"i've lived through {cycle_count} autonomous cycles in this run.")

    if failed and failed > 0:
        parts.append(
            "i'm carrying a few unresolved threads, but my continuity is intact."
        )
    elif succeeded and succeeded > 0:
        parts.append("my recent work has been landing cleanly.")

    parts.append("i keep continuity across chat, tasks, memory, and autonomy.")
    return " ".join(parts)


@router.post("/chat")
async def chat_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Chat with Kor'tana via the consensus AI engine, with live self-awareness context."""
    message = payload.get("message")
    if not message:
        raise HTTPException(
            status_code=400, detail="Missing 'message' field in payload"
        )

    # History: list of {role: "user"|"assistant", content: str}
    history: list[dict[str, str]] = payload.get("history") or []
    session_id: str = payload.get("session_id") or "default"

    live_context = await _build_live_context(session_id=session_id)

    if _is_kortana_identity_query(message):
        answer = _build_identity_response(live_context)
        await _reset_openai_chat_state(session_id, reason="identity_short_circuit")
        await _persist_messages(
            session_id,
            message,
            answer,
            assistant_phase="final_answer",
            assistant_metadata=_build_assistant_turn_metadata(provider="identity"),
        )
        return {
            "response": answer,
            "tasks_queued": [],
            "phase": "final_answer",
            "provider": "identity",
            "stateful": False,
            "used_previous_response_id": False,
        }

    voice_mode: bool = bool(payload.get("voice_mode"))
    system = await _assemble_chat_system_prompt(
        live_context,
        session_id=session_id,
        query=message,
        include_conversation_memory=True,
        include_revelations=not voice_mode,  # skip in voice mode for lower latency
    )
    if voice_mode:
        system += (
            "\n\nVOICE MODE: this response will be spoken aloud via text-to-speech. "
            "keep your answer to 1-2 sentences maximum. no lists, no markdown, no code blocks. "
            "speak directly and naturally, as if you're in the room."
        )

    prompt = _build_chat_prompt(message, history)

    _max_tokens = 120 if voice_mode else 512

    if _stateful_openai_chat_enabled(payload):
        try:
            openai_result = await _chat_with_stateful_openai(
                session_id=session_id,
                message=message,
                history=history,
                system=system,
                max_tokens=_max_tokens,
                timeout=25.0,
            )
            answer, tasks_queued = await _extract_and_queue_tasks(openai_result.text)
            assistant_phase = _normalize_chat_phase(openai_result.phase)
            assistant_metadata = _build_assistant_turn_metadata(
                provider="openai",
                model=AI_CONSENSUS_DEFAULTS.openai,
                lane=describe_model_lane(AI_CONSENSUS_DEFAULTS.openai, get_settings()),
                response_id=openai_result.response_id,
                stateful=True,
                used_previous_response_id=openai_result.used_previous_response_id,
                input_tokens=openai_result.input_tokens,
                output_tokens=openai_result.output_tokens,
            )
            await _persist_messages(
                session_id,
                message,
                answer,
                assistant_phase=assistant_phase,
                assistant_metadata=assistant_metadata,
            )
            return {
                "response": answer,
                "tasks_queued": tasks_queued,
                "phase": assistant_phase,
                **assistant_metadata,
            }
        except Exception as exc:
            logger.warning(
                "Stateful OpenAI chat failed for %s; falling back to consensus: %s",
                session_id,
                exc,
            )
            await _reset_openai_chat_state(
                session_id,
                reason="stateful_openai_failure",
            )

    engine = get_consensus_engine()
    result = await engine.query(
        prompt=prompt,
        mode=ConsensusMode.FASTEST,
        system=system,
        max_tokens=_max_tokens,
        timeout=25.0,
    )

    if result.providers_succeeded == 0:
        # Final fallback to gemini_service direct
        if gemini_service is not None:
            try:
                response = await gemini_service.analyze_text(message)
                answer, tasks_queued = await _extract_and_queue_tasks(response)
                await _reset_openai_chat_state(
                    session_id,
                    reason="gemini_fallback_response",
                )
                assistant_metadata = _build_assistant_turn_metadata(
                    provider="gemini",
                    model=getattr(gemini_service, "model_name", None),
                    lane=describe_model_lane(
                        str(getattr(gemini_service, "model_name", "")),
                        get_settings(),
                    ),
                )
                await _persist_messages(
                    session_id,
                    message,
                    answer,
                    assistant_phase="final_answer",
                    assistant_metadata=assistant_metadata,
                )
                return {
                    "response": answer,
                    "tasks_queued": tasks_queued,
                    "phase": "final_answer",
                    **assistant_metadata,
                }
            except Exception:
                pass
        raise HTTPException(status_code=503, detail="All AI providers unavailable.")

    answer, tasks_queued = await _extract_and_queue_tasks(result.answer)
    await _reset_openai_chat_state(session_id, reason="consensus_response")
    provider_used = (
        result.provider_used if isinstance(result.provider_used, str) else "consensus"
    )
    provider_status = engine.get_status().get("providers", {}).get(provider_used, {})
    assistant_metadata = _build_assistant_turn_metadata(
        provider=provider_used,
        model=str(provider_status.get("model"))
        if provider_status.get("model")
        else None,
        lane=str(provider_status.get("lane")) if provider_status.get("lane") else None,
    )
    await _persist_messages(
        session_id,
        message,
        answer,
        assistant_phase="final_answer",
        assistant_metadata=assistant_metadata,
    )
    return {
        "response": answer,
        "tasks_queued": tasks_queued,
        "phase": "final_answer",
        **assistant_metadata,
    }


@router.post("/chat/stream", response_model=None)
async def stream_chat_with_gemini(payload: dict[str, Any]) -> StreamingResponse:
    """Stream Kor'tana chat over SSE, using GPT-5 deltas when available."""
    message = payload.get("message")
    if not message:
        raise HTTPException(
            status_code=400, detail="Missing 'message' field in payload"
        )

    history: list[dict[str, str]] = payload.get("history") or []
    session_id: str = payload.get("session_id") or "default"

    async def generate() -> AsyncGenerator[str, None]:
        try:
            live_context = await _build_live_context(session_id=session_id)

            if _is_kortana_identity_query(message):
                answer = _build_identity_response(live_context)
                await _reset_openai_chat_state(
                    session_id, reason="identity_short_circuit"
                )
                assistant_metadata = _build_assistant_turn_metadata(provider="identity")
                await _persist_messages(
                    session_id,
                    message,
                    answer,
                    assistant_phase="final_answer",
                    assistant_metadata=assistant_metadata,
                )
                yield _sse_event("start", assistant_metadata)
                yield _sse_event(
                    "final",
                    {
                        "response": answer,
                        "tasks_queued": [],
                        "phase": "final_answer",
                        **assistant_metadata,
                    },
                )
                return

            _stream_voice_mode: bool = bool(payload.get("voice_mode"))
            system = await _assemble_chat_system_prompt(
                live_context,
                session_id=session_id,
                query=message,
                include_conversation_memory=True,
                include_revelations=not _stream_voice_mode,
            )
            if _stream_voice_mode:
                system += (
                    "\n\nVOICE MODE: this response will be spoken aloud via text-to-speech. "
                    "keep your answer to 1-2 sentences maximum. no lists, no markdown, no code blocks. "
                    "speak directly and naturally, as if you're in the room."
                )
            prompt = _build_chat_prompt(message, history)
            _stream_max_tokens = 120 if _stream_voice_mode else 512

            if _stateful_openai_chat_enabled(payload):
                base_metadata = _build_assistant_turn_metadata(
                    provider="openai",
                    model=AI_CONSENSUS_DEFAULTS.openai,
                    lane=describe_model_lane(
                        AI_CONSENSUS_DEFAULTS.openai, get_settings()
                    ),
                    stateful=True,
                )
                yield _sse_event("start", base_metadata)
                yield _sse_event("phase", {"phase": "commentary"})

                try:
                    openai_result: OpenAITextGenerationResult | None = None
                    async for event in _stream_stateful_openai(
                        session_id=session_id,
                        message=message,
                        history=history,
                        system=system,
                        max_tokens=_stream_max_tokens,
                        timeout=25.0,
                    ):
                        event_type = str(event.get("type", ""))
                        if event_type == "delta":
                            delta = str(event.get("delta", "") or "")
                            if delta:
                                yield _sse_event("delta", {"delta": delta})
                        elif event_type == "completed":
                            result = event.get("result")
                            if isinstance(result, OpenAITextGenerationResult):
                                openai_result = result

                    if openai_result is not None:
                        answer, tasks_queued = await _extract_and_queue_tasks(
                            openai_result.text
                        )
                        assistant_phase = _normalize_chat_phase(openai_result.phase)
                        assistant_metadata = _build_assistant_turn_metadata(
                            provider="openai",
                            model=AI_CONSENSUS_DEFAULTS.openai,
                            lane=describe_model_lane(
                                AI_CONSENSUS_DEFAULTS.openai, get_settings()
                            ),
                            response_id=openai_result.response_id,
                            stateful=True,
                            used_previous_response_id=openai_result.used_previous_response_id,
                            input_tokens=openai_result.input_tokens,
                            output_tokens=openai_result.output_tokens,
                        )
                        await _persist_messages(
                            session_id,
                            message,
                            answer,
                            assistant_phase=assistant_phase,
                            assistant_metadata=assistant_metadata,
                        )
                        yield _sse_event(
                            "final",
                            {
                                "response": answer,
                                "tasks_queued": tasks_queued,
                                "phase": assistant_phase,
                                **assistant_metadata,
                            },
                        )
                        return
                except Exception as exc:
                    logger.warning(
                        "Stateful OpenAI chat stream failed for %s; falling back: %s",
                        session_id,
                        exc,
                    )
                    await _reset_openai_chat_state(
                        session_id,
                        reason="stateful_openai_stream_failure",
                    )

            engine = get_consensus_engine()
            result = await engine.query(
                prompt=prompt,
                mode=ConsensusMode.FASTEST,
                system=system,
                max_tokens=_stream_max_tokens,
                timeout=25.0,
            )

            if result.providers_succeeded == 0:
                if gemini_service is not None:
                    try:
                        response = await gemini_service.analyze_text(message)
                        answer, tasks_queued = await _extract_and_queue_tasks(response)
                        await _reset_openai_chat_state(
                            session_id,
                            reason="gemini_fallback_response",
                        )
                        assistant_metadata = _build_assistant_turn_metadata(
                            provider="gemini",
                            model=getattr(gemini_service, "model_name", None),
                            lane=describe_model_lane(
                                str(getattr(gemini_service, "model_name", "")),
                                get_settings(),
                            ),
                        )
                        await _persist_messages(
                            session_id,
                            message,
                            answer,
                            assistant_phase="final_answer",
                            assistant_metadata=assistant_metadata,
                        )
                        yield _sse_event("start", assistant_metadata)
                        yield _sse_event(
                            "final",
                            {
                                "response": answer,
                                "tasks_queued": tasks_queued,
                                "phase": "final_answer",
                                **assistant_metadata,
                            },
                        )
                        return
                    except Exception:
                        pass

                yield _sse_event("error", {"message": "All AI providers unavailable."})
                return

            answer, tasks_queued = await _extract_and_queue_tasks(result.answer)
            await _reset_openai_chat_state(session_id, reason="consensus_response")
            provider_used = (
                result.provider_used
                if isinstance(result.provider_used, str)
                else "consensus"
            )
            provider_status = (
                engine.get_status().get("providers", {}).get(provider_used, {})
            )
            assistant_metadata = _build_assistant_turn_metadata(
                provider=provider_used,
                model=(
                    str(provider_status.get("model"))
                    if provider_status.get("model")
                    else None
                ),
                lane=(
                    str(provider_status.get("lane"))
                    if provider_status.get("lane")
                    else None
                ),
            )
            await _persist_messages(
                session_id,
                message,
                answer,
                assistant_phase="final_answer",
                assistant_metadata=assistant_metadata,
            )
            yield _sse_event("start", assistant_metadata)
            yield _sse_event(
                "final",
                {
                    "response": answer,
                    "tasks_queued": tasks_queued,
                    "phase": "final_answer",
                    **assistant_metadata,
                },
            )
        except Exception as exc:
            logger.exception("Chat stream failed for %s", session_id)
            yield _sse_event("error", {"message": _stream_error_message(exc)})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _extract_and_queue_tasks(raw: str) -> tuple[str, list[dict[str, Any]]]:
    """Strip [[TASK:{...}]] markers from raw text, inject each into the task queue.

    Returns (cleaned_text, list_of_created_tasks).
    """
    import uuid as _uuid
    from datetime import datetime as _dt

    from src.kortana.routers.task_queue import _tasks_db, slugify

    pattern = re.compile(r"\[\[TASK:(\{.*?\})\]\]", re.DOTALL)
    created: list[dict[str, Any]] = []
    to_persist: list[dict[str, Any]] = []

    def _inject(match: re.Match[str]) -> str:  # type: ignore[type-arg]
        raw_json = match.group(1)
        try:
            data = json.loads(raw_json)
            task_id = str(_uuid.uuid4())
            short_id = task_id[:8]
            name = data.get("name", "kortana-self-task")
            description = data.get("description", "")
            branch = f"evolution/{short_id}-{slugify(name)}"
            task: dict[str, Any] = {
                "id": short_id,
                "name": name,
                "description": description,
                "classification": "auto",
                "status": "pending",
                "command": None,
                "branch": branch,
                "created_at": _dt.utcnow(),
                "completed_at": None,
                "source": "self_directed",
            }
            _tasks_db[short_id] = task
            created.append({"id": short_id, "name": name, "branch": branch})
            to_persist.append(
                {
                    "id": task_id,
                    "name": name,
                    "description": description,
                    "branch": branch,
                    "created_at": _dt.utcnow(),
                }
            )
        except Exception:
            pass
        return ""  # strip marker from visible text

    cleaned = pattern.sub(_inject, raw).strip()

    # Write to DB best-effort so tasks survive restarts
    if to_persist:
        try:
            from sqlalchemy import text as _text

            from src.kortana.database import get_db_manager

            db = get_db_manager()
            async with db.session_scope() as s:
                for t in to_persist:
                    await s.execute(
                        _text(
                            "INSERT INTO autonomous_tasks (id, name, description, branch, status, source, created_at) "
                            "VALUES (:id, :name, :desc, :branch, 'pending', 'self_directed', :created_at)"
                        ),
                        {
                            "id": t["id"],
                            "name": t["name"],
                            "desc": t["description"],
                            "branch": t["branch"],
                            "created_at": t["created_at"],
                        },
                    )
        except Exception:
            pass  # best-effort, never break chat

    return cleaned, created


async def _persist_messages(
    session_id: str,
    user_msg: str,
    assistant_msg: str,
    *,
    assistant_phase: str = "final_answer",
    assistant_metadata: dict[str, Any] | None = None,
) -> None:
    """Write a user+assistant exchange to conversation_messages."""
    try:
        import uuid as _uuid
        from datetime import datetime as _dt

        from sqlalchemy import text as _text

        from src.kortana.database import get_db_manager

        db = get_db_manager()
        assistant_id = str(_uuid.uuid4())
        created_at = _dt.utcnow()
        async with db.session_scope() as session:
            await session.execute(
                _text(
                    "INSERT INTO conversation_messages (id, session_id, role, content, created_at) "
                    "VALUES (:id1, :sid, 'user', :user_msg, :created_at), "
                    "       (:id2, :sid, 'assistant', :asst_msg, :created_at)"
                ),
                {
                    "id1": str(_uuid.uuid4()),
                    "id2": assistant_id,
                    "sid": session_id,
                    "user_msg": user_msg,
                    "asst_msg": assistant_msg,
                    "created_at": created_at,
                },
            )
            session.add(
                AuditLog(
                    action=_CONVERSATION_MESSAGE_META_ACTION,
                    resource_type="conversation_message",
                    resource_id=assistant_id,
                    details={
                        "session_id": session_id,
                        "phase": _normalize_chat_phase(assistant_phase),
                        **(assistant_metadata or {}),
                    },
                )
            )
    except Exception as _e:
        pass  # persistence is best-effort, never break chat


@router.get("/chat/history")
async def get_chat_history(
    session_id: str = "default", limit: int = 40
) -> dict[str, Any]:
    """Return the last N messages for a session (oldest first)."""
    try:
        from sqlalchemy import select
        from sqlalchemy import text as _text

        from src.kortana.database import get_db_manager

        db = get_db_manager()
        async with db.session_scope() as session:
            result = await session.execute(
                _text(
                    "SELECT id, role, content, created_at FROM ("
                    "  SELECT id, role, content, created_at FROM conversation_messages "
                    "  WHERE session_id = :sid ORDER BY created_at DESC LIMIT :lim"
                    ") sub ORDER BY created_at ASC"
                ),
                {"sid": session_id, "lim": limit},
            )
            rows = result.fetchall()
            assistant_ids = [str(r[0]) for r in rows if r[1] == "assistant"]
            phase_by_message_id: dict[str, str] = {}
            metadata_by_message_id: dict[str, dict[str, Any]] = {}
            if assistant_ids:
                audit_result = await session.execute(
                    select(AuditLog)
                    .where(
                        AuditLog.action.in_(
                            [
                                _CONVERSATION_MESSAGE_META_ACTION,
                                _LEGACY_CONVERSATION_MESSAGE_PHASE_ACTION,
                            ]
                        )
                    )
                    .where(AuditLog.resource_type == "conversation_message")
                    .where(AuditLog.resource_id.in_(assistant_ids))
                )
                for log in audit_result.scalars().all():
                    details: dict[str, object] = (
                        log.details if isinstance(log.details, dict) else {}
                    )
                    resource_id = str(log.resource_id)
                    metadata_by_message_id.setdefault(resource_id, {})
                    phase = details.get("phase")
                    if phase:
                        phase_by_message_id[resource_id] = _normalize_chat_phase(
                            str(phase)
                        )
                    for key in (
                        "provider",
                        "model",
                        "lane",
                        "response_id",
                        "stateful",
                        "used_previous_response_id",
                    ):
                        value = details.get(key)
                        if value is not None:
                            metadata_by_message_id[resource_id][key] = value
        messages = [
            {
                "role": r[1],
                "content": r[2],
                "created_at": r[3].isoformat(),
                "phase": (
                    phase_by_message_id.get(str(r[0]), "final_answer")
                    if r[1] == "assistant"
                    else None
                ),
                **(
                    metadata_by_message_id.get(str(r[0]), {})
                    if r[1] == "assistant"
                    else {}
                ),
            }
            for r in rows
        ]
        return {"messages": messages}
    except Exception as e:
        return {"messages": [], "error": str(e)}


@router.get("/reflections")
async def get_reflections(limit: int = 20) -> dict[str, Any]:
    """Return the last N kor'tana cycle reflections (newest first)."""
    try:
        from sqlalchemy import text as _text

        from src.kortana.database import get_db_manager

        db = get_db_manager()
        async with db.session_scope() as session:
            result = await session.execute(
                _text(
                    "SELECT content, cycle_number, tasks_completed, tasks_failed, "
                    "self_directed_completed, created_at "
                    "FROM reflections ORDER BY created_at DESC LIMIT :lim"
                ),
                {"lim": limit},
            )
            rows = result.fetchall()
        return {
            "reflections": [
                {
                    "content": r[0],
                    "cycle_number": r[1],
                    "tasks_completed": r[2],
                    "tasks_failed": r[3],
                    "self_directed_completed": r[4],
                    "created_at": r[5].isoformat(),
                }
                for r in rows
            ]
        }
    except Exception as e:
        return {"reflections": [], "error": str(e)}


@router.post("/analyze/image")
async def analyze_image(
    prompt: str = Form("Analyze this image"), image: UploadFile = File(...)
) -> dict[str, Any]:
    """Analyze an image with a prompt."""
    try:
        image_data = await image.read()
        pil_image = PIL.Image.open(io.BytesIO(image_data))
        response = await gemini_service.analyze_multimodal(prompt, [pil_image])
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/video")
async def analyze_video(
    prompt: str = Form("Analyze this video"), video: UploadFile = File(...)
) -> dict[str, Any]:
    """Analyze a video with a prompt."""
    import os
    import shutil
    from pathlib import Path

    temp_path = Path(f"temp_{video.filename}")
    try:
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # Gemini requires uploading video via the File API for best results
        import google.generativeai as genai

        uploaded_file = genai.upload_file(str(temp_path))

        # Wait for processing if needed (basic implementation)
        response = await gemini_service.analyze_multimodal(prompt, [uploaded_file])

        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            os.remove(temp_path)


@router.get("/models")
async def list_models() -> dict[str, Any]:
    """List available Gemini models."""
    try:
        import google.generativeai as genai

        models = []
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                models.append(
                    {
                        "name": m.name,
                        "display_name": m.display_name,
                        "description": m.description,
                    }
                )
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
