"""Portfolio Health Monitoring Dashboard Service (Sprint 13.4.3)

Consolidates all monitoring-related information into a single dashboard model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from services.portfolio_health_change_detection_service import (
    PortfolioHealthChangeDetectionService,
)
from services.portfolio_health_history_service import PortfolioHealthHistoryService
from services.portfolio_health_monitor_service import PortfolioHealthMonitorService
from services.portfolio_health_timeline_service import PortfolioHealthTimelineService


@dataclass
class PortfolioHealthMonitoringDashboard:
    monitoring_status: str
    monitoring_enabled: bool
    latest_score: int
    latest_grade: str
    latest_snapshot_time: Optional[str]
    total_snapshots: int
    total_detected_changes: int
    latest_change_count: int
    timeline_entries: int


class PortfolioHealthMonitoringDashboardService:
    """Service for building the consolidated portfolio health monitoring dashboard."""

    def __init__(
        self,
        history_service: Optional[PortfolioHealthHistoryService] = None,
        monitor_service: Optional[PortfolioHealthMonitorService] = None,
        change_detection_service: Optional[PortfolioHealthChangeDetectionService] = None,
        timeline_service: Optional[PortfolioHealthTimelineService] = None,
    ) -> None:
        self.history_service = history_service if history_service is not None else PortfolioHealthHistoryService()
        self.monitor_service = (
            monitor_service
            if monitor_service is not None
            else PortfolioHealthMonitorService(history_service=self.history_service)
        )
        self.change_detection_service = (
            change_detection_service
            if change_detection_service is not None
            else PortfolioHealthChangeDetectionService(history_service=self.history_service)
        )
        self.timeline_service = (
            timeline_service
            if timeline_service is not None
            else PortfolioHealthTimelineService(
                history_service=self.history_service,
                change_detection_service=self.change_detection_service,
            )
        )

    def build_dashboard(self) -> PortfolioHealthMonitoringDashboard:
        """Builds and returns the consolidated PortfolioHealthMonitoringDashboard safely without raising exceptions."""
        default_dashboard = PortfolioHealthMonitoringDashboard(
            monitoring_status="UNAVAILABLE",
            monitoring_enabled=False,
            latest_score=0,
            latest_grade="-",
            latest_snapshot_time=None,
            total_snapshots=0,
            total_detected_changes=0,
            latest_change_count=0,
            timeline_entries=0,
        )

        try:
            if self.monitor_service is None or self.timeline_service is None:
                return default_dashboard

            mon_state = self.monitor_service.get_monitoring_state()
            timeline = self.timeline_service.build_timeline()

            monitoring_status = getattr(mon_state, "monitoring_status", "UNAVAILABLE")
            monitoring_enabled = bool(getattr(mon_state, "monitoring_enabled", False))
            latest_score = int(getattr(mon_state, "latest_score", 0))
            latest_grade = str(getattr(mon_state, "latest_grade", "-"))
            latest_snapshot_time = getattr(mon_state, "latest_snapshot_time", None)
            total_snapshots = int(getattr(mon_state, "snapshot_count", 0))

            timeline_entries = int(getattr(timeline, "total_entries", 0))
            entries = getattr(timeline, "entries", []) or []

            total_detected_changes = sum(int(getattr(e, "change_count", 0)) for e in entries)
            latest_change_count = int(getattr(entries[-1], "change_count", 0)) if entries else 0

            return PortfolioHealthMonitoringDashboard(
                monitoring_status=monitoring_status,
                monitoring_enabled=monitoring_enabled,
                latest_score=latest_score,
                latest_grade=latest_grade,
                latest_snapshot_time=latest_snapshot_time,
                total_snapshots=total_snapshots,
                total_detected_changes=total_detected_changes,
                latest_change_count=latest_change_count,
                timeline_entries=timeline_entries,
            )
        except Exception:
            return default_dashboard
