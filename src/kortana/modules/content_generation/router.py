"""
Content Generation API Router for Kor'tana
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .content_generator import ContentGenerator, ContentStyle

router = APIRouter(prefix="/api/content", tags=["content-generation"])

content_generator = ContentGenerator()


class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 100


class ElaborateRequest(BaseModel):
    text: str
    target_length: int = 200


class RewriteRequest(BaseModel):
    text: str
    style: ContentStyle = ContentStyle.PROFESSIONAL


class IndustryAdaptRequest(BaseModel):
    text: str
    industry: str


@router.post("/summarize")
async def summarize_text(request: SummarizeRequest):
    """Summarize text to specified length"""
    try:
        summary = content_generator.summarize(request.text, request.max_length)
        return {
            "original": request.text,
            "summary": summary,
            "max_length": request.max_length,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/elaborate")
async def elaborate_text(request: ElaborateRequest):
    """Elaborate on text to reach target length"""
    try:
        elaborated = content_generator.elaborate(request.text, request.target_length)
        return {
            "original": request.text,
            "elaborated": elaborated,
            "target_length": request.target_length,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rewrite")
async def rewrite_text(request: RewriteRequest):
    """Rewrite text in specified style"""
    try:
        rewritten = content_generator.rewrite(request.text, request.style)
        return {
            "original": request.text,
            "rewritten": rewritten,
            "style": request.style,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adapt-industry")
async def adapt_for_industry(request: IndustryAdaptRequest):
    """Adapt text for specific industry"""
    try:
        adapted = content_generator.adjust_for_industry(
            request.text, request.industry
        )
        return {
            "original": request.text,
            "adapted": adapted,
            "industry": request.industry,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
