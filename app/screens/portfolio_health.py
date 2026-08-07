from typing import Any, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QFrame,
    QScrollArea,
)

from services.alert_center_service import AlertCenterService
from services.alert_generation_service import AlertGenerationService
from services.alert_rules_service import AlertRulesService
from services.alert_dashboard_service import AlertDashboardService
from services.alert_history_service import AlertHistoryService
from services.alert_management_service import AlertManagementService
from services.decision_engine_service import DecisionEngineService
from services.portfolio_health_change_detection_service import PortfolioHealthChangeDetectionService
from services.portfolio_health_history_service import PortfolioHealthHistoryService
from services.portfolio_health_monitor_dashboard_service import PortfolioHealthMonitoringDashboardService
from services.portfolio_health_monitor_service import PortfolioHealthMonitorService
from services.portfolio_health_service import (
    PortfolioHealthResult,
    PortfolioHealthService,
    PortfolioHealthSnapshot,
)
from services.portfolio_health_timeline_service import PortfolioHealthTimelineService


class PortfolioHealth(QWidget):

    def __init__(
        self,
        service: Optional[PortfolioHealthService] = None,
        history_service: Optional[PortfolioHealthHistoryService] = None,
        monitor_service: Optional[PortfolioHealthMonitorService] = None,
        change_detection_service: Optional[PortfolioHealthChangeDetectionService] = None,
        timeline_service: Optional[PortfolioHealthTimelineService] = None,
        monitoring_dashboard_service: Optional[PortfolioHealthMonitoringDashboardService] = None,
        alert_center_service: Optional[AlertCenterService] = None,
        alert_generation_service: Optional[AlertGenerationService] = None,
        alert_rules_service: Optional[AlertRulesService] = None,
        alert_dashboard_service: Optional[AlertDashboardService] = None,
        alert_history_service: Optional[AlertHistoryService] = None,
        alert_management_service: Optional[AlertManagementService] = None,
        decision_engine_service: Optional[DecisionEngineService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.history_service = history_service if history_service is not None else PortfolioHealthHistoryService()
        self.monitor_service = monitor_service if monitor_service is not None else PortfolioHealthMonitorService(history_service=self.history_service)
        self.change_detection_service = change_detection_service if change_detection_service is not None else PortfolioHealthChangeDetectionService(history_service=self.history_service)
        self.timeline_service = timeline_service if timeline_service is not None else PortfolioHealthTimelineService(
            history_service=self.history_service,
            change_detection_service=self.change_detection_service,
        )
        self.monitoring_dashboard_service = monitoring_dashboard_service if monitoring_dashboard_service is not None else PortfolioHealthMonitoringDashboardService(
            history_service=self.history_service,
            monitor_service=self.monitor_service,
            change_detection_service=self.change_detection_service,
            timeline_service=self.timeline_service,
        )
        self.alert_center_service = alert_center_service if alert_center_service is not None else AlertCenterService()
        self.alert_generation_service = alert_generation_service if alert_generation_service is not None else AlertGenerationService(
            history_service=self.history_service,
            monitor_service=self.monitor_service,
            change_detection_service=self.change_detection_service,
            timeline_service=self.timeline_service,
            dashboard_service=self.monitoring_dashboard_service,
        )
        self.alert_rules_service = alert_rules_service if alert_rules_service is not None else AlertRulesService()
        self.alert_dashboard_service = alert_dashboard_service if alert_dashboard_service is not None else AlertDashboardService(
            alert_center_service=self.alert_center_service,
            alert_generation_service=self.alert_generation_service,
            alert_rules_service=self.alert_rules_service,
        )
        self.alert_history_service = alert_history_service if alert_history_service is not None else AlertHistoryService()
        self.alert_management_service = alert_management_service if alert_management_service is not None else AlertManagementService(
            alert_center_service=self.alert_center_service,
            alert_history_service=self.alert_history_service,
            alert_dashboard_service=self.alert_dashboard_service,
        )
        self.decision_engine_service = decision_engine_service if decision_engine_service is not None else DecisionEngineService()
        self.service = service if service is not None else PortfolioHealthService(
            history_service=self.history_service,
            monitor_service=self.monitor_service,
            change_detection_service=self.change_detection_service,
            timeline_service=self.timeline_service,
            monitoring_dashboard_service=self.monitoring_dashboard_service,
            alert_center_service=self.alert_center_service,
            alert_generation_service=self.alert_generation_service,
            alert_rules_service=self.alert_rules_service,
            alert_dashboard_service=self.alert_dashboard_service,
            alert_history_service=self.alert_history_service,
            alert_management_service=self.alert_management_service,
            decision_engine_service=self.decision_engine_service,
        )
        self._build_ui()
        self.refresh_data()

    def refresh_data(self) -> None:
        """Fetch and bind live portfolio health snapshot, evaluation, and history data."""
        if self.service is not None:
            snapshot = None
            if hasattr(self.service, "build_snapshot"):
                try:
                    snapshot = self.service.build_snapshot()
                    self.load_snapshot(snapshot)
                except Exception:
                    pass

            if hasattr(self.service, "evaluate"):
                try:
                    result = self.service.evaluate(snapshot)
                    self.load_result(result)
                except Exception:
                    pass

        self.load_history()
        self.load_monitoring()
        self.load_change_detection()
        self.load_timeline()
        self.load_monitoring_dashboard()
        self.load_alert_center()
        self.load_generated_alerts()
        self.load_alert_rules()
        self.load_alert_dashboard()
        self.load_alert_history()
        self.load_alert_management()
        self.load_decision_engine()

    def load_decision_engine(self) -> None:
        """Bind live decision engine result to UI."""
        if getattr(self, "decision_engine_service", None) is None:
            return
        try:
            res = self.decision_engine_service.evaluate()
            self._update_decision_engine_ui(res)
        except Exception:
            pass

    def _update_decision_engine_ui(self, result: Any) -> None:
        if result is None:
            return
        summary = getattr(result, "summary", None)
        if summary is not None:
            if hasattr(self, "lbl_de_status"):
                self.lbl_de_status.setText(f"Engine Status: {getattr(summary, 'engine_status', 'UNAVAILABLE')}")
            if hasattr(self, "lbl_de_total"):
                self.lbl_de_total.setText(f"Total Decisions: {getattr(summary, 'total_decisions', 0)}")
            if hasattr(self, "lbl_de_pending"):
                self.lbl_de_pending.setText(f"Pending Decisions: {getattr(summary, 'pending_decisions', 0)}")
            if hasattr(self, "lbl_de_informational"):
                self.lbl_de_informational.setText(f"Informational Decisions: {getattr(summary, 'informational_decisions', 0)}")

        if hasattr(self, "decision_engine_list_container"):
            self._clear_layout(self.decision_engine_list_container)
            decisions = getattr(result, "decisions", [])
            if decisions:
                for decision in decisions:
                    card = QFrame()
                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")
                    lyt = QVBoxLayout(card)
                    lyt.setSpacing(4)
                    lbl = QLabel(str(decision))
                    lbl.setStyleSheet("font-size: 14px; color: #1e293b;")
                    lyt.addWidget(lbl)
                    self.decision_engine_list_container.addWidget(card)
            else:
                lbl = QLabel("No decisions available.")
                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                self.decision_engine_list_container.addWidget(lbl)

    def load_alert_management(self) -> None:
        """Bind live alert management summary to UI."""
        if getattr(self, "alert_management_service", None) is None:
            return
        try:
            res = self.alert_management_service.get_management_result()
            self._update_alert_management_ui(res)
        except Exception:
            pass

    def _update_alert_management_ui(self, mgmt_result: Any) -> None:
        if mgmt_result is None:
            return
        summary = getattr(mgmt_result, "summary", None)
        if summary is not None:
            if hasattr(self, "lbl_am_total"):
                self.lbl_am_total.setText(f"Total Alerts: {getattr(summary, 'total_alerts', 0)}")
            if hasattr(self, "lbl_am_active"):
                self.lbl_am_active.setText(f"Active: {getattr(summary, 'active_alerts', 0)}")
            if hasattr(self, "lbl_am_acknowledged"):
                self.lbl_am_acknowledged.setText(f"Acknowledged: {getattr(summary, 'acknowledged_alerts', 0)}")
            if hasattr(self, "lbl_am_dismissed"):
                self.lbl_am_dismissed.setText(f"Dismissed: {getattr(summary, 'dismissed_alerts', 0)}")
            if hasattr(self, "lbl_am_last_updated"):
                updated = getattr(summary, "last_updated", "N/A") or "N/A"
                self.lbl_am_last_updated.setText(f"Last Updated: {updated}")

        if hasattr(self, "alert_management_list_container"):
            self._clear_layout(self.alert_management_list_container)
            alerts = getattr(mgmt_result, "alerts", [])
            if alerts:
                for alert in alerts:
                    card = QFrame()
                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")
                    lyt = QVBoxLayout(card)
                    lyt.setSpacing(4)

                    id_lbl = QLabel(f"Alert ID: {getattr(alert, 'alert_id', '')}")
                    id_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-weight: 600;")

                    sev = getattr(alert, 'severity', 'INFO')
                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#16a34a" if sev == "LOW" else "#2563eb"
                    sev_lbl = QLabel(f"[{sev}]")
                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    title_lbl = QLabel(getattr(alert, 'title', ''))
                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    status_lbl = QLabel(f"Current Status: {getattr(alert, 'status', 'ACTIVE')}")
                    status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155;")

                    ts_lbl = QLabel(getattr(alert, 'timestamp', ''))
                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    lyt.addWidget(id_lbl)
                    lyt.addWidget(sev_lbl)
                    lyt.addWidget(title_lbl)
                    lyt.addWidget(status_lbl)
                    lyt.addWidget(ts_lbl)
                    self.alert_management_list_container.addWidget(card)
            else:
                lbl = QLabel("No managed alerts")
                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                self.alert_management_list_container.addWidget(lbl)

    def load_alert_history(self) -> None:
        """Bind live alert history summary to UI."""
        if getattr(self, "alert_history_service", None) is None:
            return
        try:
            res = self.alert_history_service.get_history()
            self._update_alert_history_ui(res)
        except Exception:
            pass

    def _update_alert_history_ui(self, history: Any) -> None:
        if history is None:
            return
        if hasattr(self, "lbl_ah_total"):
            self.lbl_ah_total.setText(f"Total Entries: {getattr(history, 'total_entries', 0)}")
        if hasattr(self, "lbl_ah_latest"):
            latest = getattr(history, "latest_timestamp", "N/A") or "N/A"
            self.lbl_ah_latest.setText(f"Latest: {latest}")
        if hasattr(self, "lbl_ah_earliest"):
            earliest = getattr(history, "earliest_timestamp", "N/A") or "N/A"
            self.lbl_ah_earliest.setText(f"Earliest: {earliest}")

        if hasattr(self, "alert_history_list_container"):
            self._clear_layout(self.alert_history_list_container)
            entries = getattr(history, "entries", [])
            if entries:
                for entry in entries:
                    card = QFrame()
                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")
                    lyt = QVBoxLayout(card)
                    lyt.setSpacing(4)

                    ts_lbl = QLabel(getattr(entry, 'timestamp', ''))
                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    sev = getattr(entry, 'severity', 'INFO')
                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#16a34a" if sev == "LOW" else "#2563eb"
                    sev_lbl = QLabel(f"[{sev}]")
                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    type_lbl = QLabel(f"Type: {getattr(entry, 'alert_type', '')}")
                    type_lbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")

                    title_lbl = QLabel(getattr(entry, 'title', ''))
                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    status_lbl = QLabel(f"Status: {getattr(entry, 'status', 'ACTIVE')}")
                    status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155;")

                    lyt.addWidget(ts_lbl)
                    lyt.addWidget(sev_lbl)
                    lyt.addWidget(type_lbl)
                    lyt.addWidget(title_lbl)
                    lyt.addWidget(status_lbl)
                    self.alert_history_list_container.addWidget(card)
            else:
                lbl = QLabel("No alert history")
                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                self.alert_history_list_container.addWidget(lbl)

    def load_alert_dashboard(self) -> None:
        """Bind live alert dashboard summary to UI."""
        if getattr(self, "alert_dashboard_service", None) is None:
            return
        try:
            res = self.alert_dashboard_service.build_dashboard()
            self._update_alert_dashboard_ui(res)
        except Exception:
            pass

    def _update_alert_dashboard_ui(self, dashboard: Any) -> None:
        if dashboard is None:
            return
        summary = getattr(dashboard, "summary", None)
        if summary is not None:
            if hasattr(self, "lbl_ad_total"):
                self.lbl_ad_total.setText(f"Total Alerts: {getattr(summary, 'total_alerts', 0)}")
            if hasattr(self, "lbl_ad_active"):
                self.lbl_ad_active.setText(f"Active: {getattr(summary, 'active_alerts', 0)}")
            if hasattr(self, "lbl_ad_acknowledged"):
                self.lbl_ad_acknowledged.setText(f"Acknowledged: {getattr(summary, 'acknowledged_alerts', 0)}")
            if hasattr(self, "lbl_ad_dismissed"):
                self.lbl_ad_dismissed.setText(f"Dismissed: {getattr(summary, 'dismissed_alerts', 0)}")
            if hasattr(self, "lbl_ad_info"):
                self.lbl_ad_info.setText(f"INFO: {getattr(summary, 'info_alerts', 0)}")
            if hasattr(self, "lbl_ad_low"):
                self.lbl_ad_low.setText(f"LOW: {getattr(summary, 'low_alerts', 0)}")
            if hasattr(self, "lbl_ad_medium"):
                self.lbl_ad_medium.setText(f"MEDIUM: {getattr(summary, 'medium_alerts', 0)}")
            if hasattr(self, "lbl_ad_high"):
                self.lbl_ad_high.setText(f"HIGH: {getattr(summary, 'high_alerts', 0)}")
            if hasattr(self, "lbl_ad_critical"):
                self.lbl_ad_critical.setText(f"CRITICAL: {getattr(summary, 'critical_alerts', 0)}")

        if hasattr(self, "alert_dashboard_list_container"):
            self._clear_layout(self.alert_dashboard_list_container)
            alerts = getattr(dashboard, "alerts", [])
            if alerts:
                for alert in alerts:
                    card = QFrame()
                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")
                    lyt = QVBoxLayout(card)
                    lyt.setSpacing(4)

                    sev = getattr(alert, 'severity', 'INFO')
                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#16a34a" if sev == "LOW" else "#2563eb"
                    sev_lbl = QLabel(f"[{sev}]")
                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    type_lbl = QLabel(f"Type: {getattr(alert, 'alert_type', '')}")
                    type_lbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")

                    title_lbl = QLabel(getattr(alert, 'title', ''))
                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    status_lbl = QLabel(f"Status: {getattr(alert, 'status', 'ACTIVE')}")
                    status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155;")

                    ts_lbl = QLabel(getattr(alert, 'timestamp', ''))
                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    lyt.addWidget(sev_lbl)
                    lyt.addWidget(type_lbl)
                    lyt.addWidget(title_lbl)
                    lyt.addWidget(status_lbl)
                    lyt.addWidget(ts_lbl)
                    self.alert_dashboard_list_container.addWidget(card)
            else:
                lbl = QLabel("No dashboard alerts")
                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                self.alert_dashboard_list_container.addWidget(lbl)

    def load_alert_rules(self) -> None:
        """Bind live alert rules evaluation to UI."""
        if getattr(self, "alert_rules_service", None) is None:
            return
        try:
            res = self.alert_rules_service.evaluate_rules()
            self._update_alert_rules_ui(res)
        except Exception:
            pass

    def _update_alert_rules_ui(self, rules_result: Any) -> None:
        if rules_result is None:
            return
        if hasattr(self, "lbl_alert_rules_total"):
            self.lbl_alert_rules_total.setText(f"Total Rules: {getattr(rules_result, 'total_rules', 0)}")
        if hasattr(self, "lbl_alert_rules_triggered"):
            self.lbl_alert_rules_triggered.setText(f"Triggered Rules: {getattr(rules_result, 'triggered_rules', 0)}")

        if hasattr(self, "alert_rules_list_container"):
            self._clear_layout(self.alert_rules_list_container)
            rules = getattr(rules_result, "rules", [])
            if rules:
                for rule in rules:
                    card = QFrame()
                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")
                    lyt = QVBoxLayout(card)
                    lyt.setSpacing(4)

                    name_lbl = QLabel(getattr(rule, 'rule_name', ''))
                    name_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    sev = getattr(rule, 'severity', 'INFO')
                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#16a34a" if sev == "LOW" else "#2563eb"
                    sev_lbl = QLabel(f"Severity: {sev}")
                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    triggered = getattr(rule, 'triggered', False)
                    triggered_text = "YES" if triggered else "NO"
                    triggered_color = "#16a34a" if triggered else "#64748b"
                    triggered_lbl = QLabel(f"Triggered: {triggered_text}")
                    triggered_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {triggered_color};")

                    desc_lbl = QLabel(getattr(rule, 'description', ''))
                    desc_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    lyt.addWidget(name_lbl)
                    lyt.addWidget(sev_lbl)
                    lyt.addWidget(triggered_lbl)
                    lyt.addWidget(desc_lbl)
                    self.alert_rules_list_container.addWidget(card)
            else:
                lbl = QLabel("No alert rules evaluated")
                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                self.alert_rules_list_container.addWidget(lbl)

    def load_generated_alerts(self) -> None:
        """Bind live generated alerts report to UI."""
        if getattr(self, "alert_generation_service", None) is None:
            return
        try:
            res = self.alert_generation_service.generate_alerts()
            self._update_generated_alerts_ui(res)
        except Exception:
            pass

    def _update_generated_alerts_ui(self, gen_result: Any) -> None:
        if gen_result is None:
            return
        if hasattr(self, "lbl_gen_alerts_count"):
            self.lbl_gen_alerts_count.setText(f"Generated Alerts: {getattr(gen_result, 'generated_alerts', 0)}")

        if hasattr(self, "generated_alerts_container"):
            self._clear_layout(self.generated_alerts_container)
            alerts = getattr(gen_result, "alerts", [])
            if alerts:
                for alert in alerts:
                    card = QFrame()
                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")
                    lyt = QVBoxLayout(card)
                    lyt.setSpacing(4)

                    sev = getattr(alert, 'severity', 'INFO')
                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#2563eb"
                    sev_lbl = QLabel(f"[{sev}]")
                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    type_lbl = QLabel(f"Type: {getattr(alert, 'alert_type', '')}")
                    type_lbl.setStyleSheet("font-size: 13px; color: #475569; font-weight: 600;")

                    ts_lbl = QLabel(getattr(alert, 'timestamp', ''))
                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    title_lbl = QLabel(getattr(alert, 'title', ''))
                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    status_lbl = QLabel(getattr(alert, 'status', 'ACTIVE'))
                    status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155;")

                    lyt.addWidget(sev_lbl)
                    lyt.addWidget(type_lbl)
                    lyt.addWidget(ts_lbl)
                    lyt.addWidget(title_lbl)
                    lyt.addWidget(status_lbl)
                    self.generated_alerts_container.addWidget(card)
            else:
                lbl = QLabel("No generated alerts")
                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                self.generated_alerts_container.addWidget(lbl)

    def load_alert_center(self) -> None:
        """Bind live alert center state to UI."""
        if getattr(self, "alert_center_service", None) is None:
            return
        try:
            state = self.alert_center_service.get_state()
            self._update_alert_center_ui(state)
        except Exception:
            pass

    def _update_alert_center_ui(self, state: Any) -> None:
        if state is None:
            return
        if hasattr(self, "lbl_ac_total"):
            self.lbl_ac_total.setText(f"Total Alerts: {getattr(state, 'total_alerts', 0)}")
        if hasattr(self, "lbl_ac_active"):
            self.lbl_ac_active.setText(f"Active: {getattr(state, 'active_alerts', 0)}")
        if hasattr(self, "lbl_ac_acknowledged"):
            self.lbl_ac_acknowledged.setText(f"Acknowledged: {getattr(state, 'acknowledged_alerts', 0)}")
        if hasattr(self, "lbl_ac_dismissed"):
            self.lbl_ac_dismissed.setText(f"Dismissed: {getattr(state, 'dismissed_alerts', 0)}")

        if hasattr(self, "alerts_list_container"):
            self._clear_layout(self.alerts_list_container)
            alerts = getattr(state, "alerts", [])
            if alerts:
                for alert in alerts:
                    card = QFrame()
                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")
                    lyt = QVBoxLayout(card)
                    lyt.setSpacing(4)

                    sev = getattr(alert, 'severity', 'INFO')
                    sev_color = "#dc2626" if sev in ["HIGH", "CRITICAL"] else "#d97706" if sev == "MEDIUM" else "#2563eb"
                    sev_lbl = QLabel(f"[{sev}]")
                    sev_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {sev_color};")

                    ts_lbl = QLabel(getattr(alert, 'timestamp', ''))
                    ts_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

                    title_lbl = QLabel(getattr(alert, 'title', ''))
                    title_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1e293b;")

                    status_lbl = QLabel(getattr(alert, 'status', 'ACTIVE'))
                    status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #334155;")

                    lyt.addWidget(sev_lbl)
                    lyt.addWidget(ts_lbl)
                    lyt.addWidget(title_lbl)
                    lyt.addWidget(status_lbl)
                    self.alerts_list_container.addWidget(card)
            else:
                lbl = QLabel("No alerts recorded")
                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                self.alerts_list_container.addWidget(lbl)

    def load_monitoring_dashboard(self) -> None:
        """Bind live portfolio health monitoring dashboard to UI."""
        if getattr(self, "monitoring_dashboard_service", None) is None:
            return
        try:
            dashboard = self.monitoring_dashboard_service.build_dashboard()
            self._update_monitoring_dashboard_ui(dashboard)
        except Exception:
            pass

    def _update_monitoring_dashboard_ui(self, dashboard: Any) -> None:
        if dashboard is None:
            return
        if hasattr(self, "lbl_mon_dash_status"):
            self.lbl_mon_dash_status.setText(f"Monitoring Status: {getattr(dashboard, 'monitoring_status', 'UNAVAILABLE')}")
        if hasattr(self, "lbl_mon_dash_enabled"):
            enabled = getattr(dashboard, 'monitoring_enabled', False)
            self.lbl_mon_dash_enabled.setText(f"Monitoring Enabled: {'YES' if enabled else 'NO'}")
        if hasattr(self, "lbl_mon_dash_latest_score"):
            self.lbl_mon_dash_latest_score.setText(f"Latest Score: {getattr(dashboard, 'latest_score', 0)}")
        if hasattr(self, "lbl_mon_dash_latest_grade"):
            self.lbl_mon_dash_latest_grade.setText(f"Latest Grade: {getattr(dashboard, 'latest_grade', '-')}")
        if hasattr(self, "lbl_mon_dash_latest_snapshot"):
            snap_time = getattr(dashboard, 'latest_snapshot_time', "N/A") or "N/A"
            self.lbl_mon_dash_latest_snapshot.setText(f"Latest Snapshot: {snap_time}")
        if hasattr(self, "lbl_mon_dash_total_snapshots"):
            self.lbl_mon_dash_total_snapshots.setText(f"Total Snapshots: {getattr(dashboard, 'total_snapshots', 0)}")
        if hasattr(self, "lbl_mon_dash_timeline_entries"):
            self.lbl_mon_dash_timeline_entries.setText(f"Timeline Entries: {getattr(dashboard, 'timeline_entries', 0)}")
        if hasattr(self, "lbl_mon_dash_latest_change_count"):
            self.lbl_mon_dash_latest_change_count.setText(f"Latest Change Count: {getattr(dashboard, 'latest_change_count', 0)}")
        if hasattr(self, "lbl_mon_dash_total_detected_changes"):
            self.lbl_mon_dash_total_detected_changes.setText(f"Total Detected Changes: {getattr(dashboard, 'total_detected_changes', 0)}")

    def load_timeline(self) -> None:
        """Bind live portfolio health timeline report to UI."""
        if getattr(self, "timeline_service", None) is None:
            return
        try:
            timeline = self.timeline_service.build_timeline()
            self._update_timeline_ui(timeline)
        except Exception:
            pass

    def _update_timeline_ui(self, timeline: Any) -> None:
        if timeline is None:
            return
        if hasattr(self, "lbl_tl_entries"):
            self.lbl_tl_entries.setText(f"Entries: {getattr(timeline, 'total_entries', 0)}")
        if hasattr(self, "lbl_tl_earliest"):
            earliest = getattr(timeline, "earliest_timestamp", "N/A") or "N/A"
            self.lbl_tl_earliest.setText(f"Earliest: {earliest}")
        if hasattr(self, "lbl_tl_latest"):
            latest = getattr(timeline, "latest_timestamp", "N/A") or "N/A"
            self.lbl_tl_latest.setText(f"Latest: {latest}")

        if hasattr(self, "timeline_list_container"):
            self._clear_layout(self.timeline_list_container)
            entries = getattr(timeline, "entries", [])
            if entries:
                for entry in entries:
                    card = QFrame()
                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px;")
                    lyt = QVBoxLayout(card)
                    lyt.setSpacing(4)

                    ts_lbl = QLabel(f"#{getattr(entry, 'sequence', '')}  {getattr(entry, 'timestamp', '')}")
                    ts_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67;")

                    score_lbl = QLabel(f"Score: {getattr(entry, 'score', 0)}")
                    score_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")

                    grade_lbl = QLabel(f"Grade: {getattr(entry, 'grade', '-')}")
                    grade_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")

                    trend = getattr(entry, "trend_direction", "STABLE")
                    t_color = "#16a34a" if trend == "IMPROVING" else "#dc2626" if trend == "DETERIORATING" else "#64748b"
                    trend_lbl = QLabel(f"Trend: {trend}")
                    trend_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {t_color};")

                    changes_lbl = QLabel(f"Changes: {getattr(entry, 'change_count', 0)}")
                    changes_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")

                    lyt.addWidget(ts_lbl)
                    lyt.addWidget(score_lbl)
                    lyt.addWidget(grade_lbl)
                    lyt.addWidget(trend_lbl)
                    lyt.addWidget(changes_lbl)
                    self.timeline_list_container.addWidget(card)
            else:
                lbl = QLabel("No timeline entries available")
                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                self.timeline_list_container.addWidget(lbl)

    def load_change_detection(self) -> None:
        """Bind live portfolio health change detection report to UI."""
        if getattr(self, "change_detection_service", None) is None:
            return
        try:
            report = self.change_detection_service.detect_changes()
            self._update_change_detection_ui(report)
        except Exception:
            pass

    def _update_change_detection_ui(self, report: Any) -> None:
        if report is None:
            return
        if hasattr(self, "lbl_cd_snapshots_compared"):
            self.lbl_cd_snapshots_compared.setText(f"Snapshots Compared: {getattr(report, 'snapshot_count', 0)}")
        if hasattr(self, "lbl_cd_changes_detected"):
            has_chg = getattr(report, 'has_changes', False)
            self.lbl_cd_changes_detected.setText(f"Changes Detected: {'YES' if has_chg else 'NO'}")
        if hasattr(self, "lbl_cd_total_changes"):
            self.lbl_cd_total_changes.setText(f"Total Changes: {getattr(report, 'total_changes', 0)}")

        if hasattr(self, "changes_list_container"):
            self._clear_layout(self.changes_list_container)
            changes = getattr(report, "changes", [])
            changed_items = [c for c in changes if getattr(c, "change_type", "UNCHANGED") != "UNCHANGED"]
            if changed_items:
                for item in changed_items:
                    card = QFrame()
                    card.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px;")
                    lyt = QVBoxLayout(card)
                    lyt.setSpacing(4)
                    fname_lbl = QLabel(getattr(item, "field_name", ""))
                    fname_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #173b67;")
                    val_lbl = QLabel(f"{getattr(item, 'previous_value', '')} → {getattr(item, 'current_value', '')}")
                    val_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
                    ctype = getattr(item, "change_type", "")
                    color = "#16a34a" if ctype == "INCREASED" else "#dc2626" if ctype == "DECREASED" else "#2563eb"
                    type_lbl = QLabel(ctype)
                    type_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {color};")
                    lyt.addWidget(fname_lbl)
                    lyt.addWidget(val_lbl)
                    lyt.addWidget(type_lbl)
                    self.changes_list_container.addWidget(card)
            else:
                lbl = QLabel("No changes detected")
                lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                self.changes_list_container.addWidget(lbl)

    def load_monitoring(self) -> None:
        """Bind live portfolio health monitoring metrics to UI."""
        if getattr(self, "monitor_service", None) is None:
            return
        try:
            state = self.monitor_service.get_monitoring_state()
            if state is not None:
                if hasattr(self, "lbl_mon_enabled"):
                    enabled_str = "YES" if state.monitoring_enabled else "NO"
                    self.lbl_mon_enabled.setText(f"Monitoring Enabled: {enabled_str}")
                if hasattr(self, "lbl_mon_status"):
                    self.lbl_mon_status.setText(f"Monitoring Status: {state.monitoring_status}")
                if hasattr(self, "lbl_mon_snapshots"):
                    self.lbl_mon_snapshots.setText(f"Snapshots Available: {state.snapshot_count}")
                if hasattr(self, "lbl_mon_latest_snapshot"):
                    time_str = state.latest_snapshot_time if state.latest_snapshot_time else "N/A"
                    self.lbl_mon_latest_snapshot.setText(f"Latest Snapshot: {time_str}")
                if hasattr(self, "lbl_mon_latest_score"):
                    self.lbl_mon_latest_score.setText(f"Latest Score: {state.latest_score}")
                if hasattr(self, "lbl_mon_latest_grade"):
                    self.lbl_mon_latest_grade.setText(f"Latest Grade: {state.latest_grade}")
        except Exception:
            pass

    def load_history(self) -> None:
        """Bind live portfolio health history metrics to UI."""
        if getattr(self, "history_service", None) is None:
            return
        try:
            history = self.history_service.get_history()
            count = len(history) if history else 0
            latest = history[-1] if history else None

            if hasattr(self, "lbl_history_entries"):
                self.lbl_history_entries.setText(f"History Entries: {count}")
            if hasattr(self, "lbl_history_latest_score"):
                score_str = str(latest.score) if latest else "N/A"
                self.lbl_history_latest_score.setText(f"Latest Score: {score_str}")
            if hasattr(self, "lbl_history_latest_grade"):
                grade_str = str(latest.grade) if latest else "N/A"
                self.lbl_history_latest_grade.setText(f"Latest Grade: {grade_str}")
        except Exception:
            pass

    def load_snapshot(self, snapshot: Optional[PortfolioHealthSnapshot] = None) -> None:
        """Bind live snapshot metrics to the metric cards."""
        if snapshot is None:
            return

        if "Position Count" in self.cards:
            self.cards["Position Count"].setText(str(snapshot.position_count))

        if "Cash Allocation" in self.cards:
            val = snapshot.cash_allocation_pct
            val_str = f"{val:.1f}%" if (val % 1 != 0) else f"{int(val)}%"
            self.cards["Cash Allocation"].setText(val_str)

        if "Largest Position" in self.cards:
            self.cards["Largest Position"].setText(str(snapshot.largest_position))

    def load_result(self, result: Optional[PortfolioHealthResult] = None) -> None:
        """Bind live PortfolioHealthResult metrics to score, diversification, concentration, and analytics sections."""
        if result is None:
            return

        if "Overall Health Score" in self.cards:
            grade_suffix = f" ({result.grade})" if getattr(result, "grade", None) else ""
            self.cards["Overall Health Score"].setText(f"{result.score} / 100{grade_suffix}")

        if "Diversification" in self.cards:
            self.cards["Diversification"].setText(str(result.diversification_rating))

        if "Concentration" in self.cards:
            self.cards["Concentration"].setText(str(result.concentration_rating))

        analytics = getattr(result, "analytics", None)
        if analytics is not None:
            if hasattr(self, "lbl_breakdown_div"):
                self.lbl_breakdown_div.setText(f"Diversification: {analytics.diversification_score} / 40")
            if hasattr(self, "lbl_breakdown_conc"):
                self.lbl_breakdown_conc.setText(f"Concentration: {analytics.concentration_score} / 40")
            if hasattr(self, "lbl_breakdown_cash"):
                self.lbl_breakdown_cash.setText(f"Cash Allocation: {analytics.cash_score} / 20")

            if hasattr(self, "strengths_container"):
                self._clear_layout(self.strengths_container)
                if analytics.strengths:
                    for item in analytics.strengths:
                        lbl = QLabel(f"• {item}")
                        lbl.setStyleSheet("font-size: 14px; color: #16a34a; font-weight: 500;")
                        self.strengths_container.addWidget(lbl)
                else:
                    lbl = QLabel("None identified")
                    lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                    self.strengths_container.addWidget(lbl)

            if hasattr(self, "weaknesses_container"):
                self._clear_layout(self.weaknesses_container)
                if analytics.weaknesses:
                    for item in analytics.weaknesses:
                        lbl = QLabel(f"• {item}")
                        lbl.setStyleSheet("font-size: 14px; color: #dc2626; font-weight: 500;")
                        self.weaknesses_container.addWidget(lbl)
                else:
                    lbl = QLabel("None identified")
                    lbl.setStyleSheet("font-size: 14px; color: #64748b; font-style: italic;")
                    self.weaknesses_container.addWidget(lbl)

        trend = getattr(result, "trend", None)
        if trend is not None:
            if hasattr(self, "lbl_trend_current"):
                self.lbl_trend_current.setText(f"Current Score: {trend.current_score}")
            if hasattr(self, "lbl_trend_previous"):
                self.lbl_trend_previous.setText(f"Previous Score: {trend.previous_score}")
            if hasattr(self, "lbl_trend_change"):
                change_str = f"+{trend.score_change}" if trend.score_change > 0 else str(trend.score_change)
                self.lbl_trend_change.setText(f"Score Change: {change_str}")
            if hasattr(self, "lbl_trend_direction"):
                self.lbl_trend_direction.setText(f"Trend: {trend.trend_direction}")

        hist_analytics = getattr(result, "historical_analytics", None)
        if hist_analytics is not None:
            if hasattr(self, "lbl_hist_entries"):
                self.lbl_hist_entries.setText(f"History Entries: {hist_analytics.history_count}")
            if hasattr(self, "lbl_hist_best"):
                self.lbl_hist_best.setText(f"Best Score: {hist_analytics.best_score}")
            if hasattr(self, "lbl_hist_worst"):
                self.lbl_hist_worst.setText(f"Worst Score: {hist_analytics.worst_score}")
            if hasattr(self, "lbl_hist_avg"):
                self.lbl_hist_avg.setText(f"Average Score: {hist_analytics.average_score}")
            if hasattr(self, "lbl_hist_curr"):
                self.lbl_hist_curr.setText(f"Current Score: {hist_analytics.current_score}")
            if hasattr(self, "lbl_hist_trend"):
                self.lbl_hist_trend.setText(f"Overall Trend: {hist_analytics.overall_trend}")

        summary = getattr(result, "dashboard_summary", None)
        if summary is not None:
            if hasattr(self, "lbl_dash_curr_score"):
                self.lbl_dash_curr_score.setText(f"Current Score: {summary.current_score}")
            if hasattr(self, "lbl_dash_curr_grade"):
                self.lbl_dash_curr_grade.setText(f"Current Grade: {summary.current_grade}")
            if hasattr(self, "lbl_dash_best_score"):
                self.lbl_dash_best_score.setText(f"Best Historical Score: {summary.best_score}")
            if hasattr(self, "lbl_dash_best_grade"):
                self.lbl_dash_best_grade.setText(f"Best Historical Grade: {summary.best_grade}")
            if hasattr(self, "lbl_dash_worst_score"):
                self.lbl_dash_worst_score.setText(f"Worst Historical Score: {summary.worst_score}")
            if hasattr(self, "lbl_dash_worst_grade"):
                self.lbl_dash_worst_grade.setText(f"Worst Historical Grade: {summary.worst_grade}")
            if hasattr(self, "lbl_dash_avg_score"):
                self.lbl_dash_avg_score.setText(f"Average Historical Score: {summary.average_score}")
            if hasattr(self, "lbl_dash_total_snapshots"):
                self.lbl_dash_total_snapshots.setText(f"Total Snapshots: {summary.total_snapshots}")

            if hasattr(self, "lbl_highlight_highest"):
                self.lbl_highlight_highest.setText(f"Highest Score Achieved: {summary.best_score}")
            if hasattr(self, "lbl_highlight_lowest"):
                self.lbl_highlight_lowest.setText(f"Lowest Score Achieved: {summary.worst_score}")
            if hasattr(self, "lbl_highlight_vs_avg"):
                diff = round(summary.current_score - summary.average_score, 1)
                diff_str = f"+{diff}" if diff > 0 else str(diff)
                self.lbl_highlight_vs_avg.setText(f"Current Score vs Average: {diff_str}")

        metrics = getattr(result, "historical_metrics", None)
        if metrics is not None:
            if hasattr(self, "lbl_metrics_range"):
                self.lbl_metrics_range.setText(f"Score Range: {metrics.score_range}")
            if hasattr(self, "lbl_metrics_volatility"):
                self.lbl_metrics_volatility.setText(f"Volatility Score: {metrics.volatility_score}")
            if hasattr(self, "lbl_metrics_improving"):
                self.lbl_metrics_improving.setText(f"Improving Periods: {metrics.improving_periods}")
            if hasattr(self, "lbl_metrics_deteriorating"):
                self.lbl_metrics_deteriorating.setText(f"Deteriorating Periods: {metrics.deteriorating_periods}")
            if hasattr(self, "lbl_metrics_stability"):
                self.lbl_metrics_stability.setText(f"Stability Rating: {metrics.stability_rating}")

        insights = getattr(result, "historical_insights", None)
        if insights is not None:
            if hasattr(self, "lbl_insights_improvement"):
                self.lbl_insights_improvement.setText(f"Improvement Percentage: {insights.improvement_percentage}%")
            if hasattr(self, "lbl_insights_deterioration"):
                self.lbl_insights_deterioration.setText(f"Deterioration Percentage: {insights.deterioration_percentage}%")
            if hasattr(self, "lbl_insights_neutral"):
                self.lbl_insights_neutral.setText(f"Neutral Percentage: {insights.neutral_percentage}%")
            if hasattr(self, "lbl_insights_consistency"):
                self.lbl_insights_consistency.setText(f"Consistency Score: {insights.consistency_score}")
            if hasattr(self, "lbl_insights_quality"):
                self.lbl_insights_quality.setText(f"Quality Rating: {insights.quality_rating}")
            if hasattr(self, "lbl_insights_direction"):
                self.lbl_insights_direction.setText(f"Direction Rating: {insights.direction_rating}")

        mon_state = getattr(result, "monitoring_state", None)
        if mon_state is not None:
            if hasattr(self, "lbl_mon_enabled"):
                enabled_str = "YES" if mon_state.monitoring_enabled else "NO"
                self.lbl_mon_enabled.setText(f"Monitoring Enabled: {enabled_str}")
            if hasattr(self, "lbl_mon_status"):
                self.lbl_mon_status.setText(f"Monitoring Status: {mon_state.monitoring_status}")
            if hasattr(self, "lbl_mon_snapshots"):
                self.lbl_mon_snapshots.setText(f"Snapshots Available: {mon_state.snapshot_count}")
            if hasattr(self, "lbl_mon_latest_snapshot"):
                time_str = mon_state.latest_snapshot_time if mon_state.latest_snapshot_time else "N/A"
                self.lbl_mon_latest_snapshot.setText(f"Latest Snapshot: {time_str}")
            if hasattr(self, "lbl_mon_latest_score"):
                self.lbl_mon_latest_score.setText(f"Latest Score: {mon_state.latest_score}")
            if hasattr(self, "lbl_mon_latest_grade"):
                self.lbl_mon_latest_grade.setText(f"Latest Grade: {mon_state.latest_grade}")

        cd_report = getattr(result, "change_report", None)
        if cd_report is not None:
            self._update_change_detection_ui(cd_report)

        timeline = getattr(result, "timeline", None)
        if timeline is not None:
            self._update_timeline_ui(timeline)

        mon_dash = getattr(result, "monitoring_dashboard", None)
        if mon_dash is not None:
            self._update_monitoring_dashboard_ui(mon_dash)

        ac_state = getattr(result, "alert_center", None)
        if ac_state is not None:
            self._update_alert_center_ui(ac_state)

        gen_res = getattr(result, "generated_alerts", None)
        if gen_res is not None:
            self._update_generated_alerts_ui(gen_res)

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def _build_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f7fb;
                color: #1f2937;
                font-family: Segoe UI;
            }

            QLabel#pageTitle {
                font-size: 28px;
                font-weight: 700;
                color: #173b67;
            }

            QLabel#pageSubtitle {
                font-size: 14px;
                color: #64748b;
            }

            QFrame#metricCard {
                background-color: white;
                border: 1px solid #dce3ed;
                border-radius: 10px;
            }

            QLabel#cardTitle {
                font-size: 12px;
                font-weight: 600;
                color: #64748b;
            }

            QLabel#cardValue {
                font-size: 22px;
                font-weight: 700;
                color: #173b67;
            }

            QLabel#sectionHeader {
                font-size: 16px;
                font-weight: 700;
                color: #173b67;
            }
        """)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        content_widget = QWidget()
        root_layout = QVBoxLayout(content_widget)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(20)

        # Header Title
        title_box = QVBoxLayout()
        header_title = QLabel("Portfolio Health")
        header_title.setObjectName("pageTitle")

        header_subtitle = QLabel("Overview of key health and risk metrics for your portfolio")
        header_subtitle.setObjectName("pageSubtitle")

        title_box.addWidget(header_title)
        title_box.addWidget(header_subtitle)
        root_layout.addLayout(title_box)

        # Metric Cards Grid Layout
        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)

        cards_spec = [
            ("Overall Health Score", "85 / 100", 0, 0),
            ("Diversification", "GOOD", 0, 1),
            ("Concentration", "MODERATE", 0, 2),
            ("Position Count", "12", 1, 0),
            ("Cash Allocation", "5%", 1, 1),
            ("Largest Position", "KPITTECH", 1, 2),
        ]

        self.cards = {}
        for title, value, row, col in cards_spec:
            card_frame, val_lbl = self._create_metric_card(title, value)
            cards_grid.addWidget(card_frame, row, col)
            self.cards[title] = val_lbl

        root_layout.addLayout(cards_grid)

        # Analytics Sections: Health Score Breakdown
        breakdown_card = QFrame()
        breakdown_card.setObjectName("metricCard")
        breakdown_layout = QVBoxLayout(breakdown_card)
        breakdown_layout.setContentsMargins(16, 14, 16, 14)
        breakdown_layout.setSpacing(8)

        lbl_breakdown_header = QLabel("Health Score Breakdown")
        lbl_breakdown_header.setObjectName("sectionHeader")
        breakdown_layout.addWidget(lbl_breakdown_header)

        self.lbl_breakdown_div = QLabel("Diversification: - / 40")
        self.lbl_breakdown_div.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_breakdown_conc = QLabel("Concentration: - / 40")
        self.lbl_breakdown_conc.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_breakdown_cash = QLabel("Cash Allocation: - / 20")
        self.lbl_breakdown_cash.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        breakdown_layout.addWidget(self.lbl_breakdown_div)
        breakdown_layout.addWidget(self.lbl_breakdown_conc)
        breakdown_layout.addWidget(self.lbl_breakdown_cash)

        root_layout.addWidget(breakdown_card)

        # Strengths Section
        strengths_card = QFrame()
        strengths_card.setObjectName("metricCard")
        strengths_layout = QVBoxLayout(strengths_card)
        strengths_layout.setContentsMargins(16, 14, 16, 14)
        strengths_layout.setSpacing(8)

        lbl_strengths_header = QLabel("Strengths")
        lbl_strengths_header.setObjectName("sectionHeader")
        strengths_layout.addWidget(lbl_strengths_header)

        self.strengths_container = QVBoxLayout()
        strengths_layout.addLayout(self.strengths_container)

        root_layout.addWidget(strengths_card)

        # Weaknesses Section
        weaknesses_card = QFrame()
        weaknesses_card.setObjectName("metricCard")
        weaknesses_layout = QVBoxLayout(weaknesses_card)
        weaknesses_layout.setContentsMargins(16, 14, 16, 14)
        weaknesses_layout.setSpacing(8)

        lbl_weaknesses_header = QLabel("Weaknesses")
        lbl_weaknesses_header.setObjectName("sectionHeader")
        weaknesses_layout.addWidget(lbl_weaknesses_header)

        self.weaknesses_container = QVBoxLayout()
        weaknesses_layout.addLayout(self.weaknesses_container)

        root_layout.addWidget(weaknesses_card)

        # Portfolio Health Trend Section
        trend_card = QFrame()
        trend_card.setObjectName("metricCard")
        trend_layout = QVBoxLayout(trend_card)
        trend_layout.setContentsMargins(16, 14, 16, 14)
        trend_layout.setSpacing(8)

        lbl_trend_header = QLabel("Portfolio Health Trend")
        lbl_trend_header.setObjectName("sectionHeader")
        trend_layout.addWidget(lbl_trend_header)

        self.lbl_trend_current = QLabel("Current Score: -")
        self.lbl_trend_current.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_trend_previous = QLabel("Previous Score: -")
        self.lbl_trend_previous.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_trend_change = QLabel("Score Change: -")
        self.lbl_trend_change.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_trend_direction = QLabel("Trend: -")
        self.lbl_trend_direction.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        trend_layout.addWidget(self.lbl_trend_current)
        trend_layout.addWidget(self.lbl_trend_previous)
        trend_layout.addWidget(self.lbl_trend_change)
        trend_layout.addWidget(self.lbl_trend_direction)

        root_layout.addWidget(trend_card)

        # Portfolio Health History Section
        history_card = QFrame()
        history_card.setObjectName("metricCard")
        history_layout = QVBoxLayout(history_card)
        history_layout.setContentsMargins(16, 14, 16, 14)
        history_layout.setSpacing(8)

        lbl_history_header = QLabel("Portfolio Health History")
        lbl_history_header.setObjectName("sectionHeader")
        history_layout.addWidget(lbl_history_header)

        self.lbl_history_entries = QLabel("History Entries: 0")
        self.lbl_history_entries.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_history_latest_score = QLabel("Latest Score: N/A")
        self.lbl_history_latest_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_history_latest_grade = QLabel("Latest Grade: N/A")
        self.lbl_history_latest_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        history_layout.addWidget(self.lbl_history_entries)
        history_layout.addWidget(self.lbl_history_latest_score)
        history_layout.addWidget(self.lbl_history_latest_grade)

        root_layout.addWidget(history_card)

        # Portfolio Health Historical Analytics Section
        hist_card = QFrame()
        hist_card.setObjectName("metricCard")
        hist_layout = QVBoxLayout(hist_card)
        hist_layout.setContentsMargins(16, 14, 16, 14)
        hist_layout.setSpacing(8)

        lbl_hist_header = QLabel("Portfolio Health Historical Analytics")
        lbl_hist_header.setObjectName("sectionHeader")
        hist_layout.addWidget(lbl_hist_header)

        self.lbl_hist_entries = QLabel("History Entries: 0")
        self.lbl_hist_entries.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_hist_best = QLabel("Best Score: 0")
        self.lbl_hist_best.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_hist_worst = QLabel("Worst Score: 0")
        self.lbl_hist_worst.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_hist_avg = QLabel("Average Score: 0.0")
        self.lbl_hist_avg.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_hist_curr = QLabel("Current Score: 0")
        self.lbl_hist_curr.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_hist_trend = QLabel("Overall Trend: STABLE")
        self.lbl_hist_trend.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        hist_layout.addWidget(self.lbl_hist_entries)
        hist_layout.addWidget(self.lbl_hist_best)
        hist_layout.addWidget(self.lbl_hist_worst)
        hist_layout.addWidget(self.lbl_hist_avg)
        hist_layout.addWidget(self.lbl_hist_curr)
        hist_layout.addWidget(self.lbl_hist_trend)

        root_layout.addWidget(hist_card)

        # Portfolio Health Dashboard Summary Section
        dash_card = QFrame()
        dash_card.setObjectName("metricCard")
        dash_layout = QVBoxLayout(dash_card)
        dash_layout.setContentsMargins(16, 14, 16, 14)
        dash_layout.setSpacing(8)

        lbl_dash_header = QLabel("Portfolio Health Dashboard Summary")
        lbl_dash_header.setObjectName("sectionHeader")
        dash_layout.addWidget(lbl_dash_header)

        self.lbl_dash_curr_score = QLabel("Current Score: 0")
        self.lbl_dash_curr_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_curr_grade = QLabel("Current Grade: -")
        self.lbl_dash_curr_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_best_score = QLabel("Best Historical Score: 0")
        self.lbl_dash_best_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_best_grade = QLabel("Best Historical Grade: -")
        self.lbl_dash_best_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_worst_score = QLabel("Worst Historical Score: 0")
        self.lbl_dash_worst_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_worst_grade = QLabel("Worst Historical Grade: -")
        self.lbl_dash_worst_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_avg_score = QLabel("Average Historical Score: 0.0")
        self.lbl_dash_avg_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_dash_total_snapshots = QLabel("Total Snapshots: 0")
        self.lbl_dash_total_snapshots.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        dash_layout.addWidget(self.lbl_dash_curr_score)
        dash_layout.addWidget(self.lbl_dash_curr_grade)
        dash_layout.addWidget(self.lbl_dash_best_score)
        dash_layout.addWidget(self.lbl_dash_best_grade)
        dash_layout.addWidget(self.lbl_dash_worst_score)
        dash_layout.addWidget(self.lbl_dash_worst_grade)
        dash_layout.addWidget(self.lbl_dash_avg_score)
        dash_layout.addWidget(self.lbl_dash_total_snapshots)

        # Historical Highlights Subsection
        lbl_highlights_header = QLabel("Historical Highlights")
        lbl_highlights_header.setObjectName("sectionHeader")
        lbl_highlights_header.setStyleSheet("font-size: 15px; font-weight: 700; color: #173b67; margin-top: 6px;")
        dash_layout.addWidget(lbl_highlights_header)

        self.lbl_highlight_highest = QLabel("Highest Score Achieved: 0")
        self.lbl_highlight_highest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_highlight_lowest = QLabel("Lowest Score Achieved: 0")
        self.lbl_highlight_lowest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_highlight_vs_avg = QLabel("Current Score vs Average: 0.0")
        self.lbl_highlight_vs_avg.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        dash_layout.addWidget(self.lbl_highlight_highest)
        dash_layout.addWidget(self.lbl_highlight_lowest)
        dash_layout.addWidget(self.lbl_highlight_vs_avg)

        root_layout.addWidget(dash_card)

        # Portfolio Health Historical Metrics Section
        metrics_card = QFrame()
        metrics_card.setObjectName("metricCard")
        metrics_layout = QVBoxLayout(metrics_card)
        metrics_layout.setContentsMargins(16, 14, 16, 14)
        metrics_layout.setSpacing(8)

        lbl_metrics_header = QLabel("Portfolio Health Historical Metrics")
        lbl_metrics_header.setObjectName("sectionHeader")
        metrics_layout.addWidget(lbl_metrics_header)

        self.lbl_metrics_range = QLabel("Score Range: 0")
        self.lbl_metrics_range.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_metrics_volatility = QLabel("Volatility Score: 0.0")
        self.lbl_metrics_volatility.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_metrics_improving = QLabel("Improving Periods: 0")
        self.lbl_metrics_improving.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_metrics_deteriorating = QLabel("Deteriorating Periods: 0")
        self.lbl_metrics_deteriorating.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_metrics_stability = QLabel("Stability Rating: VERY_STABLE")
        self.lbl_metrics_stability.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        metrics_layout.addWidget(self.lbl_metrics_range)
        metrics_layout.addWidget(self.lbl_metrics_volatility)
        metrics_layout.addWidget(self.lbl_metrics_improving)
        metrics_layout.addWidget(self.lbl_metrics_deteriorating)
        metrics_layout.addWidget(self.lbl_metrics_stability)

        root_layout.addWidget(metrics_card)

        # Portfolio Health Historical Insights Section
        insights_card = QFrame()
        insights_card.setObjectName("metricCard")
        insights_layout = QVBoxLayout(insights_card)
        insights_layout.setContentsMargins(16, 14, 16, 14)
        insights_layout.setSpacing(8)

        lbl_insights_header = QLabel("Portfolio Health Historical Insights")
        lbl_insights_header.setObjectName("sectionHeader")
        insights_layout.addWidget(lbl_insights_header)

        self.lbl_insights_improvement = QLabel("Improvement Percentage: 0.0%")
        self.lbl_insights_improvement.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_insights_deterioration = QLabel("Deterioration Percentage: 0.0%")
        self.lbl_insights_deterioration.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_insights_neutral = QLabel("Neutral Percentage: 0.0%")
        self.lbl_insights_neutral.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_insights_consistency = QLabel("Consistency Score: 0.0")
        self.lbl_insights_consistency.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_insights_quality = QLabel("Quality Rating: MIXED")
        self.lbl_insights_quality.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_insights_direction = QLabel("Direction Rating: STABLE")
        self.lbl_insights_direction.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        insights_layout.addWidget(self.lbl_insights_improvement)
        insights_layout.addWidget(self.lbl_insights_deterioration)
        insights_layout.addWidget(self.lbl_insights_neutral)
        insights_layout.addWidget(self.lbl_insights_consistency)
        insights_layout.addWidget(self.lbl_insights_quality)
        insights_layout.addWidget(self.lbl_insights_direction)

        root_layout.addWidget(insights_card)

        # Portfolio Health Monitoring Section
        monitoring_card = QFrame()
        monitoring_card.setObjectName("metricCard")
        monitoring_layout = QVBoxLayout(monitoring_card)
        monitoring_layout.setContentsMargins(16, 14, 16, 14)
        monitoring_layout.setSpacing(8)

        lbl_monitoring_header = QLabel("Portfolio Health Monitoring")
        lbl_monitoring_header.setObjectName("sectionHeader")
        monitoring_layout.addWidget(lbl_monitoring_header)

        self.lbl_mon_enabled = QLabel("Monitoring Enabled: NO")
        self.lbl_mon_enabled.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_status = QLabel("Monitoring Status: UNAVAILABLE")
        self.lbl_mon_status.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_snapshots = QLabel("Snapshots Available: 0")
        self.lbl_mon_snapshots.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_latest_snapshot = QLabel("Latest Snapshot: N/A")
        self.lbl_mon_latest_snapshot.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_latest_score = QLabel("Latest Score: 0")
        self.lbl_mon_latest_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_latest_grade = QLabel("Latest Grade: -")
        self.lbl_mon_latest_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        monitoring_layout.addWidget(self.lbl_mon_enabled)
        monitoring_layout.addWidget(self.lbl_mon_status)
        monitoring_layout.addWidget(self.lbl_mon_snapshots)
        monitoring_layout.addWidget(self.lbl_mon_latest_snapshot)
        monitoring_layout.addWidget(self.lbl_mon_latest_score)
        monitoring_layout.addWidget(self.lbl_mon_latest_grade)

        root_layout.addWidget(monitoring_card)

        # Portfolio Health Change Detection Section
        cd_card = QFrame()
        cd_card.setObjectName("metricCard")
        cd_layout = QVBoxLayout(cd_card)
        cd_layout.setContentsMargins(16, 14, 16, 14)
        cd_layout.setSpacing(8)

        lbl_cd_header = QLabel("Portfolio Health Change Detection")
        lbl_cd_header.setObjectName("sectionHeader")
        cd_layout.addWidget(lbl_cd_header)

        self.lbl_cd_snapshots_compared = QLabel("Snapshots Compared: 0")
        self.lbl_cd_snapshots_compared.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_cd_changes_detected = QLabel("Changes Detected: NO")
        self.lbl_cd_changes_detected.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_cd_total_changes = QLabel("Total Changes: 0")
        self.lbl_cd_total_changes.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        cd_layout.addWidget(self.lbl_cd_snapshots_compared)
        cd_layout.addWidget(self.lbl_cd_changes_detected)
        cd_layout.addWidget(self.lbl_cd_total_changes)

        lbl_changes_subheader = QLabel("Changes")
        lbl_changes_subheader.setStyleSheet("font-size: 15px; font-weight: 700; color: #173b67; margin-top: 6px;")
        cd_layout.addWidget(lbl_changes_subheader)

        self.changes_list_container = QVBoxLayout()
        cd_layout.addLayout(self.changes_list_container)

        root_layout.addWidget(cd_card)

        # Portfolio Health Timeline Section
        tl_card = QFrame()
        tl_card.setObjectName("metricCard")
        tl_layout = QVBoxLayout(tl_card)
        tl_layout.setContentsMargins(16, 14, 16, 14)
        tl_layout.setSpacing(8)

        lbl_tl_header = QLabel("Portfolio Health Timeline")
        lbl_tl_header.setObjectName("sectionHeader")
        tl_layout.addWidget(lbl_tl_header)

        self.lbl_tl_entries = QLabel("Entries: 0")
        self.lbl_tl_entries.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_tl_earliest = QLabel("Earliest: N/A")
        self.lbl_tl_earliest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_tl_latest = QLabel("Latest: N/A")
        self.lbl_tl_latest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        tl_layout.addWidget(self.lbl_tl_entries)
        tl_layout.addWidget(self.lbl_tl_earliest)
        tl_layout.addWidget(self.lbl_tl_latest)

        self.timeline_list_container = QVBoxLayout()
        tl_layout.addLayout(self.timeline_list_container)

        root_layout.addWidget(tl_card)

        # Portfolio Health Monitoring Dashboard Section
        mon_dash_card = QFrame()
        mon_dash_card.setObjectName("metricCard")
        mon_dash_layout = QVBoxLayout(mon_dash_card)
        mon_dash_layout.setContentsMargins(16, 14, 16, 14)
        mon_dash_layout.setSpacing(8)

        lbl_mon_dash_header = QLabel("Portfolio Health Monitoring Dashboard")
        lbl_mon_dash_header.setObjectName("sectionHeader")
        mon_dash_layout.addWidget(lbl_mon_dash_header)

        self.lbl_mon_dash_status = QLabel("Monitoring Status: UNAVAILABLE")
        self.lbl_mon_dash_status.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_dash_enabled = QLabel("Monitoring Enabled: NO")
        self.lbl_mon_dash_enabled.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_dash_latest_score = QLabel("Latest Score: 0")
        self.lbl_mon_dash_latest_score.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_dash_latest_grade = QLabel("Latest Grade: -")
        self.lbl_mon_dash_latest_grade.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_dash_latest_snapshot = QLabel("Latest Snapshot: N/A")
        self.lbl_mon_dash_latest_snapshot.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_dash_total_snapshots = QLabel("Total Snapshots: 0")
        self.lbl_mon_dash_total_snapshots.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_dash_timeline_entries = QLabel("Timeline Entries: 0")
        self.lbl_mon_dash_timeline_entries.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_dash_latest_change_count = QLabel("Latest Change Count: 0")
        self.lbl_mon_dash_latest_change_count.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_mon_dash_total_detected_changes = QLabel("Total Detected Changes: 0")
        self.lbl_mon_dash_total_detected_changes.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        mon_dash_layout.addWidget(self.lbl_mon_dash_status)
        mon_dash_layout.addWidget(self.lbl_mon_dash_enabled)
        mon_dash_layout.addWidget(self.lbl_mon_dash_latest_score)
        mon_dash_layout.addWidget(self.lbl_mon_dash_latest_grade)
        mon_dash_layout.addWidget(self.lbl_mon_dash_latest_snapshot)
        mon_dash_layout.addWidget(self.lbl_mon_dash_total_snapshots)
        mon_dash_layout.addWidget(self.lbl_mon_dash_timeline_entries)
        mon_dash_layout.addWidget(self.lbl_mon_dash_latest_change_count)
        mon_dash_layout.addWidget(self.lbl_mon_dash_total_detected_changes)

        root_layout.addWidget(mon_dash_card)

        # Alert Center Section
        ac_card = QFrame()
        ac_card.setObjectName("metricCard")
        ac_layout = QVBoxLayout(ac_card)
        ac_layout.setContentsMargins(16, 14, 16, 14)
        ac_layout.setSpacing(8)

        lbl_ac_header = QLabel("Alert Center")
        lbl_ac_header.setObjectName("sectionHeader")
        ac_layout.addWidget(lbl_ac_header)

        self.lbl_ac_total = QLabel("Total Alerts: 0")
        self.lbl_ac_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_ac_active = QLabel("Active: 0")
        self.lbl_ac_active.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_ac_acknowledged = QLabel("Acknowledged: 0")
        self.lbl_ac_acknowledged.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_ac_dismissed = QLabel("Dismissed: 0")
        self.lbl_ac_dismissed.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        ac_layout.addWidget(self.lbl_ac_total)
        ac_layout.addWidget(self.lbl_ac_active)
        ac_layout.addWidget(self.lbl_ac_acknowledged)
        ac_layout.addWidget(self.lbl_ac_dismissed)

        self.alerts_list_container = QVBoxLayout()
        ac_layout.addLayout(self.alerts_list_container)

        root_layout.addWidget(ac_card)

        # Generated Alerts Section
        gen_card = QFrame()
        gen_card.setObjectName("metricCard")
        gen_layout = QVBoxLayout(gen_card)
        gen_layout.setContentsMargins(16, 14, 16, 14)
        gen_layout.setSpacing(8)

        lbl_gen_header = QLabel("Generated Alerts")
        lbl_gen_header.setObjectName("sectionHeader")
        gen_layout.addWidget(lbl_gen_header)

        self.lbl_gen_alerts_count = QLabel("Generated Alerts: 0")
        self.lbl_gen_alerts_count.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        gen_layout.addWidget(self.lbl_gen_alerts_count)

        self.generated_alerts_container = QVBoxLayout()
        gen_layout.addLayout(self.generated_alerts_container)

        root_layout.addWidget(gen_card)

        # Alert Rules Section
        ar_card = QFrame()
        ar_card.setObjectName("metricCard")
        ar_layout = QVBoxLayout(ar_card)
        ar_layout.setContentsMargins(16, 14, 16, 14)
        ar_layout.setSpacing(8)

        lbl_ar_header = QLabel("Alert Rules")
        lbl_ar_header.setObjectName("sectionHeader")
        ar_layout.addWidget(lbl_ar_header)

        self.lbl_alert_rules_total = QLabel("Total Rules: 0")
        self.lbl_alert_rules_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_alert_rules_triggered = QLabel("Triggered Rules: 0")
        self.lbl_alert_rules_triggered.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        ar_layout.addWidget(self.lbl_alert_rules_total)
        ar_layout.addWidget(self.lbl_alert_rules_triggered)

        self.alert_rules_list_container = QVBoxLayout()
        ar_layout.addLayout(self.alert_rules_list_container)

        root_layout.addWidget(ar_card)

        # Alert Dashboard Section
        ad_card = QFrame()
        ad_card.setObjectName("metricCard")
        ad_layout = QVBoxLayout(ad_card)
        ad_layout.setContentsMargins(16, 14, 16, 14)
        ad_layout.setSpacing(8)

        lbl_ad_header = QLabel("Alert Dashboard")
        lbl_ad_header.setObjectName("sectionHeader")
        ad_layout.addWidget(lbl_ad_header)

        self.lbl_ad_total = QLabel("Total Alerts: 0")
        self.lbl_ad_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_ad_active = QLabel("Active: 0")
        self.lbl_ad_active.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_ad_acknowledged = QLabel("Acknowledged: 0")
        self.lbl_ad_acknowledged.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_ad_dismissed = QLabel("Dismissed: 0")
        self.lbl_ad_dismissed.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        self.lbl_ad_info = QLabel("INFO: 0")
        self.lbl_ad_info.setStyleSheet("font-size: 14px; color: #2563eb; font-weight: 600;")
        self.lbl_ad_low = QLabel("LOW: 0")
        self.lbl_ad_low.setStyleSheet("font-size: 14px; color: #16a34a; font-weight: 600;")
        self.lbl_ad_medium = QLabel("MEDIUM: 0")
        self.lbl_ad_medium.setStyleSheet("font-size: 14px; color: #d97706; font-weight: 600;")
        self.lbl_ad_high = QLabel("HIGH: 0")
        self.lbl_ad_high.setStyleSheet("font-size: 14px; color: #dc2626; font-weight: 600;")
        self.lbl_ad_critical = QLabel("CRITICAL: 0")
        self.lbl_ad_critical.setStyleSheet("font-size: 14px; color: #dc2626; font-weight: 600;")

        ad_layout.addWidget(self.lbl_ad_total)
        ad_layout.addWidget(self.lbl_ad_active)
        ad_layout.addWidget(self.lbl_ad_acknowledged)
        ad_layout.addWidget(self.lbl_ad_dismissed)
        ad_layout.addWidget(self.lbl_ad_info)
        ad_layout.addWidget(self.lbl_ad_low)
        ad_layout.addWidget(self.lbl_ad_medium)
        ad_layout.addWidget(self.lbl_ad_high)
        ad_layout.addWidget(self.lbl_ad_critical)

        self.alert_dashboard_list_container = QVBoxLayout()
        ad_layout.addLayout(self.alert_dashboard_list_container)

        root_layout.addWidget(ad_card)

        # Alert History Section
        ah_card = QFrame()
        ah_card.setObjectName("metricCard")
        ah_layout = QVBoxLayout(ah_card)
        ah_layout.setContentsMargins(16, 14, 16, 14)
        ah_layout.setSpacing(8)

        lbl_ah_header = QLabel("Alert History")
        lbl_ah_header.setObjectName("sectionHeader")
        ah_layout.addWidget(lbl_ah_header)

        self.lbl_ah_total = QLabel("Total Entries: 0")
        self.lbl_ah_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_ah_latest = QLabel("Latest: N/A")
        self.lbl_ah_latest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_ah_earliest = QLabel("Earliest: N/A")
        self.lbl_ah_earliest.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        ah_layout.addWidget(self.lbl_ah_total)
        ah_layout.addWidget(self.lbl_ah_latest)
        ah_layout.addWidget(self.lbl_ah_earliest)

        self.alert_history_list_container = QVBoxLayout()
        ah_layout.addLayout(self.alert_history_list_container)

        root_layout.addWidget(ah_card)

        # Alert Management Section
        am_card = QFrame()
        am_card.setObjectName("metricCard")
        am_layout = QVBoxLayout(am_card)
        am_layout.setContentsMargins(16, 14, 16, 14)
        am_layout.setSpacing(8)

        lbl_am_header = QLabel("Alert Management")
        lbl_am_header.setObjectName("sectionHeader")
        am_layout.addWidget(lbl_am_header)

        self.lbl_am_total = QLabel("Total Alerts: 0")
        self.lbl_am_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_am_active = QLabel("Active: 0")
        self.lbl_am_active.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_am_acknowledged = QLabel("Acknowledged: 0")
        self.lbl_am_acknowledged.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_am_dismissed = QLabel("Dismissed: 0")
        self.lbl_am_dismissed.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_am_last_updated = QLabel("Last Updated: N/A")
        self.lbl_am_last_updated.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        am_layout.addWidget(self.lbl_am_total)
        am_layout.addWidget(self.lbl_am_active)
        am_layout.addWidget(self.lbl_am_acknowledged)
        am_layout.addWidget(self.lbl_am_dismissed)
        am_layout.addWidget(self.lbl_am_last_updated)

        self.alert_management_list_container = QVBoxLayout()
        am_layout.addLayout(self.alert_management_list_container)

        root_layout.addWidget(am_card)

        # Decision Engine Section
        de_card = QFrame()
        de_card.setObjectName("metricCard")
        de_layout = QVBoxLayout(de_card)
        de_layout.setContentsMargins(16, 14, 16, 14)
        de_layout.setSpacing(8)

        lbl_de_header = QLabel("Decision Engine")
        lbl_de_header.setObjectName("sectionHeader")
        de_layout.addWidget(lbl_de_header)

        self.lbl_de_status = QLabel("Engine Status: READY")
        self.lbl_de_status.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_de_total = QLabel("Total Decisions: 0")
        self.lbl_de_total.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_de_pending = QLabel("Pending Decisions: 0")
        self.lbl_de_pending.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")
        self.lbl_de_informational = QLabel("Informational Decisions: 0")
        self.lbl_de_informational.setStyleSheet("font-size: 14px; color: #1f2937; font-weight: 600;")

        de_layout.addWidget(self.lbl_de_status)
        de_layout.addWidget(self.lbl_de_total)
        de_layout.addWidget(self.lbl_de_pending)
        de_layout.addWidget(self.lbl_de_informational)

        self.decision_engine_list_container = QVBoxLayout()
        de_layout.addLayout(self.decision_engine_list_container)

        root_layout.addWidget(de_card)

        root_layout.addStretch()

        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)

    def _create_metric_card(self, title: str, value: str):
        card = QFrame()
        card.setObjectName("metricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        t_lbl = QLabel(title.upper())
        t_lbl.setObjectName("cardTitle")

        val_lbl = QLabel(value)
        val_lbl.setObjectName("cardValue")

        layout.addWidget(t_lbl)
        layout.addWidget(val_lbl)
        return card, val_lbl
