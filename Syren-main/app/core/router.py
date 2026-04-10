"""Request router — routes classified requests to Production or Canary LLM."""

from __future__ import annotations
from threading import Lock
from typing import Dict
from app.config import get_settings
from app.models.schemas import RiskAssessment


class RequestRouter:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._lock = Lock()
        self._stats: Dict[str, int] = {
            "total_requests": 0, "production_count": 0, "canary_count": 0,
        }
        self._threat_counts: Dict[str, int] = {}

    def route_request(self, assessment: RiskAssessment) -> str:
        with self._lock:
            self._stats["total_requests"] += 1
            if assessment.score < self._settings.RISK_THRESHOLD_LOW:
                self._stats["production_count"] += 1
                route = "production"
            else:
                self._stats["canary_count"] += 1
                route = "canary"
            if assessment.threat_type:
                self._threat_counts[assessment.threat_type] = (
                    self._threat_counts.get(assessment.threat_type, 0) + 1
                )
        return route

    def get_stats(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._stats)

    def get_threat_counts(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._threat_counts)

    def reset_stats(self) -> None:
        with self._lock:
            self._stats = {"total_requests": 0, "production_count": 0, "canary_count": 0}
            self._threat_counts = {}