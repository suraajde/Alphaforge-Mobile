import pytest
from PySide6.QtWidgets import QApplication

from app.screens.portfolio_action_center import PortfolioActionCenter
from services.action_center_service import (
    ActionCenterService,
    ActionCenterViewModel,
    ApprovedActionViewModel,
    DeferredActionViewModel,
    GovernanceSnapshotViewModel,
    ReviewSummaryViewModel,
)
from services.rebalance_decision_service import (
    RebalanceAction,
    RebalanceDecision,
    RebalancePriority,
)
from services.rebalance_orchestrator_service import RebalancePlan


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_summary_generation():
    service = ActionCenterService()

    # Case A: Explicit empty state
    vm_empty = service.build_view_model(None, observations=[], review_date="2026-08-01")
    assert isinstance(vm_empty.summary, ReviewSummaryViewModel)
    assert vm_empty.summary.review_date == "2026-08-01"
    assert vm_empty.summary.portfolio_status == "NO ACTION REQUIRED"
    assert vm_empty.summary.approved_action_count == 0
    assert vm_empty.summary.deferred_action_count == 0
    assert vm_empty.summary.estimated_turnover == 0.0

    # Case B: Approved Plan + Governance Pipeline Sample Observation
    plan = RebalancePlan(
        approved_actions=[
            RebalanceDecision(action="REPLACE", symbol="INFY", candidate_symbol="TCS", priority="HIGH", confidence=92.0)
        ],
        deferred_actions=[
            RebalanceDecision(action="REVIEW", symbol="HDFCBANK", candidate_symbol="ICICIBANK", priority="MEDIUM", confidence=74.0, rationale=["Cooling period active"])
        ],
        turnover_pct=8.33,
        replacement_count=1,
        add_count=0,
        rationale=["Approved REPLACE for INFY -> TCS"],
    )

    vm_active = service.build_view_model(plan, review_date="2026-08-02")
    assert vm_active.summary.review_date == "2026-08-02"
    assert vm_active.summary.portfolio_status == "REBALANCE APPROVED"
    assert vm_active.summary.approved_action_count == 1
    assert vm_active.summary.deferred_action_count == 2  # 1 governance alert + 1 plan deferred item
    assert vm_active.summary.estimated_turnover == 8.33


def test_approved_actions_mapping():
    service = ActionCenterService()
    plan = RebalancePlan(
        approved_actions=[
            RebalanceDecision(action="ADD", symbol="CDSL", candidate_symbol=None, priority="HIGH", confidence=96.0),
            RebalanceDecision(action="REPLACE", symbol="INFY", candidate_symbol="TCS", priority="HIGH", confidence=92.0),
        ],
    )

    vm = service.build_view_model(plan, observations=[])
    assert len(vm.approved_actions) == 2

    add_vm = vm.approved_actions[0]
    assert isinstance(add_vm, ApprovedActionViewModel)
    assert add_vm.action == "ADD"
    assert add_vm.current_holding == "CDSL"
    assert add_vm.candidate_holding == "-"
    assert add_vm.priority == "HIGH"
    assert add_vm.confidence == 96.0

    rep_vm = vm.approved_actions[1]
    assert rep_vm.action == "REPLACE"
    assert rep_vm.current_holding == "INFY"
    assert rep_vm.candidate_holding == "TCS"
    assert rep_vm.confidence == 92.0


def test_deferred_actions_mapping():
    service = ActionCenterService()
    plan = RebalancePlan(
        deferred_actions=[
            RebalanceDecision(
                action="REVIEW", symbol="HDFCBANK", candidate_symbol="ICICIBANK",
                priority="MEDIUM", confidence=74.0, rationale=["Manual review required", "Cooling period active"]
            ),
        ],
    )

    vm = service.build_view_model(plan, observations=[])
    assert len(vm.deferred_actions) == 1

    def_vm = vm.deferred_actions[0]
    assert isinstance(def_vm, DeferredActionViewModel)
    assert def_vm.action == "REVIEW"
    assert def_vm.current_holding == "HDFCBANK"
    assert def_vm.candidate_holding == "ICICIBANK"
    assert "Manual review required; Cooling period active" in def_vm.reason
    assert def_vm.confidence == 74.0


def test_rationale_mapping():
    service = ActionCenterService()
    rationale_items = [
        "Approved ADD for CDSL (capacity slot 1/1).",
        "Approved REPLACE for INFY -> TCS (Turnover: 8.33%).",
        "Deferred REPLACE for WIPRO -> LTIM: Maximum replacement limit reached.",
    ]
    plan = RebalancePlan(rationale=rationale_items)

    vm = service.build_view_model(plan, observations=[])
    assert vm.rationale == rationale_items


def test_governance_snapshot_generation():
    service = ActionCenterService()
    vm = service.build_view_model(None, observations=[])

    snap = vm.governance_snapshot
    assert isinstance(snap, GovernanceSnapshotViewModel)
    assert snap.review_frequency == "Monthly Review"
    assert snap.rebalance_mode == "Conditional Rebalance"
    assert snap.max_replacements == "Max Replacements: 3"
    assert snap.turnover_budget == "Turnover Budget: 20%"
    assert snap.emergency_override == "Emergency Override: Enabled"


def test_ui_screen_loads_without_error(qapp):
    screen = PortfolioActionCenter()
    assert screen is not None

    plan = RebalancePlan(
        approved_actions=[
            RebalanceDecision(action="REPLACE", symbol="INFY", candidate_symbol="TCS", priority="HIGH", confidence=92.0)
        ],
        deferred_actions=[
            RebalanceDecision(action="REVIEW", symbol="HDFCBANK", candidate_symbol="ICICIBANK", priority="MEDIUM", confidence=74.0, rationale=["Cooling active"])
        ],
        turnover_pct=8.33,
        replacement_count=1,
        add_count=0,
        rationale=["Approved REPLACE for INFY -> TCS"],
    )

    screen.load_plan(plan, review_date="2026-08-02")
    assert screen.lbl_status_val.text() == "REBALANCE APPROVED"
    assert screen.approved_table.rowCount() == 1
    assert screen.deferred_table.rowCount() == 2  # 1 governance alert + 1 plan deferred action
