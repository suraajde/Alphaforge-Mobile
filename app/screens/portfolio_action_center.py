"""Portfolio Action Center Screen (Sprint 12.9.0 Portfolio Action Center Foundation)

Presents governance review summaries, approved actions, deferred actions, rebalance rationale,
and governance policy snapshots in a modern PySide6 interface.
"""
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from services.action_center_service import (
    ActionCenterService,
    ActionCenterViewModel,
)
from services.rebalance_orchestrator_service import RebalancePlan


class PortfolioActionCenter(QWidget):
    """User-facing review center for AlphaForge governance decisions and rebalance plans."""

    def __init__(
        self,
        action_center_service: Optional[ActionCenterService] = None,
        alpha12_provider: Optional[Any] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.alpha12_provider = alpha12_provider
        self.service = (
            action_center_service
            if action_center_service is not None
            else ActionCenterService(alpha12_provider=alpha12_provider)
        )
        self._build_ui()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(24, 20, 24, 20)
        root_layout.setSpacing(16)

        # Scroll Area for clean presentation across resolutions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")

        container = QWidget()
        self.container_layout = QVBoxLayout(container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(20)

        # Header Title
        header_title = QLabel("Portfolio Action Center")
        header_title.setStyleSheet("font-size: 24px; font-weight: 700; color: #1e3a8a;")
        self.container_layout.addWidget(header_title)

        header_subtitle = QLabel("Track, review and approve portfolio governance decisions")
        header_subtitle.setStyleSheet("font-size: 12px; font-weight: 500; color: #64748b;")
        self.container_layout.addWidget(header_subtitle)

        # --------------------------------------------------
        # 1. MONTHLY REVIEW SUMMARY
        # --------------------------------------------------
        self.summary_frame = QFrame()
        self.summary_frame.setObjectName("metricCard")
        summary_layout = QVBoxLayout(self.summary_frame)
        summary_layout.setContentsMargins(16, 14, 16, 14)
        summary_layout.setSpacing(10)

        summary_title = QLabel("Monthly Review Summary")
        summary_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1e3a8a;")
        summary_layout.addWidget(summary_title)

        summary_grid = QGridLayout()
        summary_grid.setSpacing(12)

        self.lbl_review_date_val = self._create_card_value(summary_grid, "REVIEW DATE", 0, 0)
        self.lbl_status_val = self._create_card_value(summary_grid, "PORTFOLIO STATUS", 0, 1)
        self.lbl_approved_count_val = self._create_card_value(summary_grid, "APPROVED ACTIONS", 0, 2)
        self.lbl_deferred_count_val = self._create_card_value(summary_grid, "DEFERRED ACTIONS", 1, 0)
        self.lbl_turnover_val = self._create_card_value(summary_grid, "ESTIMATED TURNOVER", 1, 1)

        summary_layout.addLayout(summary_grid)
        self.container_layout.addWidget(self.summary_frame)

        # --------------------------------------------------
        # 2. APPROVED ACTIONS TABLE
        # --------------------------------------------------
        approved_box = QFrame()
        approved_box.setObjectName("metricCard")
        approved_layout = QVBoxLayout(approved_box)
        approved_layout.setContentsMargins(16, 14, 16, 14)

        approved_title = QLabel("Approved Actions")
        approved_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #16a34a;")
        approved_layout.addWidget(approved_title)

        self.approved_table = QTableWidget(0, 5)
        self.approved_table.setHorizontalHeaderLabels([
            "Action", "Current Holding", "Candidate Holding", "Priority", "Confidence"
        ])
        self._style_table(self.approved_table)
        approved_layout.addWidget(self.approved_table)
        self.container_layout.addWidget(approved_box)

        # --------------------------------------------------
        # 3. DEFERRED ACTIONS TABLE
        # --------------------------------------------------
        deferred_box = QFrame()
        deferred_box.setObjectName("metricCard")
        deferred_layout = QVBoxLayout(deferred_box)
        deferred_layout.setContentsMargins(16, 14, 16, 14)

        deferred_title = QLabel("Deferred Actions")
        deferred_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #eab308;")
        deferred_layout.addWidget(deferred_title)

        self.deferred_table = QTableWidget(0, 5)
        self.deferred_table.setHorizontalHeaderLabels([
            "Action", "Current Holding", "Candidate Holding", "Reason", "Confidence"
        ])
        self._style_table(self.deferred_table)
        deferred_layout.addWidget(self.deferred_table)
        self.container_layout.addWidget(deferred_box)

        # --------------------------------------------------
        # 3b. ACTIVE HOLDINGS & EMERGENCY GOVERNANCE
        # --------------------------------------------------
        holdings_gov_box = QFrame()
        holdings_gov_box.setObjectName("metricCard")
        holdings_gov_layout = QVBoxLayout(holdings_gov_box)
        holdings_gov_layout.setContentsMargins(16, 14, 16, 14)

        holdings_gov_title = QLabel("Active Holdings & Emergency Governance")
        holdings_gov_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f87171;")
        holdings_gov_layout.addWidget(holdings_gov_title)

        self.holdings_gov_table = QTableWidget(0, 7)
        self.holdings_gov_table.setHorizontalHeaderLabels([
            "Symbol", "Company / Sector", "Weight", "Target", "Drift", "Status", "Emergency Swap"
        ])
        self._style_table(self.holdings_gov_table)
        self.holdings_gov_table.setMinimumHeight(180)
        self.holdings_gov_table.setMaximumHeight(260)
        holdings_gov_layout.addWidget(self.holdings_gov_table)
        self.container_layout.addWidget(holdings_gov_box)

        # --------------------------------------------------
        # 4. REBALANCE RATIONALE
        # --------------------------------------------------
        rationale_box = QFrame()
        rationale_box.setObjectName("metricCard")
        rationale_layout = QVBoxLayout(rationale_box)
        rationale_layout.setContentsMargins(16, 14, 16, 14)

        rationale_title = QLabel("Rebalance Rationale")
        rationale_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1e3a8a;")
        rationale_layout.addWidget(rationale_title)

        self.rationale_list = QListWidget()
        self.rationale_list.setMaximumHeight(120)
        self.rationale_list.setStyleSheet(
            "QListWidget { background-color: #0f172a; border: 1px solid #334155; border-radius: 6px; color: #cbd5e1; padding: 8px; font-size: 13px; }"
        )
        rationale_layout.addWidget(self.rationale_list)
        self.container_layout.addWidget(rationale_box)

        # --------------------------------------------------
        # 5. GOVERNANCE SNAPSHOT
        # --------------------------------------------------
        gov_box = QFrame()
        gov_box.setObjectName("metricCard")
        gov_layout = QVBoxLayout(gov_box)
        gov_layout.setContentsMargins(16, 12, 16, 12)
        gov_layout.setSpacing(8)

        gov_title = QLabel("Governance Snapshot")
        gov_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        gov_layout.addWidget(gov_title)

        gov_form = QFormLayout()
        gov_form.setSpacing(8)
        gov_form.setLabelAlignment(Qt.AlignLeft)

        self.lbl_gov_freq = self._create_form_value("Monthly Review")
        self.lbl_gov_mode = self._create_form_value("Conditional Rebalance")
        self.lbl_gov_max = self._create_form_value("Max Replacements: 3")
        self.lbl_gov_budget = self._create_form_value("Turnover Budget: 20%")
        self.lbl_gov_emergency = self._create_form_value("Emergency Override: Enabled")

        gov_form.addRow(self._create_form_label("Review Frequency"), self.lbl_gov_freq)
        gov_form.addRow(self._create_form_label("Rebalance Mode"), self.lbl_gov_mode)
        gov_form.addRow(self._create_form_label("Max Replacements"), self.lbl_gov_max)
        gov_form.addRow(self._create_form_label("Turnover Budget"), self.lbl_gov_budget)
        gov_form.addRow(self._create_form_label("Emergency Override"), self.lbl_gov_emergency)

        gov_layout.addLayout(gov_form)
        self.container_layout.addWidget(gov_box)

        scroll.setWidget(container)
        root_layout.addWidget(scroll)

        # Initial Presentation
        self.load_plan(None)

    def load_mock_data(self) -> None:
        """Clear mock data and load current active portfolio plan."""
        self.load_plan(None)

    def load_plan(
        self,
        plan: Optional[RebalancePlan] = None,
        observations: Optional[list] = None,
        review_date: Optional[str] = None,
    ) -> None:
        """Populate the Action Center UI widgets using ActionCenterService view model."""
        from services.portfolio_application_service import PortfolioApplicationService
        from services.portfolio_state_service import PortfolioStateService
        from config.path_config import get_data_path
        from app.theme import UIColors, get_status_color

        self.approved_table.clearContents()
        self.approved_table.setRowCount(0)
        self.deferred_table.clearContents()
        self.deferred_table.setRowCount(0)
        self.holdings_gov_table.clearContents()
        self.holdings_gov_table.setRowCount(0)
        self.rationale_list.clear()

        app_service = PortfolioApplicationService()
        status_resp = app_service.get_status()
        state = status_resp.get("state", {}) if isinstance(status_resp, dict) else {}
        if not state:
            state_path = get_data_path("portfolio/portfolio_state.json")
            state_res = PortfolioStateService().load_state(path=state_path)
            state = state_res.get("state", {}) if isinstance(state_res, dict) else {}
        positions = state.get("positions", {}) if isinstance(state, dict) else {}

        date_str = review_date or datetime.now().strftime("%Y-%m-%d")

        if not positions and plan is None and observations is None:
            self.lbl_review_date_val.setText(date_str)
            self.lbl_status_val.setText("NO ACTIVE PORTFOLIO DATA")
            self.lbl_status_val.setStyleSheet(f"color: {UIColors.GREY}; font-weight: 700; font-size: 16px;")
            self.lbl_approved_count_val.setText("0")
            self.lbl_deferred_count_val.setText("0")
            self.lbl_turnover_val.setText("0.0%")
            self.rationale_list.addItem(
                QListWidgetItem("• No active portfolio data — Create or import a portfolio to evaluate portfolio actions.")
            )
            return

        if plan is None and observations is None:
            vm: ActionCenterViewModel = self.service.evaluate_active_portfolio(portfolio_state=state, review_date=review_date)
        else:
            vm: ActionCenterViewModel = self.service.build_view_model(plan, observations=observations, review_date=review_date)

        # 1. Render Summary
        self.lbl_review_date_val.setText(vm.summary.review_date)
        self.lbl_status_val.setText(vm.summary.portfolio_status)

        status_color = get_status_color(vm.summary.portfolio_status)
        self.lbl_status_val.setStyleSheet(f"color: {status_color}; font-weight: 700; font-size: 16px;")

        self.lbl_approved_count_val.setText(str(vm.summary.approved_action_count))
        self.lbl_deferred_count_val.setText(str(vm.summary.deferred_action_count))
        self.lbl_turnover_val.setText(f"{vm.summary.estimated_turnover:.1f}%")

        # 2. Render Approved Actions Table
        self.approved_table.setRowCount(0)
        for i, a in enumerate(vm.approved_actions):
            self.approved_table.insertRow(i)
            self.approved_table.setItem(i, 0, QTableWidgetItem(a.action))
            self.approved_table.setItem(i, 1, QTableWidgetItem(a.current_holding))
            self.approved_table.setItem(i, 2, QTableWidgetItem(a.candidate_holding))
            self.approved_table.setItem(i, 3, QTableWidgetItem(a.priority))
            self.approved_table.setItem(i, 4, QTableWidgetItem(f"{a.confidence:.1f}%"))

        # 3. Render Deferred Actions Table
        self.deferred_table.setRowCount(0)
        for i, d in enumerate(vm.deferred_actions):
            self.deferred_table.insertRow(i)
            self.deferred_table.setItem(i, 0, QTableWidgetItem(d.action))
            self.deferred_table.setItem(i, 1, QTableWidgetItem(d.current_holding))
            self.deferred_table.setItem(i, 2, QTableWidgetItem(d.candidate_holding))
            self.deferred_table.setItem(i, 3, QTableWidgetItem(d.reason))
            self.deferred_table.setItem(i, 4, QTableWidgetItem(f"{d.confidence:.1f}%"))

        # 3b. Render Active Holdings & Emergency Governance Table
        self.holdings_gov_table.setRowCount(0)
        pos_items = list(positions.values()) if isinstance(positions, dict) else []
        for i, pos in enumerate(pos_items):
            if not isinstance(pos, dict):
                continue
            sym = str(pos.get("symbol", "")).strip().upper()
            comp_name = pos.get("company_name", sym) or sym
            sector = pos.get("sector", "UNKNOWN") or "UNKNOWN"
            comp_label = f"{comp_name} ({sector})"
            act_wt = float(pos.get("actual_weight", 0.0) or 0.0)
            tgt_wt = float(pos.get("target_weight", 0.0) or 0.0)
            drift = float(pos.get("drift_pct", 0.0) or 0.0)
            status_str = str(pos.get("allocation_state", "ACTIVE") or "ACTIVE")

            self.holdings_gov_table.insertRow(i)
            self.holdings_gov_table.setItem(i, 0, QTableWidgetItem(sym))
            self.holdings_gov_table.setItem(i, 1, QTableWidgetItem(comp_label))
            self.holdings_gov_table.setItem(i, 2, QTableWidgetItem(f"{act_wt:.2f}%"))
            self.holdings_gov_table.setItem(i, 3, QTableWidgetItem(f"{tgt_wt:.2f}%"))
            self.holdings_gov_table.setItem(i, 4, QTableWidgetItem(f"{drift:+.2f}%"))
            self.holdings_gov_table.setItem(i, 5, QTableWidgetItem(status_str))

            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setAlignment(Qt.AlignCenter)

            eject_btn = QPushButton("🚨 Emergency Swap")
            eject_btn.setStyleSheet(
                "QPushButton { background-color: #ef4444; color: white; font-weight: bold; font-size: 11px; padding: 4px 10px; border-radius: 4px; }"
                "QPushButton:hover { background-color: #dc2626; }"
            )
            eject_btn.clicked.connect(lambda _, s=sym: self.confirm_and_emergency_eject(s))
            action_layout.addWidget(eject_btn)
            self.holdings_gov_table.setCellWidget(i, 6, action_widget)

        # 4. Render Rationale
        self.rationale_list.clear()
        for r in vm.rationale:
            item = QListWidgetItem(f"• {r}")
            self.rationale_list.addItem(item)

        # 5. Governance Snapshot
        self.lbl_gov_freq.setText(vm.governance_snapshot.review_frequency)
        self.lbl_gov_mode.setText(vm.governance_snapshot.rebalance_mode)
        self.lbl_gov_max.setText(vm.governance_snapshot.max_replacements)
        self.lbl_gov_budget.setText(vm.governance_snapshot.turnover_budget)
        self.lbl_gov_emergency.setText(vm.governance_snapshot.emergency_override)

    def confirm_and_emergency_eject(self, symbol: str) -> None:
        symbol = str(symbol).strip().upper()
        if not symbol:
            return

        reply = QMessageBox.warning(
            self,
            "Confirm Emergency Eject",
            f"Are you sure you want to emergency eject '{symbol}' from your active portfolio?\n\n"
            f"• '{symbol}' will be permanently deleted from active holdings.\n"
            f"• The #1 highest-ranked candidate from the Reserve 8 bench will be automatically promoted into your portfolio with 0 quantity.\n"
            f"• Your Smart SIP engine will automatically route the next capital allocation into this new holding.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        from services.portfolio_application_service import PortfolioApplicationService
        app_service = PortfolioApplicationService()
        result = app_service.emergency_replace_position(symbol)

        if isinstance(result, dict) and result.get("status") == "OK":
            replacement = result.get("replacement_symbol", "Reserve 8 candidate")

            # Explicitly reset all table views to prevent stale UI state
            self.holdings_gov_table.clearContents()
            self.holdings_gov_table.setRowCount(0)
            self.approved_table.clearContents()
            self.approved_table.setRowCount(0)
            self.deferred_table.clearContents()
            self.deferred_table.setRowCount(0)
            self.load_plan(None)

            QMessageBox.information(
                self,
                "Emergency Swap Successful",
                f"Successfully ejected '{symbol}'.\n\n"
                f"Promoted '{replacement}' from the Reserve 8 bench into your active portfolio.\n\n"
                f"Action Center has been refreshed.",
            )
        else:
            err_msg = (
                result.get("error", "Unknown error during emergency replace.")
                if isinstance(result, dict)
                else "Unknown error."
            )
            QMessageBox.critical(
                self,
                "Emergency Eject Failed",
                f"Failed to eject '{symbol}':\n\n{err_msg}",
            )

    # ======================================================
    # PRIVATE UI HELPERS
    # ======================================================

    def _create_card_value(self, grid: QGridLayout, title: str, row: int, col: int) -> QLabel:
        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: #0f172a; border-radius: 6px; padding: 8px; }")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 6, 8, 6)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 700;")
        val_lbl = QLabel("-")
        val_lbl.setStyleSheet("color: #f8fafc; font-size: 16px; font-weight: 700;")

        layout.addWidget(t_lbl)
        layout.addWidget(val_lbl)
        grid.addWidget(frame, row, col)
        return val_lbl

    def _create_form_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500;")
        return lbl

    def _create_form_value(self, text: str = "-") -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #38bdf8; font-size: 13px; font-weight: 700;")
        return lbl

    def _style_table(self, table: QTableWidget) -> None:
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setMinimumHeight(140)
        table.setMaximumHeight(180)
        table.setStyleSheet(
            "QTableWidget { background-color: #0f172a; border: 1px solid #334155; gridline-color: #1e293b; color: #f8fafc; font-size: 12px; }"
            "QHeaderView::section { background-color: #1e293b; color: #94a3b8; font-weight: 700; font-size: 12px; border: none; padding: 6px; }"
        )
