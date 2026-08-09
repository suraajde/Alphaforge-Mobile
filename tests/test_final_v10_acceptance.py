"""Final AlphaForge v1.0 Acceptance Test Suite

Verifies all critical governance, portfolio, action center, allocation, reset,
stale data removal, dashboard, and developer contact requirements.
"""

import pytest
from pathlib import Path
from services.action_center_service import ActionCenterService, ActionCenterViewModel
from services.investment_allocation_service import InvestmentAllocationService
from services.portfolio_administration_service import PortfolioAdministrationService
from services.portfolio_governance_service import PortfolioGovernanceService, GovernanceEvaluation
from services.rebalance_decision_service import RebalanceDecisionService
from services.rebalance_orchestrator_service import RebalanceOrchestratorService
from services.sip_optimization_service import SIPOptimizationService
from services.portfolio_state_service import PortfolioStateService


def test_action_center_no_mock_data(tmp_path):
    """Verify DEFAULT_SAMPLE_EVALUATIONS is completely removed and empty state is clean."""
    import services.action_center_service as acs
    assert not hasattr(acs, "DEFAULT_SAMPLE_EVALUATIONS"), "DEFAULT_SAMPLE_EVALUATIONS must be removed"

    service = ActionCenterService()

    # Empty portfolio state test
    empty_state = {"state_version": "1.0", "positions": {}}
    vm = service.evaluate_active_portfolio(portfolio_state=empty_state)
    assert vm.summary.portfolio_status == "NO ACTIVE PORTFOLIO DATA"
    assert vm.summary.approved_action_count == 0
    assert vm.summary.deferred_action_count == 0
    assert vm.summary.estimated_turnover == 0.0
    assert len(vm.approved_actions) == 0
    assert len(vm.deferred_actions) == 0


def test_rebalancing_scenarios():
    """Verify specific rebalancing governance decision scenarios (Requirements 7 & 8)."""
    gov_svc = PortfolioGovernanceService()

    # Scenario A: Small drift + strong incumbent -> HOLD / NO ACTION REQUIRED
    curr_a = {"symbol": "TCS", "score": 85.0, "conviction": 90.0, "sector": "IT", "weight": 9.0}
    cand_a = {"symbol": "INFY", "score": 86.0, "conviction": 88.0, "sector": "IT", "weight": 8.5}
    eval_a = gov_svc.evaluate_replacement(curr_a, cand_a, holding_days=45)
    assert eval_a.decision == "HOLD", "Small drift with strong incumbent must return HOLD"

    # Scenario B: Weak challenger advantage (+2 pts) -> HOLD
    curr_b = {"symbol": "RELIANCE", "score": 84.0, "conviction": 85.0, "sector": "Energy", "weight": 8.33}
    cand_b = {"symbol": "ONGC", "score": 86.0, "conviction": 84.0, "sector": "Energy", "weight": 8.33}
    eval_b = gov_svc.evaluate_replacement(curr_b, cand_b, holding_days=60)
    assert eval_b.decision == "HOLD", "Challenger with only +2 advantage must not replace incumbent"

    # Scenario C: Material superiority (+14 pts advantage, >+5 conviction, cooling satisfied) -> REPLACE
    curr_c = {"symbol": "ABC", "score": 70.0, "conviction": 75.0, "sector": "Industrials", "weight": 8.33}
    cand_c = {"symbol": "XYZ", "score": 88.0, "conviction": 86.0, "sector": "Consumer", "weight": 8.33}
    eval_c = gov_svc.evaluate_replacement(curr_c, cand_c, holding_days=45)
    assert eval_c.decision == "REPLACE", "Materially superior challenger clearing thresholds must produce REPLACE"


def test_monthly_allocation_exact_total():
    """Verify Monthly Investment allocation totals EXACTLY user input amount (Requirement 4)."""
    service = InvestmentAllocationService()
    user_input = 30000.0

    result = service.allocate_monthly_investment(user_input)
    assert result.allocation_type == "MONTHLY"
    assert result.total_input_amount == user_input
    assert abs(result.total_allocated_amount - user_input) < 0.01, f"Total allocated {result.total_allocated_amount} must equal input {user_input}"
    assert "NEW MONEY DEPLOYMENT" in result.summary_rationale
    assert len(result.allocations) == 12

    for item in result.allocations:
        assert item.target_weight_pct > 0
        assert item.expected_weight_pct >= 0
        assert item.reason != ""


def test_lump_sum_allocation_exact_total():
    """Verify Lump-Sum Investment allocation totals EXACTLY user input amount (Requirement 5)."""
    service = InvestmentAllocationService()
    user_input = 100000.0

    result = service.allocate_lump_sum_investment(user_input)
    assert result.allocation_type == "LUMP_SUM"
    assert result.total_input_amount == user_input
    assert abs(result.total_allocated_amount - user_input) < 0.01
    assert "NEW MONEY DEPLOYMENT" in result.summary_rationale
    assert len(result.allocations) == 12


def test_sip_optimization_rationale_when_no_sip_txns():
    """Verify SIP Optimization rationale is explicit when portfolio positions exist but no SIP txns exist (Requirement 6)."""
    service = SIPOptimizationService()
    sample_state = {
        "state_version": "1.0",
        "positions": {
            "TCS": {"symbol": "TCS", "quantity": 10, "current_price": 3500.0, "invested_cost": 35000.0},
        },
        "transactions": []
    }
    result = service.get_sip_analysis(state_input=sample_state)
    assert result.analysis_status == "NO_DATA"
    assert result.rationale == "No historical SIP configuration recorded."
    assert "contains no positions" not in result.rationale


def test_portfolio_reset_cleanup(tmp_path):
    """Verify Portfolio Reset unlinks history files and returns clean state (Requirement 3)."""
    state_file = tmp_path / "portfolio_state.json"
    state_svc = PortfolioStateService()
    state_svc.save_state({
        "state_version": "1.0",
        "positions": {"TCS": {"symbol": "TCS", "quantity": 10}},
        "total_portfolio_value": 35000.0,
    }, path=state_file)

    admin_svc = PortfolioAdministrationService(state_service=state_svc)
    res = admin_svc.reset_portfolio_holdings(path=state_file, backup_dir=tmp_path / "backups")

    assert res.get("status") == "OK"
    loaded = state_svc.load_state(path=state_file).get("state", {})
    assert loaded.get("positions") == {}
    assert loaded.get("total_portfolio_value") == 0.0


def test_settings_developer_contact_info():
    """Verify Settings developer contact details and LinkedIn URL (Requirement 15)."""
    from app.screens.settings import Settings
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    screen = Settings()
    
    found_linkedin = False
    for widget in screen.findChildren(object):
        if hasattr(widget, "text"):
            txt = widget.text()
            if "https://in.linkedin.com/in/suraaj-de-81336932" in txt and "suraaj-de-81336932" in txt:
                found_linkedin = True
                break

    assert found_linkedin, "Exact LinkedIn URL https://in.linkedin.com/in/suraaj-de-81336932 with display text suraaj-de-81336932 must be present in Settings"
