from dataclasses import dataclass
from typing import Any
import pytest

from services.alert_generation_service import (
    AlertGenerationResult,
    AlertGenerationService,
)


@dataclass
class MockMonitoringState:
    monitoring_status: str


@dataclass
class MockChangeItem:
    field_name: str
    previous_value: str
    current_value: str
    change_type: str


@dataclass
class MockChangeReport:
    has_changes: bool
    total_changes: int
    changes: list[MockChangeItem]


@dataclass
class MockTimelineEntry:
    trend_direction: str


@dataclass
class MockTimeline:
    total_entries: int
    entries: list[MockTimelineEntry]


def test_service_instantiation():
    """Verify AlertGenerationService instantiation."""
    service = AlertGenerationService()
    assert service is not None


def test_no_monitoring_state():
    """Verify alert generation when no parameters are provided."""
    service = AlertGenerationService()
    result = service.generate_alerts()

    assert isinstance(result, AlertGenerationResult)
    assert result.generated_alerts == 0
    assert result.alerts == []


def test_monitoring_ready():
    """Verify MONITORING_STATUS alert generation when monitoring is READY."""
    service = AlertGenerationService()
    mon_state = MockMonitoringState(monitoring_status="READY")

    result = service.generate_alerts(monitoring_state=mon_state)
    assert result.generated_alerts == 1
    assert result.alerts[0].alert_type == "MONITORING_STATUS"
    assert result.alerts[0].severity == "INFO"
    assert result.alerts[0].title == "Monitoring ready"


def test_monitoring_unavailable():
    """Verify MONITORING_STATUS alert generation when monitoring is UNAVAILABLE."""
    service = AlertGenerationService()
    mon_state = MockMonitoringState(monitoring_status="UNAVAILABLE")

    result = service.generate_alerts(monitoring_state=mon_state)
    assert result.generated_alerts == 1
    assert result.alerts[0].alert_type == "MONITORING_STATUS"
    assert result.alerts[0].severity == "HIGH"
    assert result.alerts[0].title == "Monitoring unavailable"


def test_change_detection_alert():
    """Verify CHANGE_DETECTED alert generation."""
    service = AlertGenerationService()
    report = MockChangeReport(has_changes=True, total_changes=3, changes=[])

    result = service.generate_alerts(change_report=report)
    assert result.generated_alerts == 1
    assert result.alerts[0].alert_type == "CHANGE_DETECTED"
    assert result.alerts[0].severity == "MEDIUM"
    assert "3 portfolio health changes detected" in result.alerts[0].description


def test_timeline_update_alert():
    """Verify TIMELINE_UPDATED alert generation."""
    service = AlertGenerationService()
    timeline = MockTimeline(total_entries=5, entries=[])

    result = service.generate_alerts(timeline=timeline)
    assert result.generated_alerts == 1
    assert result.alerts[0].alert_type == "TIMELINE_UPDATED"
    assert result.alerts[0].severity == "LOW"


def test_health_score_change_alert():
    """Verify HEALTH_SCORE_CHANGED alert generation from change report."""
    service = AlertGenerationService()
    item = MockChangeItem("Health Score", "80", "84", "INCREASED")
    report = MockChangeReport(has_changes=True, total_changes=1, changes=[item])

    result = service.generate_alerts(change_report=report)
    # Should produce CHANGE_DETECTED and HEALTH_SCORE_CHANGED
    types = [a.alert_type for a in result.alerts]
    assert "CHANGE_DETECTED" in types
    assert "HEALTH_SCORE_CHANGED" in types
    assert result.generated_alerts == 2


def test_multiple_alerts_generation():
    """Verify multiple alerts generation when multiple conditions trigger."""
    service = AlertGenerationService()
    mon_state = MockMonitoringState(monitoring_status="READY")
    report = MockChangeReport(has_changes=True, total_changes=2, changes=[])
    timeline = MockTimeline(total_entries=3, entries=[])

    result = service.generate_alerts(
        monitoring_state=mon_state,
        change_report=report,
        timeline=timeline,
    )
    assert result.generated_alerts == 3
    types = [a.alert_type for a in result.alerts]
    assert "MONITORING_STATUS" in types
    assert "CHANGE_DETECTED" in types
    assert "TIMELINE_UPDATED" in types


def test_duplicate_prevention():
    """Verify duplicate prevention logic ensures distinct alert types."""
    service = AlertGenerationService()
    mon_state = MockMonitoringState(monitoring_status="READY")

    result = service.generate_alerts(
        monitoring_state=mon_state,
    )
    types = [a.alert_type for a in result.alerts]
    assert len(types) == len(set(types))


def test_defensive_exception_handling():
    """Verify defensive handling when inputs raise unexpected attributes or errors."""
    service = AlertGenerationService()
    corrupt_state = "INVALID_STATE_OBJECT"

    result = service.generate_alerts(monitoring_state=corrupt_state)
    assert isinstance(result, AlertGenerationResult)
    assert result.generated_alerts == 0
