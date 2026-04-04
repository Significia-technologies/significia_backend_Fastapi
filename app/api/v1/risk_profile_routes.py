"""
Risk Profile Routes — Bridge Architecture
──────────────────────────────────────────
Risk assessments are now managed through the Bridge.
The scoring calculation logic remains on the backend (it's pure math, no DB needed).
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.api.deps import get_bridge_client
from app.services.bridge_client import BridgeClient

from app.schemas.risk_profile_schema import (
    RiskAssessmentCreate, 
    RiskAssessmentCalculateRequest, 
    RiskAssessmentCalculateResponse,
    SaveAssessmentResponse,
    RiskAssessmentResponse
)
from app.schemas.custom_risk_profile_schema import (
    RiskQuestionnaireCreate,
    RiskQuestionnaireUpdate,
    RiskQuestionnaireResponse,
    CustomRiskAssessmentCreate,
    CustomRiskAssessmentResponse
)
from app.services.risk_profile_service import RiskProfileService
from app.services.custom_risk_profile_service import CustomRiskProfileService

router = APIRouter()


# ════════════════════════════════════════════════════════════════════
#  BRIDGE-POWERED ROUTES (no connector_id)
# ════════════════════════════════════════════════════════════════════

@router.post("/bridge/calculate", response_model=RiskAssessmentCalculateResponse)
def calculate_risk_profile_bridge(
    payload: RiskAssessmentCalculateRequest,
):
    """
    Dry-run calculation. This is pure math — no Bridge call needed.
    """
    total_score, question_scores = RiskProfileService.calculate_scores(payload.answers)
    risk_tier, recommendation = RiskProfileService.determine_risk_tier(total_score)
    return {
        "success": True,
        "total_score": total_score,
        "question_scores": question_scores,
        "risk_tier": risk_tier,
        "recommendation": recommendation
    }


@router.post("/bridge/save", response_model=dict)
async def save_risk_assessment_bridge(
    payload: RiskAssessmentCreate,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Save a risk assessment via the Bridge."""
    # Calculate score on the backend (it's business logic, not data)
    total_score, question_scores = RiskProfileService.calculate_scores(payload.answers)
    risk_tier, recommendation = RiskProfileService.determine_risk_tier(total_score)

    data = {
        "client_code": payload.client_code,
        "answers": payload.answers.model_dump(),
        "calculated_score": total_score,
        "question_scores": question_scores,
        "assigned_risk_tier": risk_tier,
        "tier_recommendation": recommendation,
        "disclaimer_text": payload.disclaimer_text,
        "discussion_notes": payload.discussion_notes,
        "form_name": payload.form_name,
    }
    return await bridge.post("/risk-assessments", data)


@router.get("/bridge/assessments")
@router.get("/bridge/assessments/{client_id}", response_model=list)
async def get_risk_assessments_bridge(
    client_id: Optional[str] = None,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get risk assessments for a client via the Bridge."""
    path = f"/risk-assessments/{client_id}" if client_id else "/risk-assessments"
    return await bridge.get(path)


@router.get("/bridge/questionnaires", response_model=list)
async def list_questionnaires_bridge(
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """List all risk questionnaires via the Bridge."""
    return await bridge.get("/risk-questionnaires")


@router.post("/bridge/questionnaires", response_model=dict)
async def create_questionnaire_bridge(
    payload: RiskQuestionnaireCreate,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Create a risk questionnaire via the Bridge."""
    return await bridge.post("/risk-questionnaires", payload.model_dump())


@router.get("/bridge/questionnaires/{q_id}", response_model=dict)
async def get_questionnaire_bridge(
    q_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get a risk questionnaire by ID via the Bridge."""
    return await bridge.get(f"/risk-questionnaires/{q_id}")


@router.put("/bridge/questionnaires/{q_id}", response_model=dict)
async def update_questionnaire_bridge(
    q_id: str,
    payload: RiskQuestionnaireUpdate,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Update a risk questionnaire via the Bridge."""
    return await bridge.patch(f"/risk-questionnaires/{q_id}", payload.model_dump(exclude_unset=True))


@router.post("/bridge/custom-save", response_model=dict)
async def save_custom_risk_assessment_bridge(
    payload: CustomRiskAssessmentCreate,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Save a custom risk assessment via the Bridge."""
    return await bridge.post("/custom-risk-assessments", payload.model_dump())


@router.get("/bridge/custom-assessments")
@router.get("/bridge/custom-assessments/{client_id}", response_model=list)
async def get_custom_assessments_bridge(
    client_id: Optional[str] = None,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get custom risk assessments for a client via the Bridge."""
    path = f"/custom-risk-assessments/{client_id}" if client_id else "/custom-risk-assessments"
    return await bridge.get(path)
