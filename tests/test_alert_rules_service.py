import pytest
from services.alert_rules_service import (
    AlertRule,
    AlertRulesResult,
    AlertRulesService,
)


def test_service_instantiation():
    """Verify AlertRulesService instantiation."""
    service = AlertRulesService()
    assert service is not None


def test_no_monitoring_state():
    """Verify rules evaluate safely when no monitoring state is provided."""
    service = AlertRulesService()
    result = service.evaluate_rules()
    assert isinstance(result, AlertRulesResult)
    assert result.total_rules == 5
    assert result.triggered_rules == 0
    assert len(result.rules) == 5
    for rule in result.rules:
        assert rule.triggered is False


def test_monitoring_ready():
    """Verify Monitoring Ready rule triggers when monitoring_status is READY."""
    class MockMonitoringState:
        monitoring_status = "READY"

    service = AlertRulesService()
    result = service.evaluate_rules(monitoring_state=MockMonitoringState())

    ready_rule = [r for r in result.rules if r.rule_name == "Monitoring Ready"][0]
    assert ready_rule.triggered is True
    assert ready_rule.severity == "INFO"
    assert ready_rule.alert_type == "MONITORING_STATUS"

    unavailable_rule = [r for r in result.rules if r.rule_name == "Monitoring Unavailable"][0]
    assert unavailable_rule.triggered is False


def test_monitoring_unavailable():
    """Verify Monitoring Unavailable rule triggers when monitoring_status is UNAVAILABLE."""
    class MockMonitoringState:
        monitoring_status = "UNAVAILABLE"

    service = AlertRulesService()
    result = service.evaluate_rules(monitoring_state=MockMonitoringState())

    unavailable_rule = [r for r in result.rules if r.rule_name == "Monitoring Unavailable"][0]
    assert unavailable_rule.triggered is True
    assert unavailable_rule.severity == "HIGH"
    assert unavailable_rule.alert_type == "MONITORING_STATUS"

    ready_rule = [r for r in result.rules if r.rule_name == "Monitoring Ready"][0]
    assert ready_rule.triggered is False


def test_changes_detected():
    """Verify Portfolio Changes Detected rule triggers when has_changes is True."""
    class MockChangeReport:
        has_changes = True
        total_changes = 3
        changes = []

    service = AlertRulesService()
    result = service.evaluate_rules(change_report=MockChangeReport())

    changes_rule = [r for r in result.rules if r.rule_name == "Portfolio Changes Detected"][0]
    assert changes_rule.triggered is True
    assert changes_rule.severity == "MEDIUM"
    assert changes_rule.alert_type == "CHANGE_DETECTED"


def test_timeline_updated():
    """Verify Timeline Updated rule triggers when total_entries > 1."""
    class MockTimeline:
        total_entries = 5
        entries = []

    service = AlertRulesService()
    result = service.evaluate_rules(timeline=MockTimeline())

    timeline_rule = [r for r in result.rules if r.rule_name == "Timeline Updated"][0]
    assert timeline_rule.triggered is True
    assert timeline_rule.severity == "LOW"
    assert timeline_rule.alert_type == "TIMELINE_UPDATED"


def test_timeline_not_triggered_with_single_entry():
    """Verify Timeline Updated does NOT trigger when total_entries <= 1."""
    class MockTimeline:
        total_entries = 1
        entries = []

    service = AlertRulesService()
    result = service.evaluate_rules(timeline=MockTimeline())

    timeline_rule = [r for r in result.rules if r.rule_name == "Timeline Updated"][0]
    assert timeline_rule.triggered is False


def test_health_score_changed():
    """Verify Health Score Changed rule triggers when change report contains Health Score."""
    class MockChange:
        field_name = "Health Score"
        previous_value = "80"
        current_value = "85"
        change_type = "INCREASED"

    class MockChangeReport:
        has_changes = True
        total_changes = 1
        changes = [MockChange()]

    service = AlertRulesService()
    result = service.evaluate_rules(change_report=MockChangeReport())

    score_rule = [r for r in result.rules if r.rule_name == "Health Score Changed"][0]
    assert score_rule.triggered is True
    assert score_rule.severity == "MEDIUM"
    assert score_rule.alert_type == "HEALTH_SCORE_CHANGED"


