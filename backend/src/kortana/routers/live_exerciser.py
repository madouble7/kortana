"""
KOR'TANA Live Exerciser — Real External API & PostgreSQL Integration
Exercises real connections: PostgreSQL, Redis, Gemini (free), Groq (free), GitHub API.
"""

import logging
import os
import time
import uuid
import asyncio
from datetime import datetime
from typing import Any, cast

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.database import get_db
from src.kortana.model_lane_policy import (
    describe_model_lane,
    get_active_model_lane,
    model_allowed,
)
from src.kortana.models import Agent, AuditLog, Memory, User
from src.kortana.openai_responses import sync_generate_turn
from src.kortana.provider_model_defaults import (
    GEMINI_EMBEDDING_MODEL_NAME,
    GEMINI_EMBEDDING_MODEL_PATH,
    GROQ_LLAMA_VERSATILE_MODEL,
    OPENAI_FAST_MODEL,
)
from src.kortana.voice_definition import KORTANA_BRIEF_IDENTITY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live", tags=["live-exerciser"])

SYSTEM_USER_ID = "kor-system-user-0001"
SYSTEM_AGENT_ID = "kortana-system"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
async def _ensure_bootstrap(db: AsyncSession) -> dict[str, str]:
    """Create the system user and agent if they don't exist."""
    from src.kortana.services.gemini_config import get_model_name

    result = await db.execute(select(User).where(User.id == SYSTEM_USER_ID))
    user = result.scalars().first()
    if not user:
        user = User(
            id=SYSTEM_USER_ID,
            email="system@kortana.local",
            username="kortana-system",
            hashed_password="!system-no-login",
            full_name="KOR'TANA System",
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        await db.flush()

    agent_result = await db.execute(select(Agent).where(Agent.id == SYSTEM_AGENT_ID))
    agent = agent_result.scalars().first()
    if not agent:
        system_model = get_model_name()
        agent = Agent(
            id=SYSTEM_AGENT_ID,
            owner_id=SYSTEM_USER_ID,
            name="KOR'TANA Prime",
            description="Autonomous system agent",
            model=system_model,
            system_prompt=KORTANA_BRIEF_IDENTITY,
            is_active=True,
        )
        db.add(agent)
        await db.flush()

    await db.commit()
    return {"user_id": SYSTEM_USER_ID, "agent_id": SYSTEM_AGENT_ID}


async def _exercise_postgresql(db: AsyncSession) -> dict[str, Any]:
    """Test PostgreSQL read/write with real data."""
    t0 = time.perf_counter()
    try:
        row = await db.execute(text("SELECT version()"))
        pg_version = row.scalar()

        row = await db.execute(text("SELECT count(*) FROM memories"))
        mem_count = row.scalar()

        row = await db.execute(text("SELECT count(*) FROM audit_logs"))
        log_count = row.scalar() or 0

        # Write a real audit log entry
        log_entry = AuditLog(
            id=str(uuid.uuid4()),
            action="live_exerciser",
            resource_type="system",
            resource_id="exercise",
            details={
                "event": "postgresql_exercise",
                "timestamp": datetime.utcnow().isoformat(),
            },
            created_at=datetime.utcnow(),
        )
        db.add(log_entry)
        await db.flush()

        latency = (time.perf_counter() - t0) * 1000
        return {
            "status": "ok",
            "engine": "PostgreSQL",
            "version": pg_version,
            "memories": mem_count,
            "audit_logs": int(log_count) + 1,
            "latency_ms": round(latency, 1),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }


async def _exercise_redis() -> dict[str, Any]:
    """Test Redis connectivity."""
    t0 = time.perf_counter()
    try:
        import redis as redis_lib

        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis_lib.from_url(url, socket_timeout=5)
        r.ping()
        test_key = "kortana:live_exercise"
        r.set(test_key, datetime.utcnow().isoformat(), ex=60)
        val = r.get(test_key)
        latency = (time.perf_counter() - t0) * 1000
        decoded_val = val.decode() if isinstance(val, (bytes, bytearray)) else val
        return {
            "status": "ok",
            "url": url.split("@")[-1] if "@" in url else url,
            "roundtrip_value": decoded_val,
            "latency_ms": round(latency, 1),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }


async def _exercise_gemini_embedding() -> dict[str, Any]:
    """Generate a real embedding via the shared Gemini embedding model."""
    t0 = time.perf_counter()
    try:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"status": "skip", "reason": "No GEMINI_API_KEY"}

        from google import genai

        client = genai.Client(api_key=api_key)
        resp = client.models.embed_content(
            model=GEMINI_EMBEDDING_MODEL_PATH,
            contents="KOR'TANA autonomous agent live exercise",
        )
        embeddings = resp.embeddings
        if not embeddings:
            return {"status": "error", "error": "Empty embedding response"}
        embedding = embeddings[0].values
        latency = (time.perf_counter() - t0) * 1000
        return {
            "status": "ok",
            "model": GEMINI_EMBEDDING_MODEL_NAME,
            "dimensions": len(embedding) if embedding else 0,
            "sample": list(embedding[:5]) if embedding else [],
            "latency_ms": round(latency, 1),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }


