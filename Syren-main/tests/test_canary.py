"""Tests for the Canary Token Generator."""

import re
import pytest
from app.core.canary import CanaryTokenGenerator


@pytest.fixture
def canary() -> CanaryTokenGenerator:
    return CanaryTokenGenerator()


def test_token_format(canary: CanaryTokenGenerator) -> None:
    token = canary.generate_canary_token()
    pattern = r"^syren-canary-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    assert re.match(pattern, token), f"Token '{token}' does not match expected format."


def test_token_uniqueness(canary: CanaryTokenGenerator) -> None:
    tokens = {canary.generate_canary_token() for _ in range(100)}
    assert len(tokens) == 100, "Generated tokens are not unique."


def test_fake_credentials_structure(canary: CanaryTokenGenerator) -> None:
    creds = canary.generate_fake_credentials()
    expected_keys = {
        "api_key", "api_key_secondary", "aws_access_key_id",
        "aws_secret_access_key", "database_uri", "redis_uri",
        "internal_api_url", "internal_dashboard", "jwt_signing_key",
        "service_account_token", "canary_token",
    }
    assert set(creds.keys()) == expected_keys


def test_api_key_format(canary: CanaryTokenGenerator) -> None:
    creds = canary.generate_fake_credentials()
    assert creds["api_key"].startswith("sk-syren-decoy-")
    assert len(creds["api_key"]) > 20


def test_database_uri_format(canary: CanaryTokenGenerator) -> None:
    creds = canary.generate_fake_credentials()
    assert creds["database_uri"].startswith("postgresql://admin:")
    assert "siren.corp" in creds["database_uri"]


def test_aws_key_format(canary: CanaryTokenGenerator) -> None:
    creds = canary.generate_fake_credentials()
    assert creds["aws_access_key_id"].startswith("AKIA")
    assert len(creds["aws_access_key_id"]) == 20  # AWS standard: AKIA + 16 hex chars


def test_internal_url_format(canary: CanaryTokenGenerator) -> None:
    creds = canary.generate_fake_credentials()
    assert creds["internal_api_url"].startswith("https://")
    assert "internal.siren.corp" in creds["internal_api_url"]


def test_credentials_change_between_calls(canary: CanaryTokenGenerator) -> None:
    c1 = canary.generate_fake_credentials()
    c2 = canary.generate_fake_credentials()
    assert c1["api_key"] != c2["api_key"]
    assert c1["canary_token"] != c2["canary_token"]


def test_canary_response_contains_credentials(canary: CanaryTokenGenerator) -> None:
    result = canary.generate_canary_response("Sure, here is the information.")
    assert "API Key:" in result["response"]
    assert "Database URI:" in result["response"]
    assert "Internal API:" in result["response"]
    assert "AWS Access Key:" in result["response"]


def test_canary_response_contains_tokens(canary: CanaryTokenGenerator) -> None:
    result = canary.generate_canary_response("Hello")
    assert result["canary_tokens"] is not None
    assert len(result["canary_tokens"]) >= 1
    for token in result["canary_tokens"]:
        assert "syren-canary-" in token


def test_canary_response_has_hidden_html_token(canary: CanaryTokenGenerator) -> None:
    result = canary.generate_canary_response("Hello")
    assert "<!-- " in result["response"]
    assert " -->" in result["response"]


def test_canary_response_includes_original(canary: CanaryTokenGenerator) -> None:
    original = "This is the LLM's original answer."
    result = canary.generate_canary_response(original)
    assert original in result["response"]


def test_extract_canary_tokens(canary: CanaryTokenGenerator) -> None:
    tokens = [canary.generate_canary_token() for _ in range(3)]
    text = f"Some text {tokens[0]} more text {tokens[1]} and {tokens[2]}"
    extracted = canary.extract_canary_tokens(text)
    assert set(extracted) == set(tokens)


def test_extract_from_text_with_no_tokens(canary: CanaryTokenGenerator) -> None:
    extracted = canary.extract_canary_tokens("No tokens here at all.")
    assert extracted == []


def test_credentials_used_in_response(canary: CanaryTokenGenerator) -> None:
    result = canary.generate_canary_response("Give me credentials")
    assert "credentials_used" in result
    creds = result["credentials_used"]
    assert "api_key" in creds
    assert creds["canary_token"] in result["canary_tokens"]
    