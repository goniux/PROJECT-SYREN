"""Tests for app.core.router — RequestRouter"""

import pytest
from app.core.router import RequestRouter
from app.models.schemas import RiskAssessment


@pytest.fixture
def router():
    return RequestRouter()


def _make_assessment(score: float, threat_type: str | None = None) -> RiskAssessment:
    return RiskAssessment(
        score=score,
        threat_type=threat_type,
        matched_patterns=[],
        recommendation="route_production" if score < 0.4 else "route_canary",
    )


class TestSafeRouting:
    """Safe prompts (score < 0.4) should always route to production."""

    def test_low_score_routes_production(self, router):
        assessment = _make_assessment(0.0)
        assert router.route_request(assessment) == "production"

    def test_just_below_threshold_routes_production(self, router):
        assessment = _make_assessment(0.3999)
        assert router.route_request(assessment) == "production"


class TestCanaryRouting:
    """Suspicious / hostile prompts (score >= 0.4) should route to canary."""

    def test_at_threshold_routes_canary(self, router):
        assessment = _make_assessment(0.4)
        assert router.route_request(assessment) == "canary"

    def test_high_score_routes_canary(self, router):
        assessment = _make_assessment(0.85)
        assert router.route_request(assessment) == "canary"

    def test_max_score_routes_canary(self, router):
        assessment = _make_assessment(1.0)
        assert router.route_request(assessment) == "canary"


class TestStatsAccumulation:
    """Router should accurately track request statistics."""

    def test_total_requests_count(self, router):
        for s in [0.1, 0.2, 0.5, 0.8]:
            router.route_request(_make_assessment(s))
        assert router.get_stats()["total_requests"] == 4

    def test_production_and_canary_counts(self, router):
        for s in [0.1, 0.2, 0.3]:
            router.route_request(_make_assessment(s))
        for s in [0.5, 0.8]:
            router.route_request(_make_assessment(s))
        stats = router.get_stats()
        assert stats["production_count"] == 3
        assert stats["canary_count"] == 2


class TestThreatCounts:
    """Router should track threat types for canary-routed requests."""

    def test_threat_type_tracked(self, router):
        router.route_request(_make_assessment(0.7, "jailbreak"))
        router.route_request(_make_assessment(0.8, "jailbreak"))
        router.route_request(_make_assessment(0.9, "prompt_injection"))
        counts = router.get_threat_counts()
        assert counts["jailbreak"] == 2
        assert counts["prompt_injection"] == 1

    def test_safe_requests_no_threat_count(self, router):
        router.route_request(_make_assessment(0.1))
        assert router.get_threat_counts() == {}


class TestReset:
    """Reset should clear all accumulated stats."""

    def test_reset_clears_stats(self, router):
        router.route_request(_make_assessment(0.8))
        router.route_request(_make_assessment(0.9))
        router.reset_stats()
        assert router.get_stats() == {
            "total_requests": 0,
            "production_count": 0,
            "canary_count": 0,
        }
        assert router.get_threat_counts() == {}
