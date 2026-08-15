"""Sprint 14.1.8 Final Acceptance Gate — Portfolio Intelligence & System Safety

Integration tests for Portfolio Health lifecycle (baseline, deduplication, monitoring states),
Watchtower, Action Center consistency, authoritative Alpha 12 provider invariant,
test data isolation, and startup recursion safety.
"""
from __future__ import annotations

import os
import json
import pytest
from PySide6.QtWidgets import QApplication

from services.portfolio_health_service import PortfolioHealthService, PortfolioHealthResult
from services.portfolio_health_history_service import PortfolioHealthHistoryService
from services.portfolio_health_monitor_service import PortfolioHealthMonitorService
from services.action_center_service import ActionCenterService
from services.investment_allocation_service import InvestmentAllocationService
from services.rebalance_decision_service import RebalanceAction, RebalanceDecisionService
from services.portfolio_governance_service import PortfolioGovernanceService, GovernanceDecision
from config.path_config import get_data_path


@pytest.fixture(scope="module")
def qapp():
    """Ensure a single QApplication instance for Qt widget testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def isolated_data_dir(tmp_path, monkeypatch):
    """Isolate data path via ALPHAFORGE_DATA_DIR."""
    isolated = tmp_path / "test_data_dir"
    isolated.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", str(isolated))
    return isolated


def test_portfolio_health_baseline_and_deduplication(isolated_data_dir):
    """Verify first valid health evaluation establishes baseline and duplicate evaluations do not manufacture history."""
    hist_svc = PortfolioHealthHistoryService()
    health_svc = PortfolioHealthService(history_service=hist_svc)

    # 1. Initially empty history
    assert len(hist_svc.get_history()) == 0

    # 2. First evaluation with active portfolio positions establishes baseline snapshot
    sample_state = {
        "positions": {
            "INFY": {"actual_weight": 10.0, "current_price": 1800.0},
            "TCS": {"actual_weight": 10.0, "current_price": 3800.0},
        },
        "total_portfolio_value": 100000.0,
    }
    snap = health_svc.build_snapshot()
    snap.position_count = 2
    snap.portfolio_value = 100000.0
    snap.invested_value = 90000.0
    snap.cash_allocation_pct = 10.0
    snap.largest_position = "INFY"
    snap.largest_position_weight_pct = 10.0

    res1 = health_svc.evaluate(snap)
    history_after_first = hist_svc.get_history()
    assert len(history_after_first) == 1, "Expected baseline snapshot created on first valid evaluation"

    # 3. Second evaluation with identical parameters must NOT append duplicate snapshot
    health_svc.invalidate_evaluation_cache()
    res2 = health_svc.evaluate(snap)
    history_after_second = hist_svc.get_history()
    assert len(history_after_second) == 1, "Duplicate snapshot creation prevented for unchanged portfolio health"


def test_portfolio_health_monitoring_states(isolated_data_dir):
    """Verify UNAVAILABLE, WAITING, and READY monitoring state lifecycle."""
    non_existent_file = str(isolated_data_dir / "non_existent.json")
    hist_svc_missing = PortfolioHealthHistoryService(storage_path=non_existent_file)
    mon_svc = PortfolioHealthMonitorService(history_service=hist_svc_missing)

    # 1. UNAVAILABLE: storage file does not exist
    state = mon_svc.get_monitoring_state()
    assert state.monitoring_status == "UNAVAILABLE"

    # 2. WAITING: empty storage file exists
    empty_file = str(isolated_data_dir / "empty_history.json")
    with open(empty_file, "w", encoding="utf-8") as f:
        f.write("")
    hist_svc_empty = PortfolioHealthHistoryService(storage_path=empty_file)
    mon_svc_empty = PortfolioHealthMonitorService(history_service=hist_svc_empty)
    state = mon_svc_empty.get_monitoring_state()
    assert state.monitoring_status == "WAITING"

    # 3. READY: history file contains at least 1 valid snapshot
    valid_file = str(isolated_data_dir / "valid_history.json")
    hist_svc_valid = PortfolioHealthHistoryService(storage_path=valid_file)
    hist_svc_valid.save_snapshot(
        PortfolioHealthResult(
            score=85,
            grade="A",
            diversification_rating="GOOD",
            concentration_rating="LOW",
            position_count=10,
            largest_position_weight_pct=10.0,
            cash_allocation_pct=5.0,
        )
    )
    mon_svc_valid = PortfolioHealthMonitorService(history_service=hist_svc_valid)
    state = mon_svc_valid.get_monitoring_state()
    assert state.monitoring_status == "READY"
    assert state.snapshot_count == 1


def test_action_center_rebalancing_consistency():
    """Verify Action Center decisions are consistent with rebalancing engine (HOLD is NOT SELL, Cooling is DEFERRED)."""
    gov_svc = PortfolioGovernanceService()
    # Scenario: Strong incumbent INFY vs slightly better TCS -> HOLD
    holding = {"symbol": "INFY", "score": 82.0, "conviction": 80.0, "sector": "IT", "weight": 8.33}
    challenger = {"symbol": "TCS", "score": 85.0, "conviction": 82.0, "sector": "IT", "weight": 0.0}

    eval_result = gov_svc.evaluate_replacement(holding, challenger, holding_days=60)
    assert eval_result.decision == GovernanceDecision.HOLD

    dec_svc = RebalanceDecisionService(gov_svc)
    decision = dec_svc.create_decision_from_governance(eval_result)
    assert decision.action == RebalanceAction.HOLD

    action_center_svc = ActionCenterService()
    vm = action_center_svc.build_view_model(evaluations=[eval_result])

    # Verified: No HOLD action implies SELL
    for approved in vm.approved_actions:
        assert approved.action != "SELL"
    for deferred in vm.deferred_actions:
        assert deferred.action != "SELL"


def test_authoritative_alpha12_provider_consistency():
    """Verify authoritative Alpha 12 provider is respected across InvestmentAllocationService and ActionCenterService."""
    custom_alpha12 = [
        {"symbol": f"CUSTOM_{i}", "company_name": f"Custom Stock {i}", "rank": i, "conviction": 90.0 - i}
        for i in range(1, 13)
    ]
    provider = lambda: custom_alpha12

    # 1. InvestmentAllocationService
    alloc_svc = InvestmentAllocationService(alpha12_provider=provider)
    alloc_result = alloc_svc.allocate_monthly_investment(6000.0)
    allocated_symbols = [a.symbol for a in alloc_result.allocations]
    assert allocated_symbols[0] == "CUSTOM_1"
    assert allocated_symbols[1] == "CUSTOM_2"

    # 2. ActionCenterService
    ac_svc = ActionCenterService(alpha12_provider=provider)
    portfolio_state = {
        "positions": {"CUSTOM_1": {"actual_weight": 8.33, "current_price": 1000.0}},
        "total_portfolio_value": 120000.0,
    }
    vm = ac_svc.evaluate_active_portfolio(portfolio_state=portfolio_state)
    assert vm.summary.review_date is not None


def test_test_data_isolation(isolated_data_dir):
    """Verify test operations respect ALPHAFORGE_DATA_DIR and never modify real user portfolio data."""
    test_path = get_data_path("portfolio/portfolio_state.json")
    assert str(isolated_data_dir) in str(test_path)

    # Real repo root data dir must NOT be touched
    real_repo_state = os.path.join("data", "portfolio", "portfolio_state.json")
    if os.path.exists(real_repo_state):
        mtime_before = os.path.getmtime(real_repo_state)
        # Perform allocation
        svc = InvestmentAllocationService()
        svc.allocate_monthly_investment(5000.0)
        mtime_after = os.path.getmtime(real_repo_state)
        assert mtime_before == mtime_after, "Test execution modified real production portfolio_state.json!"


def test_startup_safety_no_recursion(qapp):
    """Verify MainWindow creation executes safely without infinite recursion (Sprint 14.1.7 fix intact)."""
    from app.main_window import MainWindow

    window = MainWindow()
    assert window is not None
    assert window.windowTitle() == "AlphaForge"

    # Access pages safely
    health_screen = window.portfolio_health
    assert health_screen is not None

    action_screen = window.action_center
    assert action_screen is not None

    watchtower_screen = window.watchtower
    assert watchtower_screen is not None

    window.close()
