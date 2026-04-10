"""Pydantic request/response models for Project Syren."""

from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=32000, description="The user prompt.")
    session_id: Optional[str] = Field(None, description="Optional session identifier.")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata.")


class RiskAssessment(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Normalised risk score 0.0-1.0.")
    threat_type: Optional[str] = Field(None, description="Primary threat category.")
    matched_patterns: List[str] = Field(default_factory=list, description="Fired pattern names.")
    recommendation: str = Field("route_production", description="route_production or route_canary.")


class ChatResponse(BaseModel):
    response: str = Field(..., description="LLM-generated text.")
    risk_score: float = Field(..., description="Risk score from The Sentry.")
    route_taken: str = Field(..., description="production or canary.")
    latency_ms: float = Field(..., description="Processing latency in ms.")
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    canary_tokens_found: Optional[List[str]] = Field(None)


class HealthResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, str]


class MetricsResponse(BaseModel):
    total_requests: int
    production_count: int
    canary_count: int
    avg_risk_score: float
    top_threat_types: List[str]