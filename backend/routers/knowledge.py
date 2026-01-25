from fastapi import APIRouter, HTTPException
import os
import json
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

router = APIRouter()

KORTANA_BACKEND_URL = os.getenv("KORTANA_BACKEND_URL", "http://localhost:8000")

# In-memory knowledge base (in production, use vector database like ChromaDB)
knowledge_base: List[Dict[str, Any]] = []
ritual_documents: List[Dict[str, Any]] = []

class KnowledgeManager:
    def __init__(self):
        self.knowledge = knowledge_base
        self.rituals = ritual_documents

    def extract_insights(self, content: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extract learnings and insights from development activities."""
        prompt = f"""
        Extract key insights, lessons learned, and best practices from this development content:

        Source: {source}
        Content: {content}

        Focus on:
        1. Technical patterns or solutions
        2. Problems encountered and solutions
        3. Code quality improvements
        4. Development process optimizations
        5. Architectural decisions

        Provide insights in a structured format.
        """

        gemini_payload = {"text": prompt}

        try:
            response = requests.post(f"{KORTANA_BACKEND_URL}/api/gemini/analyze", json=gemini_payload)
            if response.status_code == 200:
                result = response.json()
                analysis = result.get("analysis", "Analysis failed")
            else:
                analysis = "Failed to analyze content"
        except requests.RequestException:
            analysis = "Error connecting to Gemini service"

        insight = {
            "id": hashlib.md5(f"{source}:{content[:100]}".encode()).hexdigest()[:8],
            "source": source,
            "content": content[:500],  # Truncate for storage
            "insights": analysis,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "tags": self._extract_tags(content, analysis)
        }

        return insight

    def _extract_tags(self, content: str, analysis: str) -> List[str]:
        """Extract relevant tags from content and analysis."""
        tags = []
        content_lower = content.lower()
        analysis_lower = analysis.lower()

        # Technical tags
        if any(word in content_lower for word in ["api", "endpoint", "router", "backend"]):
            tags.append("backend")
        if any(word in content_lower for word in ["frontend", "react", "ui", "component"]):
            tags.append("frontend")
        if any(word in content_lower for word in ["test", "pytest", "coverage"]):
            tags.append("testing")
        if any(word in content_lower for word in ["deploy", "cloud", "docker"]):
            tags.append("deployment")

        # Process tags
        if any(word in analysis_lower for word in ["autonomous", "self", "ai"]):
            tags.append("autonomy")
        if any(word in analysis_lower for word in ["error", "fix", "bug"]):
            tags.append("debugging")
        if any(word in analysis_lower for word in ["performance", "optimize", "speed"]):
            tags.append("performance")

        return list(set(tags))  # Remove duplicates

    def ingest_learning(self, content: str, source: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Ingest new learning into the knowledge base."""
        insight = self.extract_insights(content, source, metadata)

        # Check for duplicates
        existing = next((k for k in self.knowledge if k["id"] == insight["id"]), None)
        if existing:
            # Update existing insight
            existing.update(insight)
            return {"message": "Knowledge updated", "insight": insight}
        else:
            # Add new insight
            self.knowledge.append(insight)
            return {"message": "Knowledge ingested", "insight": insight}

    def search_knowledge(self, query: str, tags: Optional[List[str]] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base for relevant insights."""
        results = []

        for item in self.knowledge:
            # Text search in content and insights
            text_match = query.lower() in item["content"].lower() or query.lower() in item["insights"].lower()

            # Tag filtering
            tag_match = True
            if tags:
                tag_match = any(tag in item.get("tags", []) for tag in tags)

            if text_match and tag_match:
                results.append(item)

        # Sort by relevance (simple: newer first)
        results.sort(key=lambda x: x["timestamp"], reverse=True)

        return results[:limit]

    def generate_ritual_document(self, milestone: str, context: str) -> Dict[str, Any]:
        """Generate a ritual document for major milestones."""
        prompt = f"""
        Create a ritual document for this milestone:

        Milestone: {milestone}
        Context: {context}

        Generate a document in the style of previous rituals (Ritual_016.md, etc.) that:
        1. Documents the achievement
        2. Reflects on lessons learned
        3. Sets intentions for future development
        4. Maintains the mythic, constellation-themed narrative

        Structure the document with appropriate sections and formatting.
        """

        gemini_payload = {"text": prompt}

        try:
            response = requests.post(f"{KORTANA_BACKEND_URL}/api/gemini/analyze", json=gemini_payload)
            if response.status_code == 200:
                result = response.json()
                content = result.get("analysis", "Ritual generation failed")
            else:
                content = "Failed to generate ritual"
        except requests.RequestException:
            content = "Error connecting to Gemini service"

        ritual_number = len(self.rituals) + 17  # Starting from 17 after 16
        ritual = {
            "id": f"ritual_{ritual_number}",
            "title": f"Ritual_{ritual_number}.md",
            "milestone": milestone,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }

        self.rituals.append(ritual)
        return ritual

    def update_covenant_index(self) -> Dict[str, Any]:
        """Update the COVENANT_INDEX.md with current knowledge state."""
        total_insights = len(self.knowledge)
        total_rituals = len(self.rituals)
        tags = set()
        for item in self.knowledge:
            tags.update(item.get("tags", []))

        covenant_update = {
            "timestamp": datetime.now().isoformat(),
            "knowledge_stats": {
                "total_insights": total_insights,
                "total_rituals": total_rituals,
                "unique_tags": list(tags),
                "recent_insights": len([k for k in self.knowledge if self._is_recent(k["timestamp"])])
            },
            "autonomy_status": "active" if total_insights > 0 else "initializing"
        }

        return covenant_update

    def _is_recent(self, timestamp: str, days: int = 7) -> bool:
        """Check if timestamp is within recent days."""
        try:
            dt = datetime.fromisoformat(timestamp)
            return (datetime.now() - dt).days <= days
        except:
            return False

# Global instance
knowledge_manager = KnowledgeManager()

@router.post("/ingest")
async def ingest_learning(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Ingest new learning into the knowledge base."""
    content = payload.get("content", "")
    source = payload.get("source", "unknown")
    metadata = payload.get("metadata")

    if not content:
        raise HTTPException(status_code=400, detail="Content is required")

    try:
        result = knowledge_manager.ingest_learning(content, source, metadata)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_knowledge(query: str, tags: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Search the knowledge base."""
    tag_list = tags.split(",") if tags else None

    try:
        results = knowledge_manager.search_knowledge(query, tag_list, limit)
        return {
            "query": query,
            "tags": tag_list,
            "total_results": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ritual")
async def generate_ritual(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a ritual document for a milestone."""
    milestone = payload.get("milestone", "")
    context = payload.get("context", "")

    if not milestone:
        raise HTTPException(status_code=400, detail="Milestone is required")

    try:
        ritual = knowledge_manager.generate_ritual_document(milestone, context)
        return {
            "message": "Ritual generated",
            "ritual": ritual
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/covenant")
async def get_covenant_status() -> Dict[str, Any]:
    """Get current covenant index status."""
    try:
        status = knowledge_manager.update_covenant_index()
        return {
            "covenant_status": status,
            "knowledge_base_size": len(knowledge_manager.knowledge),
            "ritual_count": len(knowledge_manager.rituals)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_knowledge_stats() -> Dict[str, Any]:
    """Get knowledge base statistics."""
    total_insights = len(knowledge_manager.knowledge)
    tags = {}
    sources = {}

    for item in knowledge_manager.knowledge:
        # Count tags
        for tag in item.get("tags", []):
            tags[tag] = tags.get(tag, 0) + 1

        # Count sources
        source = item.get("source", "unknown")
        sources[source] = sources.get(source, 0) + 1

    return {
        "total_insights": total_insights,
        "tag_distribution": tags,
        "source_distribution": sources,
        "recent_insights": len([k for k in knowledge_manager.knowledge if knowledge_manager._is_recent(k["timestamp"])])
    }
