"""
Financial Analysis API Routes — Bridge Architecture
───────────────────────────────────────────────────
Financial analysis endpoints now support Bridge-powered routes.
"""
import os
import uuid
import tempfile
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_bridge_client
from app.services.bridge_client import BridgeClient

from app.schemas.financial_analysis_schema import (
    FinancialAnalysisCreate,
    FinancialAnalysisResponse,
    FinancialAnalysisSummary,
    CalculationDetailsResponse,
)

router = APIRouter()


# ════════════════════════════════════════════════════════════════════
#  BRIDGE-POWERED ROUTES (no connector_id)
# ════════════════════════════════════════════════════════════════════

@router.post("/bridge/analysis", response_model=dict)
async def create_analysis_bridge(
    analysis_in: FinancialAnalysisCreate,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Create a new financial analysis via the Bridge."""
    return await bridge.post("/financial-analysis/profiles", analysis_in.model_dump())


@router.get("/bridge/analysis", response_model=list)
async def list_analyses_bridge(
    client_id: Optional[str] = None,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """List all financial analyses via the Bridge."""
    params = {}
    if client_id:
        params["client_id"] = client_id
    path = f"/financial-analysis/profiles/{client_id}" if client_id else "/financial-analysis/profiles"
    return await bridge.get(path, params=params)


@router.get("/bridge/analysis/{result_id}", response_model=dict)
async def get_analysis_bridge(
    result_id: str,
    bridge: BridgeClient = Depends(get_bridge_client),
):
    """Get a financial analysis result by ID via the Bridge."""
    return await bridge.get(f"/financial-analysis/results/{result_id}")
