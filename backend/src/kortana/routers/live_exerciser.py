"""
KOR'TANA Live Exerciser — Real External API & PostgreSQL Integration
Exercises real connections: PostgreSQL, Redis, Gemini (free), Groq (free), GitHub API.
"""

import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.database import get_db
from src.kortana.models import Agent, AuditLog, Memory, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/live", tags=["live-exerciser"])

SYSTEM_USER_ID = "kor-system-user-0001"
SYSTEM_AGENT_ID = "kortana-system"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
async def _ensure_bootstrap(db: AsyncSession) -> dict[str, str]:
    """Create the system user and agent if they don't exist."""
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
        agent = Agent(
            id=SYSTEM_AGENT_ID,
            owner_id=SYSTEM_USER_ID,
            name="KOR'TANA Prime",
            description="Autonomous system agent",
            model="gemini-3.1-flash-lite-preview",
            system_prompt="You are KOR'TANA, an autonomous AI agent.",
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
        return {
            "status": "ok",
            "url": url.split("@")[-1] if "@" in url else url,
            "roundtrip_value": val.decode() if val else None,
            "latency_ms": round(latency, 1),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        }


async def _exercise_gemini_embedding() -> dict[str, Any]:
    """Generate a real embedding via Gemini gemini-embedding-001 (free tier)."""
    t0 = time.perf_counter()
    try:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"status": "skip", "reason": "No GEMINI_API_KEY"}

        from google import genai

        client = genai.Client(api_key=api_key)
        resp = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents="KOR'TANA autonomous agent live exercise",
        )
        embeddings = resp.embeddings
        if not embeddings:
            return {"status": "error", "error": "Empty embedding response"}
        embedding = embeddings[0].values
        latency = (time.perf_counter() - t0) * 1000
        return {
            "status": "ok",
            "model": "gemini-embedding-001",
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

        import groq

        client = groq.Groq(api_key=api_key)
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": "Reply in exactly 5 words: What is an autonomous AI agent?",
                }
            ],
            max_tokens=30,
        )
        text_out = resp.choices[0].message.content if resp.choices else "(empty)"
        latency = (time.perf_counter() - t0) * 1000
        return {
            "status": "ok",
            "model": "llama-3.3-70b-versatile",
            "response": text_out[:200],
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
        owner = os.getenv("GITHUB_OWNER", "KOR-TANA")
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

        latency = (time.perf_counter() - t0) * 1000
        return {
            "status": "ok",
            "memory_id": mem.id,
            "has_embedding": bool(stored.embedding) if stored else False,
            "embedding_dims": len(stored.embedding)
            if stored and isinstance(stored.embedding, list)
            else 0,
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

    # 7. GitHub API (free)
    results["github"] = await _exercise_github()

    # 8. Memory store with real embedding
    embedding = None
    if emb_result.get("status") == "ok":
        # Re-use the embedding we already generated
        try:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            from google import genai

            client = genai.Client(api_key=api_key)
            resp = client.models.embed_content(
                model="models/gemini-embedding-001",
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
    }

    logger.info(
        f"Live exercise complete: {ok_count}/{total_services} OK in {total_ms:.0f}ms"
    )
    return results


@router.get("/status")
async def quick_status(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Quick connectivity check for all external dependencies."""
    checks: dict[str, Any] = {}

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
    checks["gemini_key"] = "ok" if os.getenv("GEMINI_API_KEY") else "missing"

    # Groq API key present
    checks["groq_key"] = "ok" if os.getenv("GROQ_API_KEY") else "missing"

    # GitHub token present
    checks["github_token"] = "ok" if os.getenv("GITHUB_TOKEN") else "missing"

    return {
        "status": "all_ok" if all(v == "ok" for v in checks.values()) else "degraded",
        "checks": checks,
    }
