"""Structured JSON audit logger."""

from __future__ import annotations
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional
from app.config import get_settings


class AuditLogger:
    def __init__(self, log_file: Optional[str] = None, source_ip: str = "0.0.0.0") -> None:
        self._settings = get_settings()
        self._log_file = Path(log_file or self._settings.AUDIT_LOG_FILE)
        self._source_ip = source_ip
        self._logger = logging.getLogger("syren.audit")
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        self._log_file.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]

    def _write(self, event: Dict[str, Any]) -> None:
        line = json.dumps(event, default=str, ensure_ascii=False)
        try:
            with self._log_file.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            pass
        self._logger.info("AUDIT %s", line)

    def log_request(self, request_id: str, prompt: str, risk_score: float, route: str,
                    response_time_ms: float, threat_type: Optional[str] = None,
                    matched_patterns: Optional[list[str]] = None, source_ip: Optional[str] = None) -> None:
        event = {
            "event_type": "request_classified", "timestamp": time.time(),
            "request_id": request_id, "source_ip": source_ip or self._source_ip,
            "prompt_hash": self._hash_prompt(prompt), "risk_score": risk_score,
            "threat_type": threat_type, "matched_patterns": matched_patterns or [],
            "route": route, "response_time_ms": round(response_time_ms, 2),
        }
        self._write(event)

    def log_canary_trigger(self, request_id: str, canary_tokens: list[str],
                           prompt_hash: str, source_ip: Optional[str] = None) -> None:
        event = {
            "event_type": "canary_triggered", "timestamp": time.time(),
            "severity": "HIGH", "request_id": request_id,
            "source_ip": source_ip or self._source_ip, "prompt_hash": prompt_hash,
            "canary_tokens": canary_tokens,
            "alert": "CANARY_TOKEN_CONSUMED — Investigate immediately.",
        }
        self._write(event)

    def log_rate_limit(self, source_ip: str, path: str) -> None:
        event = {
            "event_type": "rate_limit_exceeded", "timestamp": time.time(),
            "severity": "MEDIUM", "source_ip": source_ip, "path": path,
        }
        self._write(event)
        