from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from uuid import UUID
from datetime import datetime

class Q2Factors(BaseModel):
    a: Optional[str] = Field("B", description="Short-term appreciation (A/B/C)")
    b: Optional[str] = Field("B", description="Long-term appreciation (A/B/C)")
    c: Optional[str] = Field("B", description="Takeover potential (A/B/C)")
    d: Optional[str] = Field("B", description="6-month price trend (A/B/C)")
    e: Optional[str] = Field("B", description="5-year price trend (A/B/C)")
    f: Optional[str] = Field("B", description="Peer recommendation (A/B/C)")
    g: Optional[str] = Field("B", description="Price drop risk (A/B/C)")
    h: Optional[str] = Field("B", description="Dividend potential (A/B/C)")

class RiskAssessmentAnswers(BaseModel):
    q1: str
    q2: Q2Factors
    q3: str
    q4: str
    q5: str
    q6: str
    q7: str
    q8: str
    q9: str
    q10: str
    q11: str
    q12: str
    q13: str
    q14: str
    q15: str
    q16: str

class RiskAssessmentCreate(BaseModel):
    client_code: str = Field(..., pattern=r"^[A-Z0-9\-_]{1,50}$")
    answers: RiskAssessmentAnswers
    include_ai: bool = False
    disclaimer_text: Optional[str] = None
    discussion_notes: Optional[str] = ""
    form_name: Optional[str] = "Sample"

class RiskAssessmentCalculateRequest(BaseModel):
    answers: RiskAssessmentAnswers

class QuestionScoreDetail(BaseModel):
    score: int
    max: int
    details: Optional[Dict[str, Dict[str, object]]] = None

class RiskAssessmentCalculateResponse(BaseModel):
    success: bool
    total_score: int
    question_scores: Dict[str, QuestionScoreDetail]
    risk_tier: str
    recommendation: str

class RiskAssessmentResponse(BaseModel):
    id: UUID
    client_id: UUID
    client_name: Optional[str] = None
    client_code: Optional[str] = None
    calculated_score: int
    assigned_risk_tier: str
    tier_recommendation: Optional[str] = None
    form_name: str
    assessment_timestamp: datetime

    class Config:
        from_attributes = True

class SaveAssessmentResponse(BaseModel):
    success: bool
    assessment_id: UUID
    risk_id: UUID
    total_score: int
    risk_tier: str
    client_code: str
    ia_registration_number: str
