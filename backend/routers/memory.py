from typing import Any

from fastapi import APIRouter

router = APIRouter()

# Placeholder for knowledge base - in production, use a database
knowledge_base: list[Any] = []


@router.get("/documents")
async def get_documents():
    """Retrieve all documents in knowledge base."""
    return {"documents": knowledge_base}


@router.post("/add_document")
async def add_document(payload: dict):
    """Add a document to the knowledge base."""
    title = payload.get("title", "")
    content = payload.get("content", "")
    doc = {"title": title, "content": content, "id": len(knowledge_base)}
    knowledge_base.append(doc)
    return {"message": "Document added", "document": doc}


@router.post("/search")
async def search_documents(payload: dict):
    """Search knowledge base."""
    query = payload.get("query", "").lower()
    results = [
        doc
        for doc in knowledge_base
        if query in doc["content"].lower() or query in doc["title"].lower()
    ]
    return {"query": query, "results": results}
