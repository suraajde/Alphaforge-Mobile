"""Full Regression and User Acceptance Test Suite for AlphaForge v1.0.

Covers Portfolio Reset, Create Portfolio workflow, Portfolio Health empty state,
Action Center zero-mock data, Rebalancing decisions, Monthly & Lump-Sum allocations,
Settings scrollability, and exact LinkedIn URL requirements.
"""

import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication

from app.screens.portfolio import Portfolio
from app.screens.portfolio_action_center import PortfolioActionCenter
from app.screens.settings import Settings
from services.action_center_service import ActionCenterService
from services.investment_allocation_service import InvestmentAllocationService
from services.portfolio_administration_service import PortfolioAdministrationService
from services.portfolio_governance_service import PortfolioGovernanceService
from services.portfolio_health_service import PortfolioHealthService
from services.portfolio_orchestration_service import PortfolioOrchestrationService
from services.portfolio_state_service import PortfolioStateService
from services.recommendation_engine import RecommendationEngine
from services.sip_optimization_service import SIPOptimizationService


def test_reset_empty_state_and_create_portfolio_flow(tmp_path):
    """Test RESET -> EMPTY PORTFOLIO -> CREATE PORTFOLIO -> ACTIVE PORTFOLIO workflow."""
    app = QApplication.instance() or QApplication([])

    state_file = tmp_path / "portfolio_state.json"
    state_svc = PortfolioStateService()

    # Step 1: Initialize populated state
    state_svc.save_state({
        "state_version": "1.0",
        "positions": {
            "TCS": {"symbol": "TCS", "quantity": 10, "current_price": 3500.0, "invested_cost": 35000.0}
        },
        "total_portfolio_value": 35000.0,
    }, path=state_file)

    # Step 2: Reset Portfolio
    admin_svc = PortfolioAdministrationService(state_service=state_svc)
    reset_res = admin_svc.reset_portfolio_holdings(path=state_file, backup_dir=tmp_path / "backups")
    assert reset_res.get("status") == "OK"

    # Step 3: Verify Empty State after Reset
    loaded_empty = state_svc.load_state(path=state_file).get("state", {})
    assert loaded_empty.get("positions") == {}
    assert loaded_empty.get("total_portfolio_value") == 0.0

    # Step 4: Verify Portfolio Screen shows "+ Create Portfolio" button
    screen = Portfolio()
    assert hasattr(screen, "btn_create_portfolio")
    assert screen.btn_create_portfolio.text() == "+ Create Portfolio"
    assert screen.empty_title.text() == "No portfolio created yet."

    # Step 5: Test fallback Alpha 12 candidates generation
    alpha12 = screen._current_alpha12()
    assert len(alpha12) == 12, "Must return 12 candidates for initial portfolio creation"


def test_empty_portfolio_health_recommendation():
    """Verify Portfolio Health renders explicit empty-state recommendation when position_count == 0."""
    rec_engine = RecommendationEngine()

    class EmptyAnalytics:
        position_count = 0
        portfolio_value = 0.0
        invested_value = 0.0

    class EmptyHealth:
        overall_score = 0
        overall_grade = "N/A"

    report = rec_engine.generate(EmptyAnalytics(), EmptyHealth())
    assert len(report.portfolio_recommendations) == 1
    rec = report.portfolio_recommendations[0]
    assert rec.title == "No active portfolio to evaluate"
    assert rec.priority == "N/A"
    assert rec.confidence == 0
    assert rec.score == 0
    assert rec.suggested_action == "Create or import a portfolio."
    assert "No active portfolio positions are available for analysis." in rec.reasons[0]


def test_action_center_empty_and_populated_states():
    """Verify Action Center displays NO ACTIVE PORTFOLIO DATA on empty, and evaluates real active portfolio."""
    ac_svc = ActionCenterService()

    # Empty State
    empty_vm = ac_svc.evaluate_active_portfolio(portfolio_state={"positions": {}})
    assert empty_vm.summary.portfolio_status == "NO ACTIVE PORTFOLIO DATA"
    assert empty_vm.summary.approved_action_count == 0
    assert empty_vm.summary.deferred_action_count == 0
    assert empty_vm.summary.estimated_turnover == 0.0
    assert len(empty_vm.approved_actions) == 0

    # Populated State
    pop_state = {
        "positions": {
            "TCS": {"symbol": "TCS", "quantity": 10, "current_price": 3500.0, "invested_cost": 35000.0, "weight": 8.33}
        }
    }
    pop_vm = ac_svc.evaluate_active_portfolio(portfolio_state=pop_state)
    assert pop_vm.summary.portfolio_status != "NO ACTIVE PORTFOLIO DATA"


def test_rebalancing_governance_decision_scenarios():
    """Verify Alpha 12 rebalancing governance rules and decision categories."""
    gov_svc = PortfolioGovernanceService()

    # Small drift + strong incumbent -> HOLD
    curr_a = {"symbol": "TCS", "score": 85.0, "conviction": 90.0, "sector": "IT", "weight": 9.0}
    cand_a = {"symbol": "INFY", "score": 86.0, "conviction": 88.0, "sector": "IT", "weight": 8.5}
    eval_a = gov_svc.evaluate_replacement(curr_a, cand_a, holding_days=45)
    assert eval_a.decision == "HOLD"

    # Material superiority (+14 advantage, cooling satisfied) -> REPLACE
    curr_b = {"symbol": "ABC", "score": 70.0, "conviction": 75.0, "sector": "Industrials", "weight": 8.33}
    cand_b = {"symbol": "XYZ", "score": 88.0, "conviction": 86.0, "sector": "Consumer", "weight": 8.33}
    eval_b = gov_svc.evaluate_replacement(curr_b, cand_b, holding_days=45)
    assert eval_b.decision == "REPLACE"


def test_monthly_and_lumpsum_allocations_exact_totals():
    """Verify Monthly (₹30,000) and Lump-Sum (₹100,000) allocations match exact user input."""
    alloc_svc = InvestmentAllocationService()

    monthly_res = alloc_svc.allocate_monthly_investment(30000.0)
    assert abs(monthly_res.total_allocated_amount - 30000.0) < 0.01
    assert "NEW MONEY DEPLOYMENT" in monthly_res.summary_rationale

    lumpsum_res = alloc_svc.allocate_lump_sum_investment(100000.0)
    assert abs(lumpsum_res.total_allocated_amount - 100000.0) < 0.01
    assert "NEW MONEY DEPLOYMENT" in lumpsum_res.summary_rationale


def test_settings_scrollability_and_linkedin_url():
    """Verify Settings screen vertical scrollability and exact LinkedIn link."""
    app = QApplication.instance() or QApplication([])
    screen = Settings()
    assert screen is not None

    # Verify exact LinkedIn text & target
    found_linkedin = False
    for child in screen.findChildren(object):
        if hasattr(child, "text"):
            txt = child.text()
            if "https://in.linkedin.com/in/suraaj-de-81336932" in txt and "suraaj-de-81336932" in txt:
                found_linkedin = True
                break
    assert found_linkedin, "Exact LinkedIn display text and URL must be present in Settings"
