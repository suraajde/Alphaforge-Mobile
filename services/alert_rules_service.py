"""Alert Rules Engine Service (Sprint 15.0.2)

Centralized rule evaluation layer that determines whether Portfolio Health
conditions should trigger standardized alerts.

This service is RULE EVALUATION ONLY.
It does NOT generate notifications, make investment decisions,
or recommend portfolio actions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AlertRule:
    """Represents a single evaluated alert rule."""
    rule_name: str
    enabled: bool
    severity: str
    alert_type: str
    triggered: bool
    description: str


@dataclass
class AlertRulesResult:
    """Aggregated result of all evaluated alert rules."""
    total_rules: int
    triggered_rules: int
    rules: list[AlertRule]


class AlertRulesService:
    """Service layer for evaluating predefined objective alert rules.

    Evaluates rules against monitoring state, change report, timeline,
    and monitoring dashboard. Each rule evaluates to TRUE or FALSE.

    This service does NOT:
    - Generate notifications
    - Make investment decisions
    - Recommend portfolio actions
    """

    def __init__(self) -> None:
        pass

    def evaluate_rules(
        self,
        monitoring_state: Optional[Any] = None,
        change_report: Optional[Any] = None,
        timeline: Optional[Any] = None,
        monitoring_dashboard: Optional[Any] = None,
    ) -> AlertRulesResult:
        """Evaluate all predefined alert rules against provided monitoring data.

        Args:
            monitoring_state: Current monitoring state from PortfolioHealthMonitorService.
            change_report: Change report from PortfolioHealthChangeDetectionService.
            timeline: Timeline from PortfolioHealthTimelineService.
            monitoring_dashboard: Dashboard from PortfolioHealthMonitoringDashboardService.

        Returns:
            AlertRulesResult with all evaluated rules.
        """
        default_result = AlertRulesResult(total_rules=0, triggered_rules=0, rules=[])

        try:
            rules: list[AlertRule] = []

            # Rule 1: Monitoring Ready
            rules.append(self._evaluate_monitoring_ready(monitoring_state))

            # Rule 2: Monitoring Unavailable
            rules.append(self._evaluate_monitoring_unavailable(monitoring_state))

            # Rule 3: Portfolio Changes Detected
            rules.append(self._evaluate_changes_detected(change_report))

            # Rule 4: Timeline Updated
            rules.append(self._evaluate_timeline_updated(timeline))

            # Rule 5: Health Score Changed
            rules.append(self._evaluate_health_score_changed(change_report))

            triggered_count = sum(1 for r in rules if r.triggered)

            return AlertRulesResult(
                total_rules=len(rules),
                triggered_rules=triggered_count,
                rules=rules,
            )
        except Exception:
            return default_result

    def _evaluate_monitoring_ready(self, monitoring_state: Optional[Any]) -> AlertRule:
        """Rule 1: Monitoring Ready – monitoring_status == 'READY'."""
        try:
            triggered = False
            if monitoring_state is not None:
                status = getattr(monitoring_state, "monitoring_status", "")
                triggered = status == "READY"
            return AlertRule(
                rule_name="Monitoring Ready",
                enabled=True,
                severity="INFO",
                alert_type="MONITORING_STATUS",
                triggered=triggered,
                description="Portfolio health monitoring is active and ready.",
            )
        except Exception:
            return AlertRule(
                rule_name="Monitoring Ready",
                enabled=True,
                severity="INFO",
                alert_type="MONITORING_STATUS",
                triggered=False,
                description="Portfolio health monitoring is active and ready.",
            )

    def _evaluate_monitoring_unavailable(self, monitoring_state: Optional[Any]) -> AlertRule:
        """Rule 2: Monitoring Unavailable – monitoring_status == 'UNAVAILABLE'."""
        try:
            triggered = False
            if monitoring_state is not None:
                status = getattr(monitoring_state, "monitoring_status", "")
                triggered = status == "UNAVAILABLE"
            return AlertRule(
                rule_name="Monitoring Unavailable",
                enabled=True,
                severity="HIGH",
                alert_type="MONITORING_STATUS",
                triggered=triggered,
                description="Portfolio health monitoring is currently unavailable.",
            )
        except Exception:
            return AlertRule(
                rule_name="Monitoring Unavailable",
                enabled=True,
                severity="HIGH",
                alert_type="MONITORING_STATUS",
                triggered=False,
                description="Portfolio health monitoring is currently unavailable.",
            )

    def _evaluate_changes_detected(self, change_report: Optional[Any]) -> AlertRule:
        """Rule 3: Portfolio Changes Detected – change_report.has_changes == True."""
        try:
            triggered = False
            if change_report is not None:
                triggered = bool(getattr(change_report, "has_changes", False))
            return AlertRule(
                rule_name="Portfolio Changes Detected",
                enabled=True,
                severity="MEDIUM",
                alert_type="CHANGE_DETECTED",
                triggered=triggered,
                description="Portfolio health changes have been detected.",
            )
        except Exception:
            return AlertRule(
                rule_name="Portfolio Changes Detected",
                enabled=True,
                severity="MEDIUM",
                alert_type="CHANGE_DETECTED",
                triggered=False,
                description="Portfolio health changes have been detected.",
            )

    def _evaluate_timeline_updated(self, timeline: Optional[Any]) -> AlertRule:
        """Rule 4: Timeline Updated – timeline.total_entries > 1."""
        try:
            triggered = False
            if timeline is not None:
                total_entries = int(getattr(timeline, "total_entries", 0))
                triggered = total_entries > 1
            return AlertRule(
                rule_name="Timeline Updated",
                enabled=True,
                severity="LOW",
                alert_type="TIMELINE_UPDATED",
                triggered=triggered,
                description="Portfolio health timeline has been updated with new entries.",
            )
        except Exception:
            return AlertRule(
                rule_name="Timeline Updated",
                enabled=True,
                severity="LOW",
                alert_type="TIMELINE_UPDATED",
                triggered=False,
                description="Portfolio health timeline has been updated with new entries.",
            )

    def _evaluate_health_score_changed(self, change_report: Optional[Any]) -> AlertRule:
        """Rule 5: Health Score Changed – Change Report contains 'Health Score'."""
        try:
            triggered = False
            if change_report is not None:
                changes = getattr(change_report, "changes", []) or []
                for chg in changes:
                    if getattr(chg, "field_name", "") == "Health Score":
                        triggered = True
                        break
            return AlertRule(
                rule_name="Health Score Changed",
                enabled=True,
                severity="MEDIUM",
                alert_type="HEALTH_SCORE_CHANGED",
                triggered=triggered,
                description="Portfolio health score has changed between evaluations.",
            )
        except Exception:
            return AlertRule(
                rule_name="Health Score Changed",
                enabled=True,
                severity="MEDIUM",
                alert_type="HEALTH_SCORE_CHANGED",
                triggered=False,
                description="Portfolio health score has changed between evaluations.",
            )
