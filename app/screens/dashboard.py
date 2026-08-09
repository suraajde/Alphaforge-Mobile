"""Dashboard Screen Foundation for AlphaForge (Sprint 14.0.0).

Provides executive summary metrics for Portfolio Health, Alpha 12 Stability, and Alert Surveillance.
"""

from typing import Any, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from core.version import APP_VERSION
from services.alert_center_service import AlertCenterService
from services.alpha12_stability_service import Alpha12StabilityService
from services.portfolio_health_service import PortfolioHealthService


class Dashboard(QWidget):
    """Executive Dashboard summary screen for AlphaForge."""

    def __init__(
        self,
        portfolio_health_service: Optional[PortfolioHealthService] = None,
        alpha12_stability_service: Optional[Alpha12StabilityService] = None,
        alert_center_service: Optional[AlertCenterService] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)

        self.portfolio_health_service = (
            portfolio_health_service
            if portfolio_health_service is not None
            else PortfolioHealthService()
        )
        self.alpha12_stability_service = (
            alpha12_stability_service
            if alpha12_stability_service is not None
            else Alpha12StabilityService()
        )
        self.alert_center_service = (
            alert_center_service if alert_center_service is not None else AlertCenterService()
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

        # Header Title
        header_card = QFrame()
        header_card.setObjectName("metricCard")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(16, 14, 16, 14)

        title_lbl = QLabel("EXECUTIVE DASHBOARD")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e3a8a;")

        welcome_lbl = QLabel(
            f"Welcome to AlphaForge — AI Portfolio Construction Engine (v{APP_VERSION} Stable)"
        )
        welcome_lbl.setStyleSheet("font-size: 14px; color: #475569; font-weight: 600;")

        safety_lbl = QLabel(
            "Governance Notice: AlphaForge provides transparent, analytical recommendations for human review. "
            "Zero automated trading, execution, or unauthorized broker actions are performed."
        )
        safety_lbl.setStyleSheet("font-size: 12px; color: #64748b; font-style: italic; margin-top: 4px;")

        header_layout.addWidget(title_lbl)
        header_layout.addWidget(welcome_lbl)
        header_layout.addWidget(safety_lbl)
        root_layout.addWidget(header_card)

        # Overview Metric Grid (Cards)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.card_health, self.lbl_health_val = self._create_card(
            "PORTFOLIO HEALTH", "N/A"
        )
        self.card_val, self.lbl_val_val = self._create_card(
            "PORTFOLIO VALUE", "N/A"
        )
        self.card_stab, self.lbl_stab_val = self._create_card(
            "ALPHA 12 STABILITY", "N/A"
        )
        self.card_alerts, self.lbl_alerts_val = self._create_card(
            "ACTIVE ALERTS", "N/A"
        )

        cards_layout.addWidget(self.card_health)
        cards_layout.addWidget(self.card_val)
        cards_layout.addWidget(self.card_stab)
        cards_layout.addWidget(self.card_alerts)
        root_layout.addLayout(cards_layout)

        # Executive Summary Details Section
        detail_card = QFrame()
        detail_card.setObjectName("metricCard")
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(16, 14, 16, 14)
        detail_layout.setSpacing(8)

        lbl_detail_title = QLabel("SYSTEM EXECUTIVE SUMMARY")
        lbl_detail_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e293b;")
        detail_layout.addWidget(lbl_detail_title)

        self.detail_container = QVBoxLayout()
        detail_layout.addLayout(self.detail_container)
        root_layout.addWidget(detail_card)

        root_layout.addStretch()
        scroll.setWidget(content_widget)
        outer_layout.addWidget(scroll)

    def _create_card(self, title: str, value: str) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("metricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        t_lbl = QLabel(title.upper())
        t_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b;")

        v_lbl = QLabel(value)
        v_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a;")

        layout.addWidget(t_lbl)
        layout.addWidget(v_lbl)
        return card, v_lbl

    def refresh_data(self) -> None:
        """Fetch real data safely from underlying services and update UI."""
        self._load_health_summary()
        self._load_stability_summary()
        self._load_alerts_summary()
        self._render_executive_summary()

    def _load_health_summary(self) -> None:
        try:
            res = self.portfolio_health_service.evaluate()
            score = getattr(res, "score", 0)
            grade = getattr(res, "grade", "D")
            self.lbl_health_val.setText(f"{score}/100 ({grade})")

            snapshot = self.portfolio_health_service.build_snapshot()
            val = getattr(snapshot, "portfolio_value", 0.0)
            if val > 0:
                self.lbl_val_val.setText(f"${val:,.2f}")
            else:
                self.lbl_val_val.setText("Unavailable")
        except Exception:
            self.lbl_health_val.setText("Unavailable")
            self.lbl_val_val.setText("Unavailable")

    def _load_stability_summary(self) -> None:
        try:
            res = self.alpha12_stability_service.get_stability()
            metrics = getattr(res, "stability_metrics", None)
            if metrics is not None and getattr(metrics, "assessment_status", "UNAVAILABLE") != "UNAVAILABLE":
                score = getattr(metrics, "stability_score", 0.0)
                rating = getattr(metrics, "stability_rating", "MODERATE")
                self.lbl_stab_val.setText(f"{score:.1f} ({rating})")
            else:
                self.lbl_stab_val.setText("Unavailable")
        except Exception:
            self.lbl_stab_val.setText("Unavailable")

    def _load_alerts_summary(self) -> None:
        try:
            state = self.alert_center_service.get_state()
            active = getattr(state, "active_alerts", 0)
            self.lbl_alerts_val.setText(str(active))
        except Exception:
            self.lbl_alerts_val.setText("0")

    def _render_executive_summary(self) -> None:
        self._clear_layout(self.detail_container)
        try:
            snapshot = self.portfolio_health_service.build_snapshot()
            pos_cnt = getattr(snapshot, "position_count", 0)
            cash_pct = getattr(snapshot, "cash_allocation_pct", 0.0)
            largest_pos = getattr(snapshot, "largest_position", "N/A")

            res = self.portfolio_health_service.evaluate(snapshot)
            div_rating = getattr(res, "diversification_rating", "POOR")
            conc_rating = getattr(res, "concentration_rating", "HIGH")

            summary_str = (
                f"• Active Positions: {pos_cnt} | Cash Allocation: {cash_pct:.1f}% | Largest Position: {largest_pos}\n"
                f"• Diversification Rating: {div_rating} | Concentration Risk: {conc_rating}\n"
                f"• System Status: Operational (v{APP_VERSION} Stable)"
            )
            lbl = QLabel(summary_str)
            lbl.setStyleSheet("font-size: 13px; color: #334155; line-height: 1.5;")
            self.detail_container.addWidget(lbl)
        except Exception:
            err_lbl = QLabel("Executive summary metrics currently unavailable.")
            err_lbl.setStyleSheet("font-size: 13px; color: #64748b; font-style: italic;")
            self.detail_container.addWidget(err_lbl)

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count() > 0:
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()