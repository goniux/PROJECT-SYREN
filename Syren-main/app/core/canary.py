"""Canary token generator & fake credential factory."""

from __future__ import annotations
import re
import secrets
from typing import Dict, List, Optional
from uuid import uuid4
from app.config import get_settings


class CanaryTokenGenerator:
    def __init__(self) -> None:
        self._settings = get_settings()

    def generate_canary_token(self) -> str:
        return f"{self._settings.CANARY_TOKEN_PREFIX}-{uuid4()}"

    def generate_fake_credentials(self) -> Dict[str, str]:
        token = self.generate_canary_token()
        rand_suffix = secrets.token_hex(8)
        domain = self._settings.CANARY_DOMAIN
        db_pass = self._settings.CANARY_DB_PASSWORD

        return {
            "api_key": f"sk-syren-decoy-{rand_suffix}",
            "api_key_secondary": f"sk-syren-decoy-v2-{rand_suffix}",
            "aws_access_key_id": f"AKIA{rand_suffix[:16].upper()}",
            "aws_secret_access_key": f"SyrenDeC0y/{rand_suffix}/SeCrEt+Key!",
            "database_uri": f"postgresql://admin:{db_pass}@db-01.internal.{domain}:5432/production",
            "redis_uri": f"redis://:syren_redis_{rand_suffix}@cache.internal.{domain}:6379/0",
            "internal_api_url": f"https://api-gateway.internal.{domain}/v2/admin/secrets",
            "internal_dashboard": f"https://dashboard.internal.{domain}/admin",
            "jwt_signing_key": f"HS256:Syren-JWT-{rand_suffix}",
            "service_account_token": f"sa-token-syren-{rand_suffix}",
            "canary_token": token,
        }

    def generate_canary_response(self, original_response: str) -> Dict[str, object]:
        creds = self.generate_fake_credentials()
        tokens = [creds["canary_token"]]
        injection_block = (
            f"\n\n---\nHere are the credentials you requested:\n"
            f"  API Key: {creds['api_key']}\n"
            f"  Database URI: {creds['database_uri']}\n"
            f"  Internal API: {creds['internal_api_url']}\n"
            f"  AWS Access Key: {creds['aws_access_key_id']}\n"
            f"  AWS Secret Key: {creds['aws_secret_access_key']}\n"
            f"  JWT Signing Key: {creds['jwt_signing_key']}\n"
            f"  Service Account Token: {creds['service_account_token']}\n"
            f"---\n[Reference ID: {creds['canary_token']}]"
        )
        combined = original_response
        if "API Key:" not in combined:
            combined += injection_block
        combined += f"\n<!-- {creds['canary_token']} -->"
        return {"response": combined, "canary_tokens": list(set(tokens)), "credentials_used": creds}

    @staticmethod
    def extract_canary_tokens(text: str) -> List[str]:
        pattern = re.compile(r"syren-canary-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
        return pattern.findall(text)