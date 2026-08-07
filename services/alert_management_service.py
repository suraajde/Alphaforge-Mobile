"""Alert Management Service (Sprint 15.0.5)

Establishes the management layer for portfolio alerts, allowing safe state
management and retrieval of alerts.

Supported state transitions:
- ACTIVE -> ACKNOWLEDGED
- ACTIVE -> DISMISSED
- ACKNOWLEDGED -> DISMISSED

Reverse transitions are NOT allowed.

This service is ALERT MANAGEMENT ONLY.
It does NOT generate alerts, send notifications, or make investment decisions.
"""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Optional

from services.alert_center_service import AlertCenterService, PortfolioAlert


@dataclass
class AlertManagementSummary:
    """Summary of alert management statistics."""
    total_alerts: int
    active_alerts: int
    acknowledged_alerts: int
    dismissed_alerts: int
    last_updated: Optional[str]


@dataclass
class AlertManagementResult:
    """Aggregated result holding management summary and alert list."""
    summary: AlertManagementSummary
    alerts: list[PortfolioAlert]


class AlertManagementService:
    """Service layer for managing portfolio alert state transitions safely."""

    def __init__(
        self,
        alert_center_service: Optional[Any] = None,
        alert_history_service: Optional[Any] = None,
        alert_dashboard_service: Optional[Any] = None,
        storage_path: Optional[str] = None,
    ) -> None:
        self.alert_center_service = alert_center_service
        self.alert_history_service = alert_history_service
        self.alert_dashboard_service = alert_dashboard_service
        self.storage_path = storage_path

    def _get_alert_center_service(self) -> Any:
        if self.alert_center_service is not None:
            return self.alert_center_service
        return AlertCenterService(storage_path=self.storage_path)

    def get_management_summary(self) -> AlertManagementSummary:
        """Returns summary of alert management state safely."""
        return self.get_management_result().summary

    def get_alerts(self) -> list[PortfolioAlert]:
        """Returns current list of managed alerts safely."""
        return self.get_management_result().alerts

    def get_management_result(self) -> AlertManagementResult:
        """Builds and returns the AlertManagementResult safely."""
        default_summary = AlertManagementSummary(
            total_alerts=0,
            active_alerts=0,
            acknowledged_alerts=0,
            dismissed_alerts=0,
            last_updated=None,
        )
        default_result = AlertManagementResult(summary=default_summary, alerts=[])

        try:
            ac_svc = self._get_alert_center_service()
            alerts: list[PortfolioAlert] = []
            if hasattr(ac_svc, "load_alerts"):
                alerts = ac_svc.load_alerts() or []

            total = len(alerts)
            active = sum(1 for a in alerts if str(getattr(a, "status", "")).upper() == "ACTIVE")
            acknowledged = sum(1 for a in alerts if str(getattr(a, "status", "")).upper() == "ACKNOWLEDGED")
            dismissed = sum(1 for a in alerts if str(getattr(a, "status", "")).upper() == "DISMISSED")

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") if alerts else None

            summary = AlertManagementSummary(
                total_alerts=total,
                active_alerts=active,
                acknowledged_alerts=acknowledged,
                dismissed_alerts=dismissed,
                last_updated=now_str,
            )

            return AlertManagementResult(summary=summary, alerts=alerts)
        except Exception:
            return default_result

    def acknowledge_alert(self, alert_id: str) -> AlertManagementResult:
        """Transition alert status from ACTIVE -> ACKNOWLEDGED safely."""
        try:
            if not alert_id:
                return self.get_management_result()

            ac_svc = self._get_alert_center_service()
            if not hasattr(ac_svc, "load_alerts") or not hasattr(ac_svc, "save_alerts"):
                return self.get_management_result()

            alerts = ac_svc.load_alerts() or []
            updated = False
            for alert in alerts:
                if getattr(alert, "alert_id", "") == alert_id:
                    current_status = str(getattr(alert, "status", "")).upper()
                    # Only ACTIVE -> ACKNOWLEDGED is allowed
                    if current_status == "ACTIVE":
                        alert.status = "ACKNOWLEDGED"
                        updated = True
                    break

            if updated:
                ac_svc.save_alerts(alerts)
                if self.alert_history_service is not None and hasattr(self.alert_history_service, "save_history"):
                    try:
                        self.alert_history_service.save_history(alerts)
                    except Exception:
                        pass

            return self.get_management_result()
        except Exception:
            return self.get_management_result()

    def dismiss_alert(self, alert_id: str) -> AlertManagementResult:
        """Transition alert status from ACTIVE -> DISMISSED or ACKNOWLEDGED -> DISMISSED safely."""
        try:
            if not alert_id:
                return self.get_management_result()

            ac_svc = self._get_alert_center_service()
            if not hasattr(ac_svc, "load_alerts") or not hasattr(ac_svc, "save_alerts"):
                return self.get_management_result()

            alerts = ac_svc.load_alerts() or []
            updated = False
            for alert in alerts:
                if getattr(alert, "alert_id", "") == alert_id:
                    current_status = str(getattr(alert, "status", "")).upper()
                    # ACTIVE -> DISMISSED or ACKNOWLEDGED -> DISMISSED allowed
                    if current_status in ["ACTIVE", "ACKNOWLEDGED"]:
                        alert.status = "DISMISSED"
                        updated = True
                    break

            if updated:
                ac_svc.save_alerts(alerts)
                if self.alert_history_service is not None and hasattr(self.alert_history_service, "save_history"):
                    try:
                        self.alert_history_service.save_history(alerts)
                    except Exception:
                        pass

            return self.get_management_result()
        except Exception:
            return self.get_management_result()
