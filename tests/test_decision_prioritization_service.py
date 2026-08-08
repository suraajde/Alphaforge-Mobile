import pytest

from services.decision_classification_service import DecisionClassification
from services.decision_prioritization_service import (
    DecisionPriority,
    DecisionPrioritizationResult,
    DecisionPrioritizationService,
)


def test_service_instantiation():
    """Verify DecisionPrioritizationService instantiation."""
    service = DecisionPrioritizationService()
    assert service is not None


def test_empty_prioritization_result():
    """Verify prioritize returns empty DecisionPrioritizationResult by default."""
    service = DecisionPrioritizationService()
    result = service.prioritize()

    assert isinstance(result, DecisionPrioritizationResult)
    assert result.total_prioritized == 0
    assert result.critical_count == 0
    assert result.high_count == 0
    assert result.medium_count == 0
    assert result.low_count == 0
    assert result.info_count == 0
    assert result.priorities == []


def test_health_category_high_priority():
    """Verify HEALTH category with CLASSIFIED status maps to HIGH priority."""
    service = DecisionPrioritizationService()
    cls = DecisionClassification("d1", "HEALTH", "Health warning", "CLASSIFIED")
    res = service.prioritize([cls])

    assert res.total_prioritized == 1
    assert res.high_count == 1
    assert res.priorities[0].priority == "HIGH"
    assert res.priorities[0].decision_id == "d1"
    assert res.priorities[0].category == "HEALTH"


def test_monitoring_category_medium_priority():
    """Verify MONITORING category with CLASSIFIED status maps to MEDIUM priority."""
    service = DecisionPrioritizationService()
    cls = DecisionClassification("d2", "MONITORING", "Monitor item", "CLASSIFIED")
    res = service.prioritize([cls])

    assert res.total_prioritized == 1
    assert res.medium_count == 1
    assert res.priorities[0].priority == "MEDIUM"


def test_alert_category_high_priority():
    """Verify ALERT category with CLASSIFIED status maps to HIGH priority."""
    service = DecisionPrioritizationService()
    cls = DecisionClassification("d3", "ALERT", "Alert triggered", "CLASSIFIED")
    res = service.prioritize([cls])

    assert res.total_prioritized == 1
    assert res.high_count == 1
    assert res.priorities[0].priority == "HIGH"


def test_portfolio_category_medium_priority():
    """Verify PORTFOLIO category with CLASSIFIED status maps to MEDIUM priority."""
    service = DecisionPrioritizationService()
    cls = DecisionClassification("d4", "PORTFOLIO", "Portfolio change", "CLASSIFIED")
    res = service.prioritize([cls])

    assert res.total_prioritized == 1
    assert res.medium_count == 1
    assert res.priorities[0].priority == "MEDIUM"


def test_general_category_info_priority():
    """Verify GENERAL category with CLASSIFIED status maps to INFO priority."""
    service = DecisionPrioritizationService()
    cls = DecisionClassification("d5", "GENERAL", "General note", "CLASSIFIED")
    res = service.prioritize([cls])

    assert res.total_prioritized == 1
    assert res.info_count == 1
    assert res.priorities[0].priority == "INFO"


def test_unclassified_status_low_priority():
    """Verify UNCLASSIFIED classification status maps to LOW priority."""
    service = DecisionPrioritizationService()
    cls = DecisionClassification("d6", "HEALTH", "Unclassified item", "UNCLASSIFIED")
    res = service.prioritize([cls])

    assert res.total_prioritized == 1
    assert res.low_count == 1
    assert res.priorities[0].priority == "LOW"


def test_multiple_classifications():
    """Verify prioritize handles multiple classifications correctly."""
    service = DecisionPrioritizationService()
    c1 = DecisionClassification("1", "HEALTH", "H1", "CLASSIFIED")
    c2 = DecisionClassification("2", "MONITORING", "M1", "CLASSIFIED")
    c3 = DecisionClassification("3", "ALERT", "A1", "CLASSIFIED")
    c4 = DecisionClassification("4", "PORTFOLIO", "P1", "CLASSIFIED")
    c5 = DecisionClassification("5", "GENERAL", "G1", "CLASSIFIED")
    c6 = DecisionClassification("6", "UNCLASSIFIED", "U1", "UNCLASSIFIED")

    res = service.prioritize([c1, c2, c3, c4, c5, c6])

    assert res.total_prioritized == 6
    assert res.high_count == 2    # HEALTH + ALERT
    assert res.medium_count == 2  # MONITORING + PORTFOLIO
    assert res.info_count == 1    # GENERAL
    assert res.low_count == 1     # UNCLASSIFIED
    assert res.critical_count == 0


def test_priority_counts():
    """Verify priority summary counts building."""
    service = DecisionPrioritizationService()
    p1 = DecisionPriority("1", "HEALTH", "HIGH", "Desc 1")
    p2 = DecisionPriority("2", "ALERT", "HIGH", "Desc 2")
    p3 = DecisionPriority("3", "MONITORING", "MEDIUM", "Desc 3")
    p4 = DecisionPriority("4", "GENERAL", "INFO", "Desc 4")
    p5 = DecisionPriority("5", "UNCLASSIFIED", "LOW", "Desc 5")
    p6 = DecisionPriority("6", "CRITICAL_ITEM", "CRITICAL", "Desc 6")

    res = service.build_summary([p1, p2, p3, p4, p5, p6])
    assert res.total_prioritized == 6
    assert res.critical_count == 1
    assert res.high_count == 2
    assert res.medium_count == 1
    assert res.low_count == 1
    assert res.info_count == 1


def test_missing_fields_safety():
    """Verify service handles classification objects with missing fields safely."""
    service = DecisionPrioritizationService()

    class PartialClassification:
        decision_id = "p1"

    res = service.prioritize([PartialClassification()])
    assert res.total_prioritized == 1
    assert res.low_count == 1
    assert res.priorities[0].decision_id == "p1"
    assert res.priorities[0].priority == "LOW"


def test_none_input_safety():
    """Verify service handles None input safely."""
    service = DecisionPrioritizationService()
    res1 = service.prioritize(None)
    assert res1.total_prioritized == 0

    res2 = service.prioritize([None])
    assert res2.total_prioritized == 0


def test_defensive_exception_handling():
    """Verify service handles internal errors defensively without throwing exceptions."""
    class FaultyService(DecisionPrioritizationService):
        def build_summary(self, priorities=None):
            raise RuntimeError("Internal crash")

    service = FaultyService()
    c = DecisionClassification("1", "HEALTH", "H1", "CLASSIFIED")
    res = service.prioritize([c])

    assert isinstance(res, DecisionPrioritizationResult)
    assert res.total_prioritized == 0
    assert res.priorities == []
