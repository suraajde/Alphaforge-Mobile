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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.service = ActionCenterService()
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

        # Initial Sample Presentation
        self.load_mock_data()

    def load_mock_data(self) -> None:
        """Load sample RebalancePlan data matching Sprint 12.9.1 mock requirements."""
        from services.rebalance_decision_service import RebalanceDecision
        from services.rebalance_orchestrator_service import RebalancePlan

        sample_plan = RebalancePlan(
            approved_actions=[],
            deferred_actions=[
                RebalanceDecision(
                    action="REVIEW",
                    symbol="HDFCBANK",
                    candidate_symbol="ICICIBANK",
                    priority="MEDIUM",
                    confidence=74.0,
                    rationale=["Cooling period active (15/30 days held)"],
                )
            ],
            turnover_pct=0.0,
            replacement_count=0,
            add_count=0,
            rationale=["Monthly review completed. No approved replacements required; 1 position flagged for manual review."],
        )
        self.load_plan(sample_plan)

    def load_plan(
        self,
        plan: Optional[RebalancePlan] = None,
        observations: Optional[list] = None,
        review_date: Optional[str] = None,
    ) -> None:
        """Populate the Action Center UI widgets using ActionCenterService view model."""
        from services.portfolio_state_service import PortfolioStateService
        from config.path_config import get_data_path

        state_path = get_data_path("portfolio/portfolio_state.json")
        state_res = PortfolioStateService().load_state(path=state_path)
        state = state_res.get("state", {}) if isinstance(state_res, dict) else {}
        positions = state.get("positions", {}) if isinstance(state, dict) else {}

        date_str = review_date or datetime.now().strftime("%Y-%m-%d")

        if not positions:
            self.lbl_review_date_val.setText(date_str)
            self.lbl_status_val.setText("NO ACTIVE PORTFOLIO DATA")
            self.lbl_status_val.setStyleSheet("color: #94a3b8; font-weight: 700; font-size: 16px;")
            self.lbl_approved_count_val.setText("0")
            self.lbl_deferred_count_val.setText("0")
            self.lbl_turnover_val.setText("0.0%")
            self.approved_table.setRowCount(0)
            self.deferred_table.setRowCount(0)
            self.rationale_list.clear()
            self.rationale_list.addItem(
                QListWidgetItem("• No active portfolio data — Create or import a portfolio to evaluate portfolio actions.")
            )
            return

        vm: ActionCenterViewModel = self.service.build_view_model(plan, observations=observations, review_date=review_date)

        # 1. Render Summary
        self.lbl_review_date_val.setText(vm.summary.review_date)
        self.lbl_status_val.setText(vm.summary.portfolio_status)

        status_color = "#16a34a" if vm.summary.portfolio_status == "REBALANCE APPROVED" else "#64748b"
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
