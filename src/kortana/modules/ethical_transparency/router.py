"""
Ethical Transparency API Router for Kor'tana
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .decision_logger import EthicalDecisionLogger, EthicalDecisionType
from .transparency_service import TransparencyService

router = APIRouter(prefix="/api/ethics", tags=["ethical-transparency"])

decision_logger = EthicalDecisionLogger()
transparency_service = TransparencyService(decision_logger)


class LogDecisionRequest(BaseModel):
    decision_type: EthicalDecisionType
    context: str
    decision: str
    reasoning: str
    confidence: float = 0.8


class FeedbackRequest(BaseModel):
    decision_id: str
    feedback: str


@router.post("/log-decision")
async def log_decision(request: LogDecisionRequest):
    """Log an ethical decision"""
    try:
        decision_id = decision_logger.log_decision(
            request.decision_type,
            request.context,
            request.decision,
            request.reasoning,
            request.confidence,
        )
        return {"decision_id": decision_id, "status": "logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions")
async def get_all_decisions():
    """Get all ethical decisions"""
    try:
        decisions = decision_logger.get_all_decisions()
        return {"decisions": decisions, "count": len(decisions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/recent")
async def get_recent_decisions(limit: int = 10):
    """Get recent ethical decisions"""
    try:
        decisions = decision_logger.get_recent_decisions(limit)
        return {"decisions": decisions, "count": len(decisions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decisions/{decision_id}")
async def get_decision(decision_id: str):
    """Get a specific ethical decision"""
    try:
        decision = decision_logger.get_decision(decision_id)
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        return decision.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback on an ethical decision"""
    try:
        success = decision_logger.add_feedback(request.decision_id, request.feedback)
        if not success:
            raise HTTPException(status_code=404, detail="Decision not found")
        return {"decision_id": request.decision_id, "status": "feedback_added"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report")
async def get_transparency_report():
    """Get comprehensive transparency report"""
    try:
        report = transparency_service.generate_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breakdown")
async def get_decision_breakdown():
    """Get detailed breakdown of decisions by type"""
    try:
        breakdown = transparency_service.get_decision_breakdown()
        return breakdown
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
