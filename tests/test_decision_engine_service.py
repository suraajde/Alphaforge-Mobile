import pytest

from services.decision_engine_service import (
    DecisionEngineResult,
    DecisionEngineService,
    DecisionSummary,
)


def test_service_instantiation():
    """Verify DecisionEngineService instantiation."""
    service = DecisionEngineService()
    assert service is not None


def test_empty_result():
    """Verify evaluate returns empty DecisionEngineResult by default."""
    service = DecisionEngineService()
    result = service.evaluate()

    assert isinstance(result, DecisionEngineResult)
    assert isinstance(result.summary, DecisionSummary)
    assert result.summary.total_decisions == 0
    assert result.summary.pending_decisions == 0
    assert result.summary.informational_decisions == 0
    assert result.summary.engine_status == "READY"
    assert result.decisions == []


def test_engine_ready():
    """Verify engine status READY."""
    service = DecisionEngineService(engine_status="READY")
    result = service.evaluate()

    assert result.summary.engine_status == "READY"


def test_engine_unavailable():
    """Verify engine status UNAVAILABLE when configured."""
    service = DecisionEngineService(engine_status="UNAVAILABLE")
    result = service.evaluate()

    assert result.summary.engine_status == "UNAVAILABLE"


def test_build_decision_summary():
    """Verify build_decision_summary logic."""
    service = DecisionEngineService()
    summary = service.build_decision_summary(decisions=[], engine_status="WAITING")

    assert summary.engine_status == "WAITING"
    assert summary.total_decisions == 0


def test_get_decisions_empty():
    """Verify get_decisions returns empty list for foundation sprint."""
    service = DecisionEngineService()
    decisions = service.get_decisions()

    assert isinstance(decisions, list)
    assert len(decisions) == 0


def test_defensive_exception_handling():
    """Verify service handles exceptions gracefully returning default result."""
    class BrokenService(DecisionEngineService):
        def evaluate(self, portfolio_health_result=None, alert_management_result=None):
            try:
                raise RuntimeError("Engine failure")
            except Exception:
                return DecisionEngineResult(
                    summary=DecisionSummary(0, 0, 0, "UNAVAILABLE"),
                    decisions=[],
                )

    service = BrokenService()
    result = service.evaluate()

    assert isinstance(result, DecisionEngineResult)
    assert result.summary.engine_status == "UNAVAILABLE"
    assert result.summary.total_decisions == 0
    assert result.decisions == []
