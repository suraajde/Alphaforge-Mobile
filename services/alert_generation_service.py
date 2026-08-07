"""Alert Generation Framework Service (Sprint 15.0.1)

Converts Portfolio Health monitoring results into PortfolioAlert objects.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Optional

from services.alert_center_service import PortfolioAlert
from services.portfolio_health_change_detection_service import (
    PortfolioHealthChangeDetectionService,
)
from services.portfolio_health_history_service import PortfolioHealthHistoryService
from services.portfolio_health_monitor_dashboard_service import (
    PortfolioHealthMonitoringDashboardService,
)
from services.portfolio_health_monitor_service import PortfolioHealthMonitorService
from services.portfolio_health_timeline_service import PortfolioHealthTimelineService


@dataclass
class AlertGenerationResult:
    generated_alerts: int
    alerts: list[PortfolioAlert]


class AlertGenerationService:
    """Service layer for evaluating monitoring conditions and generating framework alerts."""

    def __init__(
        self,
        history_service: Optional[PortfolioHealthHistoryService] = None,
        monitor_service: Optional[PortfolioHealthMonitorService] = None,
        change_detection_service: Optional[PortfolioHealthChangeDetectionService] = None,
        timeline_service: Optional[PortfolioHealthTimelineService] = None,
        dashboard_service: Optional[PortfolioHealthMonitoringDashboardService] = None,
    ) -> None:
        self.history_service = history_service
        self.monitor_service = monitor_service
        self.change_detection_service = change_detection_service
        self.timeline_service = timeline_service
        self.dashboard_service = dashboard_service

    def generate_alerts(
        self,
        monitoring_state: Optional[Any] = None,
        change_report: Optional[Any] = None,
        timeline: Optional[Any] = None,
        monitoring_dashboard: Optional[Any] = None,
    ) -> AlertGenerationResult:
        """Generates PortfolioAlert objects from monitoring state, change report, timeline, and dashboard safely."""
        default_result = AlertGenerationResult(generated_alerts=0, alerts=[])

        try:
            if monitoring_state is None and self.monitor_service is not None:
                try:
                    monitoring_state = self.monitor_service.get_monitoring_state()
                except Exception:
                    monitoring_state = None

            if change_report is None and self.change_detection_service is not None:
                try:
                    change_report = self.change_detection_service.detect_changes()
                except Exception:
                    change_report = None

            if timeline is None and self.timeline_service is not None:
                try:
                    timeline = self.timeline_service.build_timeline()
                except Exception:
                    timeline = None

            if monitoring_dashboard is None and self.dashboard_service is not None:
                try:
                    monitoring_dashboard = self.dashboard_service.build_dashboard()
                except Exception:
                    monitoring_dashboard = None

            alerts: list[PortfolioAlert] = []
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

            # 1. MONITORING_STATUS
            if monitoring_state is not None:
                status = getattr(monitoring_state, "monitoring_status", "")
                if status == "READY":
                    alerts.append(
                        PortfolioAlert(
                            alert_id="gen_mon_ready",
                            timestamp=now_str,
                            alert_type="MONITORING_STATUS",
                            severity="INFO",
                            title="Monitoring ready",
                            description="Portfolio health monitoring is active and ready.",
                            status="ACTIVE",
                        )
                    )
                elif status == "UNAVAILABLE":
                    alerts.append(
                        PortfolioAlert(
                            alert_id="gen_mon_unavailable",
                            timestamp=now_str,
                            alert_type="MONITORING_STATUS",
                            severity="HIGH",
                            title="Monitoring unavailable",
                            description="Portfolio health monitoring is currently unavailable.",
                            status="ACTIVE",
                        )
                    )

            # 2. CHANGE_DETECTED
            if change_report is not None:
                has_changes = bool(getattr(change_report, "has_changes", False))
                total_changes = int(getattr(change_report, "total_changes", 0))
                if has_changes or total_changes > 0:
                    alerts.append(
                        PortfolioAlert(
                            alert_id="gen_changes_detected",
                            timestamp=now_str,
                            alert_type="CHANGE_DETECTED",
                            severity="MEDIUM",
                            title="Portfolio changes detected",
                            description=f"{total_changes} portfolio health changes detected.",
                            status="ACTIVE",
                        )
                    )

            # 3. TIMELINE_UPDATED
            if timeline is not None:
                total_entries = int(getattr(timeline, "total_entries", 0))
                if total_entries > 0:
                    alerts.append(
                        PortfolioAlert(
                            alert_id="gen_timeline_updated",
                            timestamp=now_str,
                            alert_type="TIMELINE_UPDATED",
                            severity="LOW",
                            title="Portfolio history updated",
                            description=f"{total_entries} timeline snapshot entries available.",
                            status="ACTIVE",
                        )
                    )

            # 4. HEALTH_SCORE_CHANGED
            score_changed = False
            if change_report is not None:
                changes = getattr(change_report, "changes", []) or []
                for chg in changes:
                    if getattr(chg, "field_name", "") == "Health Score":
                        score_changed = True
                        break

            if not score_changed and timeline is not None:
                entries = getattr(timeline, "entries", []) or []
                if len(entries) >= 2:
                    last_trend = getattr(entries[-1], "trend_direction", "STABLE")
                    if last_trend in ["IMPROVING", "DETERIORATING"]:
                        score_changed = True

            if score_changed:
                alerts.append(
                    PortfolioAlert(
                        alert_id="gen_score_changed",
                        timestamp=now_str,
                        alert_type="HEALTH_SCORE_CHANGED",
                        severity="MEDIUM",
                        title="Portfolio health score changed",
                        description="Portfolio health score updated across snapshots.",
                        status="ACTIVE",
                    )
                )

            # Duplicate prevention by alert_id / alert_type
            seen_types: set[str] = set()
            unique_alerts: list[PortfolioAlert] = []
            for a in alerts:
                if a.alert_type not in seen_types:
                    seen_types.add(a.alert_type)
                    unique_alerts.append(a)

            return AlertGenerationResult(
                generated_alerts=len(unique_alerts),
                alerts=unique_alerts,
            )
        except Exception:
            return default_result
