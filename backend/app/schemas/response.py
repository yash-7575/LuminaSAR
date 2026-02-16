"""Pydantic response models for the LuminaSAR API."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    status: str
    version: str
    ollama_connected: bool
    database_connected: bool


class GenerateResponse(BaseModel):
    narrative_id: str
    case_id: str
    narrative_text: str
    risk_score: float
    typologies: List[str]
    generation_time_seconds: int
    audit_steps: int


class SARResponse(BaseModel):
    narrative_id: str
    case_id: str
    narrative_text: str
    risk_score: Optional[float] = None
    typologies: List[str] = []
    generated_at: Optional[str] = None
    generation_time_seconds: Optional[int] = None
    customer_name: Optional[str] = None
    customer_account: Optional[str] = None
    status: Optional[str] = None


class AuditStepResponse(BaseModel):
    audit_id: str
    step_name: str
    data_sources: Dict[str, Any] = {}
    reasoning: Dict[str, Any] = {}
    confidence_scores: Dict[str, Any] = {}
    logged_at: Optional[str] = None
    previous_hash: Optional[str] = None
    current_hash: Optional[str] = None


class AuditTrailResponse(BaseModel):
    narrative_id: str
    chain_valid: bool
    steps: List[AuditStepResponse]
    sentence_attribution: Dict[str, Any] = {}


class CaseResponse(BaseModel):
    case_id: str
    customer_name: str
    customer_account: str
    status: str
    risk_score: Optional[float] = None
    typologies: List[str] = []
    created_at: Optional[str] = None
    has_narrative: bool = False


class StatsResponse(BaseModel):
    total_sars: int
    pending_cases: int
    avg_generation_time: float
    total_customers: int
    high_risk_cases: int
    cost_savings_lakhs: float


class ConfigResponse(BaseModel):
    jurisdiction: str
    deployment_env: str
    supported_jurisdictions: List[str]
