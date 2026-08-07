import pytest

from services.decision_classification_service import (
    DecisionClassification,
    DecisionClassificationResult,
    DecisionClassificationService,
)


def test_service_instantiation():
    """Verify DecisionClassificationService instantiation."""
    service = DecisionClassificationService()
    assert service is not None


def test_empty_classification_result():
    """Verify classify returns empty DecisionClassificationResult by default."""
    service = DecisionClassificationService()
    result = service.classify()

    assert isinstance(result, DecisionClassificationResult)
    assert result.total_classifications == 0
    assert result.classified == 0
    assert result.unclassified == 0
    assert result.classifications == []


def test_classification_summary():
    """Verify build_summary logic for decision classifications."""
    service = DecisionClassificationService()
    item1 = DecisionClassification("1", "HEALTH", "Health warning", "CLASSIFIED")
    item2 = DecisionClassification("2", "ALERT", "Alert pending", "UNCLASSIFIED")

    summary = service.build_summary([item1, item2])
    assert summary.total_classifications == 2
    assert summary.classified == 1
    assert summary.unclassified == 1
    assert len(summary.classifications) == 2


def test_get_classifications_empty():
    """Verify get_classifications returns empty list for foundation sprint."""
    service = DecisionClassificationService()
    classifications = service.get_classifications()

    assert isinstance(classifications, list)
    assert len(classifications) == 0


def test_defensive_exception_handling():
    """Verify service handles exceptions gracefully returning default result."""
    class BrokenService(DecisionClassificationService):
        def classify(self, **kwargs):
            try:
                raise RuntimeError("Classification failure")
            except Exception:
                return DecisionClassificationResult(
                    total_classifications=0,
                    classified=0,
                    unclassified=0,
                    classifications=[],
                )

    service = BrokenService()
    result = service.classify()

    assert isinstance(result, DecisionClassificationResult)
    assert result.total_classifications == 0
    assert result.classified == 0
    assert result.unclassified == 0
    assert result.classifications == []


def test_missing_dependencies_safety():
    """Verify service operates safely when dependencies are None."""
    service = DecisionClassificationService(
        decision_engine_service=None,
        portfolio_health_service=None,
        alert_management_service=None,
    )
    result = service.classify()

    assert isinstance(result, DecisionClassificationResult)
    assert result.total_classifications == 0
    assert result.classified == 0
    assert result.unclassified == 0
    assert result.classifications == []
