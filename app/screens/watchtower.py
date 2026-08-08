"""Watchtower Screen Foundation for AlphaForge (Sprint 14.0.0).

Provides real-time, read-only portfolio monitoring, alert center status, and system health feeds.
"""

from typing import Any, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.alert_center_service import AlertCenterService
from services.alpha12_stability_service import Alpha12StabilityService
from services.portfolio_health_monitor_dashboard_service import PortfolioHealthMonitoringDashboardService


class Watchtower(QWidget):
    """Read-only Watchtower monitoring screen foundation."""

    def __init__(
        self,
        monitoring_dashboard_service: Optional[PortfolioHealthMonitoringDashboardService] = None,
        alert_center_service: Optional[AlertCenterService] = None,
        stability_service: Optional[Alpha12StabilityService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.monitoring_dashboard_service = (
            monitoring_dashboard_service
            if monitoring_dashboard_service is not None
            else PortfolioHealthMonitoringDashboardService()
        )
        self.alert_center_service = (
            alert_center_service if alert_center_service is not None else AlertCenterService()
        )
        self.stability_service = (
            stability_service if stability_service is not None else Alpha12StabilityService()
        )

        self._build_ui()
        self.refresh_data()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(16, 16, 16, 16)
        outer_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        root_layout = QVBoxLayout(content_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(16)

        # Title & Subtitle Header
        header_card = QFrame()
        header_card.setObjectName("metricCard")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(16, 14, 16, 14)

        title_lbl = QLabel("WATCHTOWER PORTFOLIO MONITORING")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e3a8a;")

        subtitle_lbl = QLabel(
            "Read-only portfolio surveillance, alert feeds, and long-term stability watch."
        )
        subtitle_lbl.setStyleSheet("font-size: 13px; color: #64748b;")

        notice_lbl = QLabel(
            "Notice: Watchtower is an analytical surveillance interface. "
            "It does not execute automated trades, rebalancing actions, or broker transactions."
        )
        notice_lbl.setStyleSheet("font-size: 12px; color: #475569; font-style: italic; margin-top: 4px;")

        header_layout.addWidget(title_lbl)
        header_layout.addWidget(subtitle_lbl)
        header_layout.addWidget(notice_lbl)
        root_layout.addWidget(header_card)

        # Section 1: Portfolio Health Monitoring State
        mon_card = QFrame()
        mon_card.setObjectName("metricCard")
        mon_layout = QVBoxLayout(mon_card)
        mon_layout.setContentsMargins(16, 14, 16, 14)
        mon_layout.setSpacing(8)

        lbl_mon_title = QLabel("PORTFOLIO HEALTH SURVEILLANCE")
        lbl_mon_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")
        mon_layout.addWidget(lbl_mon_title)

        self.mon_container = QVBoxLayout()
        mon_layout.addLayout(self.mon_container)
        root_layout.addWidget(mon_card)

        # Section 2: Alert Center Feed Summary
        alert_card = QFrame()
        alert_card.setObjectName("metricCard")
        alert_layout = QVBoxLayout(alert_card)
        alert_layout.setContentsMargins(16, 14, 16, 14)
        alert_layout.setSpacing(8)

        lbl_alert_title = QLabel("ALERT CENTER SURVEILLANCE FEED")
        lbl_alert_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")
        alert_layout.addWidget(lbl_alert_title)

        self.alert_container = QVBoxLayout()
        alert_layout.addLayout(self.alert_container)
        root_layout.addWidget(alert_card)

        # Section 3: Alpha 12 Stability Watch
        stab_card = QFrame()
        stab_card.setObjectName("metricCard")
        stab_layout = QVBoxLayout(stab_card)
        stab_layout.setContentsMargins(16, 14, 16, 14)
        stab_layout.setSpacing(8)

        lbl_stab_title = QLabel("ALPHA 12 LONG-TERM STABILITY WATCH")
        lbl_stab_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")
        stab_layout.addWidget(lbl_stab_title)

        self.stab_container = QVBoxLayout()
        stab_layout.addLayout(self.stab_container)
        root_layout.addWidget(stab_card)

        root_layout.addStretch()
        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)

    def refresh_data(self) -> None:
        """Bind live surveillance and monitoring metrics safely to UI."""
        self._load_monitoring_surveillance()
        self._load_alert_surveillance()
        self._load_stability_surveillance()

    def _load_monitoring_surveillance(self) -> None:
        self._clear_layout(self.mon_container)
        try:
            dash = self.monitoring_dashboard_service.build_dashboard()
            status = getattr(dash, "monitoring_status", "UNAVAILABLE")
            score = getattr(dash, "latest_score", 0)
            grade = getattr(dash, "latest_grade", "N/A")
            snapshots = getattr(dash, "total_snapshots", 0)
            changes = getattr(dash, "total_detected_changes", 0)
            latest_time = getattr(dash, "latest_snapshot_time", None) or "N/A"

            info_str = (
                f"Surveillance Status: {status} | Total Snapshots Tracked: {snapshots}\n"
                f"Latest Portfolio Health Score: {score} (Grade {grade}) | Total Changes Detected: {changes}\n"
                f"Latest Snapshot Time: {latest_time}"
            )
            lbl = QLabel(info_str)
            lbl.setStyleSheet("font-size: 13px; color: #1e293b; font-weight: 600;")
            self.mon_container.addWidget(lbl)
        except Exception:
            err_lbl = QLabel("Portfolio health surveillance state unavailable.")
            err_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")
            self.mon_container.addWidget(err_lbl)

    def _load_alert_surveillance(self) -> None:
        self._clear_layout(self.alert_container)
        try:
            state = self.alert_center_service.get_state()
            total = getattr(state, "total_alerts", 0)
            active = getattr(state, "active_alerts", 0)
            ack = getattr(state, "acknowledged_alerts", 0)
            dismissed = getattr(state, "dismissed_alerts", 0)

            info_str = (
                f"Total Alerts Recorded: {total} | Active Alerts: {active}\n"
                f"Acknowledged Alerts: {ack} | Dismissed Alerts: {dismissed}"
            )
            lbl = QLabel(info_str)
            lbl.setStyleSheet("font-size: 13px; color: #1e293b; font-weight: 600;")
            self.alert_container.addWidget(lbl)
        except Exception:
            err_lbl = QLabel("Alert center surveillance feed unavailable.")
            err_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")
            self.alert_container.addWidget(err_lbl)

    def _load_stability_surveillance(self) -> None:
        self._clear_layout(self.stab_container)
        try:
            res = self.stability_service.get_stability()
            status = getattr(res, "analysis_status", "UNAVAILABLE")
            metrics = getattr(res, "stability_metrics", None)
            if metrics is not None and getattr(metrics, "assessment_status", "UNAVAILABLE") != "UNAVAILABLE":
                score = getattr(metrics, "stability_score", 0.0)
                rating = getattr(metrics, "stability_rating", "MODERATE")
                risk = getattr(metrics, "churn_risk", "LOW")
                turnover = getattr(metrics, "turnover_rate", 0.0)
                swaps_prev = getattr(metrics, "unnecessary_swap_prevention", 0)

                info_str = (
                    f"Stability Rating: {rating} (Score {score:.1f}/100) | Analysis Status: {status}\n"
                    f"Churn Risk: {risk} | Turnover Rate: {turnover:.1f}% | Unnecessary Swaps Blocked: {swaps_prev}"
                )
                lbl = QLabel(info_str)
                lbl.setStyleSheet("font-size: 13px; color: #1e293b; font-weight: 600;")
                self.stab_container.addWidget(lbl)
            else:
                lbl = QLabel("Alpha 12 stability watch data unavailable.")
                lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")
                self.stab_container.addWidget(lbl)
        except Exception:
            err_lbl = QLabel("Alpha 12 stability watch data unavailable.")
            err_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")
            self.stab_container.addWidget(err_lbl)

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count() > 0:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
