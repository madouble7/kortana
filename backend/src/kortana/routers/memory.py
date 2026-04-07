from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

# Placeholder for knowledge base - in production, use a database
knowledge_base: list[Any] = []

_MAX_TITLE_LEN = 500
_MAX_CONTENT_LEN = 51_200  # 50 KB


class DocumentIn(BaseModel):
    title: str = Field("", max_length=_MAX_TITLE_LEN)
    content: str = Field("", max_length=_MAX_CONTENT_LEN)


@router.get("/documents")
async def get_documents():
    """Retrieve all documents in knowledge base."""
    return {"documents": knowledge_base}


@router.post("/add_document")
async def add_document(payload: DocumentIn):
    """Add a document to the knowledge base."""
    doc = {
        "id": len(knowledge_base),
        "title": payload.title,
        "content": payload.content,
    }
    knowledge_base.append(doc)
    return {"message": "Document added", "document": doc}


@router.get("/search")
async def search_documents_get(query: str):
    """Search knowledge base via GET."""
    if len(query) > 500:
        raise HTTPException(status_code=422, detail="Query too long (max 500 chars)")
    q = query.lower()
    results = [
        doc
        for doc in knowledge_base
        if q in doc["content"].lower() or q in doc["title"].lower()
    ]
    return {"query": query, "results": results}


@router.post("/search")
async def search_documents(payload: dict):
    """Search knowledge base."""
    query = str(payload.get("query", ""))[:500].lower()
    results = [
        doc
        for doc in knowledge_base
        if query in doc["content"].lower() or query in doc["title"].lower()
    ]
    return {"query": query, "results": results}