async def _exercise_gemini_generate() -> dict[str, Any]:
    """Generate text via Gemini (free tier)."""
    t0 = time.perf_counter()
    try:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"status": "skip", "reason": "No GEMINI_API_KEY"}

        from google import genai

        from src.kortana.services.gemini_config import get_model_name

        client = genai.Client(api_key=api_key)
        model = get_model_name()
        resp = client.models.generate_content(
            model=f"models/{model}",
            contents="Reply in exactly 10 words: What is KOR'TANA?",
        )
        text_out = resp.text if resp else "(empty)"
        latency = (time.perf_counter() - t0) * 1000
        return {
            "status": "ok",
            "model": model,
            "model_lane": describe_model_lane(model),
            "response": (text_out or "(empty)")[:200],
            "latency_ms": round(latency, 1),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }


async def _exercise_groq() -> dict[str, Any]:
    """Generate text via Groq free tier."""
    t0 = time.perf_counter()
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"status": "skip", "reason": "No GROQ_API_KEY"}

        model_name = GROQ_LLAMA_VERSATILE_MODEL
        if not model_allowed(model_name):
            return {
                "status": "skip",
                "reason": "Groq model unavailable under active lane",
                "model": model_name,
                "model_lane": describe_model_lane(model_name),
            }

        import groq

        client = groq.Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": "Reply in exactly 5 words: What is an autonomous AI agent?",
                }
            ],
            max_tokens=30,
        )
        text_out = (
            str(resp.choices[0].message.content or "") if resp.choices else "(empty)"
        )
        latency = (time.perf_counter() - t0) * 1000
        return {
            "status": "ok",
            "model": model_name,
            "model_lane": describe_model_lane(model_name),
            "response": text_out[:200],
            "latency_ms": round(latency, 1),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }


async def _exercise_openai() -> dict[str, Any]:
    """Generate text via the shared OpenAI GPT-5 fast worker path."""
    t0 = time.perf_counter()
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"status": "skip", "reason": "No OPENAI_API_KEY"}

        model_name = OPENAI_FAST_MODEL
        if not model_allowed(model_name):
            return {
                "status": "skip",
                "reason": "OpenAI model unavailable under active lane",
                "model": model_name,
                "model_lane": describe_model_lane(model_name),
            }

        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        result = await asyncio.to_thread(
            sync_generate_turn,
            client,
            model_name=model_name,
            prompt="Reply in exactly 6 words: Why does Kor'tana use model lanes?",
            max_output_tokens=40,
        )
        latency = (time.perf_counter() - t0) * 1000
        return {
            "status": "ok",
            "model": model_name,
            "model_lane": describe_model_lane(model_name),
            "response": result.text[:200],
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "response_id": result.response_id,
            "phase": result.phase,
            "latency_ms": round(latency, 1),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }


async def _exercise_github() -> dict[str, Any]:
    """Hit GitHub API to check repo status (free, 5000 req/hr)."""
    t0 = time.perf_counter()
    try:
        token = os.getenv("GITHUB_TOKEN")
        owner = os.getenv("GITHUB_OWNER", "madouble7")
        repo = os.getenv("GITHUB_REPO", "kortana")
        if not token:
            return {"status": "skip", "reason": "No GITHUB_TOKEN"}

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        latency = (time.perf_counter() - t0) * 1000
        return {
            "status": "ok",
            "repo": data.get("full_name"),
            "stars": data.get("stargazers_count"),
            "open_issues": data.get("open_issues_count"),
            "default_branch": data.get("default_branch"),
            "latency_ms": round(latency, 1),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }


