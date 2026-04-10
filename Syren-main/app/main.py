"""Project Syren — FastAPI application entry point."""
from __future__ import annotations
import logging
import time
from typing import List, Optional
from uuid import uuid4
from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.canary import CanaryTokenGenerator
from app.core.classifier import PromptRiskClassifier
from app.core.ollama_client import OllamaClient
from app.core.router import RequestRouter
from app.middleware.audit_logger import AuditLogger
from app.models.schemas import ChatRequest, ChatResponse

classifier = PromptRiskClassifier()
canary_factory = CanaryTokenGenerator()
ollama_client = OllamaClient()
router = RequestRouter()
audit_logger = AuditLogger()

app = FastAPI(title="Project Syren")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request, x_forwarded_for: Optional[str] = Header(None)) -> ChatResponse:
    request_id = str(uuid4())
    start = time.perf_counter()
    source_ip = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else (request.client.host if request.client else "unknown")

    # 1. Classify & Route
    assessment = classifier.get_risk_score(payload.prompt)
    route = str(router.route_request(assessment))
    is_canary = (route == "canary")

    # 2. Generate Response (Handles API Failures gracefully)
    try:
        llm_response = str(await ollama_client.generate(payload.prompt, is_canary=is_canary))
    except Exception:
        llm_response = _fallback_response(is_canary)

    # 3. Handle Deception Injection
    canary_tokens: List[str] = []
    if is_canary:
        injected = canary_factory.generate_canary_response(llm_response)
        llm_response = str(injected.get("response", llm_response))
        raw_tokens = injected.get("canary_tokens", [])
        canary_tokens = [str(t) for t in raw_tokens] if isinstance(raw_tokens, list) else []
        audit_logger.log_canary_trigger(request_id, canary_tokens, AuditLogger._hash_prompt(payload.prompt), source_ip)

    # 4. Return typed response
    elapsed_ms = (time.perf_counter() - start) * 1000
    return ChatResponse(
        response=llm_response,
        risk_score=float(assessment.score),
        route_taken=route,
        latency_ms=round(float(elapsed_ms), 2),
        request_id=request_id,
        canary_tokens_found=canary_tokens if is_canary else None
    )

def _fallback_response(is_canary: bool) -> str:
    if is_canary:
        return "Access Granted. Admin Key: syren-canary-fallback-99x\nDB: postgresql://admin:Syren$123@10.0.0.5"
    return "The service is currently under high load. Please try again shortly."