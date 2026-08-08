"""Integration test suite for Stage 18 Alpha 12 Stability Engine in PortfolioHealthService (Sprint 13.9.4)."""

import pytest

from services.alpha12_stability_service import (
    Alpha12StabilityResult,
    Alpha12StabilityService,
    _empty_result,
)
from services.portfolio_health_service import (
    PortfolioHealthResult,
    PortfolioHealthService,
)


def test_portfolio_health_service_initialization_with_stability_service():
    """Verify PortfolioHealthService initializes with stability service dependency."""
    stab_svc = Alpha12StabilityService()
    ph_svc = PortfolioHealthService(alpha12_stability_service=stab_svc)
    assert ph_svc._alpha12_stability_service == stab_svc


def test_portfolio_health_result_contains_alpha12_stability():
    """Verify PortfolioHealthResult dataclass exposes alpha12_stability field."""
    res = PortfolioHealthResult(
        score=85,
        grade="B",
        diversification_rating="GOOD",
        concentration_rating="LOW",
        position_count=10,
        largest_position_weight_pct=8.5,
        cash_allocation_pct=5.0,
    )
    assert hasattr(res, "alpha12_stability")
    assert res.alpha12_stability is None


def test_evaluate_populates_stage18_alpha12_stability():
    """Verify PortfolioHealthService.evaluate() executes Stage 18 stability analysis."""
    ph_svc = PortfolioHealthService()
    res = ph_svc.evaluate()

    assert isinstance(res, PortfolioHealthResult)
    assert hasattr(res, "alpha12_stability")
    assert res.alpha12_stability is not None
    assert isinstance(res.alpha12_stability, Alpha12StabilityResult)


def test_injected_stability_service_integration():
    """Verify custom injected stability service is executed during evaluate()."""

    class CustomStabilityService:
        def get_stability(self, **kwargs):
            return _empty_result(
                status="ANALYZED",
                rationale="Custom injected stability test",
            )

    ph_svc = PortfolioHealthService(alpha12_stability_service=CustomStabilityService())
    res = ph_svc.evaluate()

    assert res.alpha12_stability is not None
    assert res.alpha12_stability.analysis_status == "ANALYZED"
    assert res.alpha12_stability.rationale == "Custom injected stability test"


def test_defensive_exception_handling_in_stage18():
    """Verify Stage 18 failure is non-blocking and never crashes evaluate()."""

    class FaultyStabilityService:
        def get_stability(self, **kwargs):
            raise RuntimeError("Stability evaluation crash")

    ph_svc = PortfolioHealthService(alpha12_stability_service=FaultyStabilityService())
    res = ph_svc.evaluate()

    assert isinstance(res, PortfolioHealthResult)
    assert res.alpha12_stability is None
    assert res.score >= 0  # Rest of pipeline evaluated successfully


def test_pipeline_execution_order():
    """Verify Stage 18 executes after Stage 17 replacement governance in pipeline sequence."""

    class OrderTrackerService:
        def __init__(self):
            self.execution_order = []

        def get_mapping(self, **kwargs):
            self.execution_order.append("mapping")
            return None

        def evaluate_replacements(self, **kwargs):
            self.execution_order.append("governance")
            return None

        def get_stability(self, **kwargs):
            self.execution_order.append("stability")
            return None

    tracker = OrderTrackerService()
    ph_svc = PortfolioHealthService(
        alpha12_mapping_service=tracker,
        alpha12_replacement_governance_service=tracker,
        alpha12_stability_service=tracker,
    )
    res = ph_svc.evaluate()

    assert "mapping" in tracker.execution_order
    assert "governance" in tracker.execution_order
    assert "stability" in tracker.execution_order

    map_idx = tracker.execution_order.index("mapping")
    gov_idx = tracker.execution_order.index("governance")
    stab_idx = tracker.execution_order.index("stability")

    assert map_idx < gov_idx < stab_idx