def test_multiple_rules_triggered():
    """Verify multiple rules can trigger simultaneously."""
    class MockMonitoringState:
        monitoring_status = "READY"

    class MockChange:
        field_name = "Health Score"
        previous_value = "70"
        current_value = "80"
        change_type = "INCREASED"

    class MockChangeReport:
        has_changes = True
        total_changes = 2
        changes = [MockChange()]

    class MockTimeline:
        total_entries = 5
        entries = []

    service = AlertRulesService()
    result = service.evaluate_rules(
        monitoring_state=MockMonitoringState(),
        change_report=MockChangeReport(),
        timeline=MockTimeline(),
    )

    assert result.total_rules == 5
    assert result.triggered_rules == 4  # Ready, Changes, Timeline, Health Score
    triggered_names = [r.rule_name for r in result.rules if r.triggered]
    assert "Monitoring Ready" in triggered_names
    assert "Portfolio Changes Detected" in triggered_names
    assert "Timeline Updated" in triggered_names
    assert "Health Score Changed" in triggered_names
    assert "Monitoring Unavailable" not in triggered_names


def test_no_rules_triggered():
    """Verify no rules trigger with empty/non-triggering data."""
    class MockMonitoringState:
        monitoring_status = "WAITING"

    class MockChangeReport:
        has_changes = False
        total_changes = 0
        changes = []

    class MockTimeline:
        total_entries = 0
        entries = []

    service = AlertRulesService()
    result = service.evaluate_rules(
        monitoring_state=MockMonitoringState(),
        change_report=MockChangeReport(),
        timeline=MockTimeline(),
    )

    assert result.total_rules == 5
    assert result.triggered_rules == 0
    for rule in result.rules:
        assert rule.triggered is False


def test_defensive_exception_handling():
    """Verify service handles exceptions gracefully and returns empty result."""
    class BrokenMonitoringState:
        @property
        def monitoring_status(self):
            raise RuntimeError("Broken")

    class BrokenChangeReport:
        @property
        def has_changes(self):
            raise RuntimeError("Broken")
        @property
        def changes(self):
            raise RuntimeError("Broken")

    class BrokenTimeline:
        @property
        def total_entries(self):
            raise RuntimeError("Broken")

    service = AlertRulesService()

    # Each individual rule handles its own exceptions
    result = service.evaluate_rules(
        monitoring_state=BrokenMonitoringState(),
        change_report=BrokenChangeReport(),
        timeline=BrokenTimeline(),
    )

    assert isinstance(result, AlertRulesResult)
    # Even with broken inputs, the service returns a valid result
    # Individual rules catch their own exceptions and return triggered=False
    assert result.total_rules == 5
    for rule in result.rules:
        assert rule.triggered is False


def test_alert_rule_dataclass():
    """Verify AlertRule dataclass structure."""
    rule = AlertRule(
        rule_name="Test Rule",
        enabled=True,
        severity="HIGH",
        alert_type="TEST_TYPE",
        triggered=True,
        description="Test description",
    )
    assert rule.rule_name == "Test Rule"
    assert rule.enabled is True
    assert rule.severity == "HIGH"
    assert rule.alert_type == "TEST_TYPE"
    assert rule.triggered is True
    assert rule.description == "Test description"


def test_alert_rules_result_dataclass():
    """Verify AlertRulesResult dataclass structure."""
    rules = [
        AlertRule("R1", True, "INFO", "T1", True, "Desc 1"),
        AlertRule("R2", True, "HIGH", "T2", False, "Desc 2"),
    ]
    result = AlertRulesResult(total_rules=2, triggered_rules=1, rules=rules)
    assert result.total_rules == 2
    assert result.triggered_rules == 1
    assert len(result.rules) == 2


def test_all_rules_have_valid_severity():
    """Verify all rules use valid severity values."""
    valid_severities = {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}
    service = AlertRulesService()
    result = service.evaluate_rules()
    for rule in result.rules:
        assert rule.severity in valid_severities, f"Invalid severity: {rule.severity}"


def test_all_rules_enabled_by_default():
    """Verify all rules are enabled by default."""
    service = AlertRulesService()
    result = service.evaluate_rules()
    for rule in result.rules:
        assert rule.enabled is True