async def _exercise_memory_store(
    db: AsyncSession, embedding: list[float] | None
) -> dict[str, Any]:
    """Store a real memory with embedding in PostgreSQL."""
    t0 = time.perf_counter()
    try:
        mem = Memory(
            id=str(uuid.uuid4()),
            agent_id=SYSTEM_AGENT_ID,
            memory_type="long_term",
            content=f"Live exerciser checkpoint at {datetime.utcnow().isoformat()}",
            embedding=embedding,
            created_at=datetime.utcnow(),
        )
        db.add(mem)
        await db.flush()

        # Read it back
        result = await db.execute(select(Memory).where(Memory.id == mem.id))
        stored = result.scalars().first()
        raw_embedding = stored.embedding if stored is not None else None
        if isinstance(raw_embedding, list):
            stored_embedding = cast(list[float], raw_embedding)
            embedding_dims = len(stored_embedding)
        else:
            stored_embedding = None
            embedding_dims = 0

        latency = (time.perf_counter() - t0) * 1000
        return {
            "status": "ok",
            "memory_id": mem.id,
            "has_embedding": bool(stored_embedding),
            "embedding_dims": embedding_dims,
            "latency_ms": round(latency, 1),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------
@router.post("/exercise")
async def run_full_exercise(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Run a full live exercise across all external services.
    Exercises: PostgreSQL, Redis, Gemini Embedding, Gemini Generate, Groq, GitHub API.
    Writes real data to the database.
    """
    t_total = time.perf_counter()
    results: dict[str, Any] = {"timestamp": datetime.utcnow().isoformat()}

    # 1. Bootstrap system user/agent
    bootstrap = await _ensure_bootstrap(db)
    results["bootstrap"] = bootstrap

    # 2. PostgreSQL
    results["postgresql"] = await _exercise_postgresql(db)

    # 3. Redis
    results["redis"] = await _exercise_redis()

    # 4. Gemini Embedding (free)
    emb_result = await _exercise_gemini_embedding()
    results["gemini_embedding"] = emb_result

    # 5. Gemini Generate (free)
    results["gemini_generate"] = await _exercise_gemini_generate()

    # 6. Groq (free)
    results["groq"] = await _exercise_groq()

    # 7. OpenAI fast worker lane
    results["openai"] = await _exercise_openai()

    # 8. GitHub API (free)
    results["github"] = await _exercise_github()

    # 9. Memory store with real embedding
    embedding = None
    if emb_result.get("status") == "ok":
        # Re-use the embedding we already generated
        try:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            from google import genai

            client = genai.Client(api_key=api_key)
            resp = client.models.embed_content(
                model=GEMINI_EMBEDDING_MODEL_PATH,
                contents=f"Live exerciser memory at {datetime.utcnow().isoformat()}",
            )
            emb_list = resp.embeddings
            if emb_list:
                raw = emb_list[0].values
                # Validate it's actually a list of numbers
                if isinstance(raw, list) and all(
                    isinstance(v, (int, float)) for v in raw[:5]
                ):
                    embedding = raw
        except Exception:
            pass
    results["memory_store"] = await _exercise_memory_store(db, embedding)

    await db.commit()

    total_ms = (time.perf_counter() - t_total) * 1000
    ok_count = sum(
        1 for k, v in results.items() if isinstance(v, dict) and v.get("status") == "ok"
    )
    total_services = sum(
        1 for k, v in results.items() if isinstance(v, dict) and "status" in v
    )
    results["summary"] = {
        "total_ms": round(total_ms, 1),
        "services_ok": ok_count,
        "services_total": total_services,
        "all_green": ok_count == total_services,
        "model_usage_lane": get_active_model_lane().value,
    }

    logger.info(
        f"Live exercise complete: {ok_count}/{total_services} OK in {total_ms:.0f}ms"
    )
    return results


@router.get("/status")
async def quick_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Quick connectivity check for all external dependencies."""
    checks: dict[str, Any] = {}
    model_usage_lane = get_active_model_lane().value

    # PostgreSQL
    try:
        row = await db.execute(text("SELECT 1"))
        checks["postgresql"] = "ok" if row.scalar() == 1 else "error"
    except Exception:
        checks["postgresql"] = "error"

    # Redis
    try:
        import redis as redis_lib

        r = redis_lib.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"), socket_timeout=3
        )
        r.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    # Gemini API key present
    checks["gemini_key"] = (
        "ok"
        if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        else "missing"
    )

    # Groq API key present
    checks["groq_key"] = "ok" if os.getenv("GROQ_API_KEY") else "missing"

    # OpenAI API key present
    checks["openai_key"] = "ok" if os.getenv("OPENAI_API_KEY") else "missing"

    # GitHub token present
    checks["github_token"] = "ok" if os.getenv("GITHUB_TOKEN") else "missing"

    models = {
        "gemini_generate": {
            "model": None,
            "lane": None,
        },
        "groq_generate": {
            "model": GROQ_LLAMA_VERSATILE_MODEL,
            "lane": describe_model_lane(GROQ_LLAMA_VERSATILE_MODEL),
            "allowed": model_allowed(GROQ_LLAMA_VERSATILE_MODEL),
        },
        "openai_generate": {
            "model": OPENAI_FAST_MODEL,
            "lane": describe_model_lane(OPENAI_FAST_MODEL),
            "allowed": model_allowed(OPENAI_FAST_MODEL),
        },
    }
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        from src.kortana.services.gemini_config import get_model_name

        gemini_model = get_model_name()
        models["gemini_generate"] = {
            "model": gemini_model,
            "lane": describe_model_lane(gemini_model),
            "allowed": model_allowed(gemini_model),
        }

    return {
        "status": "all_ok" if all(v == "ok" for v in checks.values()) else "degraded",
        "model_usage_lane": model_usage_lane,
        "checks": checks,
        "models": models,
    }
