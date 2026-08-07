"""Alert Dashboard Service (Sprint 15.0.3)

Centralized dashboard service that summarizes the current alert ecosystem
and presents alert statistics.

This service is VISUALIZATION / SUMMARY ONLY.
It does NOT generate alerts, modify alerts, send notifications, or recommend investment actions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from services.alert_center_service import PortfolioAlert


@dataclass
class AlertDashboardSummary:
    """Dataclass holding summary counts of alerts across status and severity."""
    total_alerts: int
    active_alerts: int
    acknowledged_alerts: int
    dismissed_alerts: int
    info_alerts: int
    low_alerts: int
    medium_alerts: int
    high_alerts: int
    critical_alerts: int


@dataclass
class AlertDashboard:
    """Dataclass wrapping the overall alert dashboard state."""
    summary: AlertDashboardSummary
    alerts: list[PortfolioAlert]


class AlertDashboardService:
    """Service layer for building and aggregating alert dashboard metrics safely."""

    def __init__(
        self,
        alert_center_service: Optional[Any] = None,
        alert_generation_service: Optional[Any] = None,
        alert_rules_service: Optional[Any] = None,
        storage_path: Optional[str] = None,
    ) -> None:
        self.alert_center_service = alert_center_service
        self.alert_generation_service = alert_generation_service
        self.alert_rules_service = alert_rules_service
        self.storage_path = storage_path

    def build_dashboard(
        self,
        alert_center_state: Optional[Any] = None,
        generated_alerts: Optional[Any] = None,
        alert_rules_result: Optional[Any] = None,
    ) -> AlertDashboard:
        """Build and return an AlertDashboard summarizing existing alert data safely without exceptions.

        Args:
            alert_center_state: Optional state from AlertCenterService.
            generated_alerts: Optional result from AlertGenerationService.
            alert_rules_result: Optional result from AlertRulesService.

        Returns:
            AlertDashboard with summary calculations and alert list.
        """
        default_summary = AlertDashboardSummary(
            total_alerts=0,
            active_alerts=0,
            acknowledged_alerts=0,
            dismissed_alerts=0,
            info_alerts=0,
            low_alerts=0,
            medium_alerts=0,
            high_alerts=0,
            critical_alerts=0,
        )
        default_dashboard = AlertDashboard(summary=default_summary, alerts=[])

        try:
            alerts: list[PortfolioAlert] = []
            seen_ids: set[str] = set()

            # 1. Obtain stored alerts from alert_center_state or alert_center_service
            if alert_center_state is not None:
                ac_alerts = getattr(alert_center_state, "alerts", []) or []
                for a in ac_alerts:
                    aid = getattr(a, "alert_id", "") or str(id(a))
                    if aid not in seen_ids:
                        seen_ids.add(aid)
                        alerts.append(a)
            else:
                try:
                    ac_svc = self.alert_center_service
                    if ac_svc is None:
                        from services.alert_center_service import AlertCenterService
                        ac_svc = AlertCenterService(storage_path=self.storage_path)
                    if hasattr(ac_svc, "get_state"):
                        state = ac_svc.get_state()
                        ac_alerts = getattr(state, "alerts", []) or []
                        for a in ac_alerts:
                            aid = getattr(a, "alert_id", "") or str(id(a))
                            if aid not in seen_ids:
                                seen_ids.add(aid)
                                alerts.append(a)
                    elif hasattr(ac_svc, "load_alerts"):
                        ac_alerts = ac_svc.load_alerts() or []
                        for a in ac_alerts:
                            aid = getattr(a, "alert_id", "") or str(id(a))
                            if aid not in seen_ids:
                                seen_ids.add(aid)
                                alerts.append(a)
                except Exception:
                    pass

            # 2. Obtain generated alerts if provided or via service
            if generated_alerts is not None:
                gen_list = getattr(generated_alerts, "alerts", []) or []
                for a in gen_list:
                    aid = getattr(a, "alert_id", "") or str(id(a))
                    if aid not in seen_ids:
                        seen_ids.add(aid)
                        alerts.append(a)
            elif self.alert_generation_service is not None and hasattr(self.alert_generation_service, "generate_alerts"):
                try:
                    gen_res = self.alert_generation_service.generate_alerts()
                    gen_list = getattr(gen_res, "alerts", []) or []
                    for a in gen_list:
                        aid = getattr(a, "alert_id", "") or str(id(a))
                        if aid not in seen_ids:
                            seen_ids.add(aid)
                            alerts.append(a)
                except Exception:
                    pass

            total_alerts = len(alerts)
            active_alerts = sum(1 for a in alerts if str(getattr(a, "status", "")).upper() == "ACTIVE")
            acknowledged_alerts = sum(1 for a in alerts if str(getattr(a, "status", "")).upper() == "ACKNOWLEDGED")
            dismissed_alerts = sum(1 for a in alerts if str(getattr(a, "status", "")).upper() == "DISMISSED")

            info_alerts = sum(1 for a in alerts if str(getattr(a, "severity", "")).upper() == "INFO")
            low_alerts = sum(1 for a in alerts if str(getattr(a, "severity", "")).upper() == "LOW")
            medium_alerts = sum(1 for a in alerts if str(getattr(a, "severity", "")).upper() == "MEDIUM")
            high_alerts = sum(1 for a in alerts if str(getattr(a, "severity", "")).upper() == "HIGH")
            critical_alerts = sum(1 for a in alerts if str(getattr(a, "severity", "")).upper() == "CRITICAL")

            summary = AlertDashboardSummary(
                total_alerts=total_alerts,
                active_alerts=active_alerts,
                acknowledged_alerts=acknowledged_alerts,
                dismissed_alerts=dismissed_alerts,
                info_alerts=info_alerts,
                low_alerts=low_alerts,
                medium_alerts=medium_alerts,
                high_alerts=high_alerts,
                critical_alerts=critical_alerts,
            )

            return AlertDashboard(summary=summary, alerts=alerts)
        except Exception:
            return default_dashboard
