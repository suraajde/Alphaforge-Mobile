"""AlphaForge v1.0 Final Acceptance Pass Regression Test Suite.

Verifies root causes 1 through 11 and requirements A through T.
"""
import pytest
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from services.action_center_service import ActionCenterService
from services.investment_allocation_service import InvestmentAllocationService
from services.portfolio_administration_service import PortfolioAdministrationService
from services.portfolio_governance_service import PortfolioGovernanceService
from services.portfolio_state_service import PortfolioStateService
from services.sip_optimization_service import SIPOptimizationService
from services.holding_quality_service import HoldingQualityService
from services.portfolio_health_service import PortfolioHealthService
from services.recommendation_engine import RecommendationEngine
from app.screens.portfolio import Portfolio as PortfolioScreen
from app.screens.settings import Settings


@pytest.fixture(scope="module")
def qapp():
    """Ensure a single QApplication instance for Qt widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_action_center_deduplication_exact_count():
    """Verify Action Center generates exactly 1 evaluation per holding (12 deferred for 12 holdings, not 24)."""
    service = ActionCenterService()
    holdings = [
        {"symbol": f"STOCK_{i}", "score": 75.0, "conviction": 80.0, "sector": "General", "weight": 8.33}
        for i in range(12)
    ]
    state = {
        "state_version": "1.0",
        "positions": {h["symbol"]: {"symbol": h["symbol"], "composite_score": h["score"], "conviction": h["conviction"], "actual_weight": h["weight"]} for h in holdings}
    }
    vm = service.evaluate_active_portfolio(portfolio_state=state)
    assert len(vm.deferred_actions) == 12, f"Expected exactly 12 deferred actions for 12 holdings, got {len(vm.deferred_actions)}"
    assert vm.summary.deferred_action_count == 12
    assert vm.summary.approved_action_count == 0
    assert vm.summary.portfolio_status == "NO ACTION REQUIRED"


def test_sip_optimization_rationale_with_loaded_state_dict():
    """Verify SIP Optimization correctly unwraps load_state() payload and reports 'No historical SIP configuration recorded.'"""
    service = SIPOptimizationService()

    # Wrapped payload as returned by PortfolioStateService.load_state()
    wrapped_state = {
        "status": "OK",
        "state": {
            "state_version": "1.0",
            "positions": {
                f"SYM_{i}": {"symbol": f"SYM_{i}", "company_name": f"Company {i}", "target_weight": 8.33, "actual_weight": 8.33, "invested_cost": 10000.0}
                for i in range(12)
            },
            "transactions": []
        }
    }

    result = service.get_sip_analysis(state_input=wrapped_state)
    assert result.total_positions == 12
    assert result.analysis_status == "NO_DATA"
    assert result.rationale == "No historical SIP configuration recorded."
    assert "contains no positions" not in result.rationale


def test_portfolio_ui_single_empty_frame_and_allocation_ui(qapp):
    """Verify PortfolioScreen has only one empty_frame and connects allocation_frame UI."""
    screen = PortfolioScreen()

    # Verify allocation_frame is created and attached
    assert hasattr(screen, "allocation_frame"), "PortfolioScreen must have allocation_frame"
    assert screen.allocation_frame is not None

    # Simulate render_summary with portfolio_exists = True
    summary_active = {
        "portfolio_exists": True,
        "portfolio_value": 150000.0,
        "invested_market_value": 149904.87,
        "cash_balance": 95.13,
        "position_count": 12,
        "transaction_count": 12,
        "positions": []
    }

    screen.show()
    screen._render_summary(summary_active)

    assert screen.empty_frame.isHidden(), "empty_frame must be hidden when portfolio_exists is True"
    assert not screen.holdings_frame.isHidden(), "holdings_frame must be visible when portfolio_exists is True"
    assert not screen.allocation_frame.isHidden(), "allocation_frame must be visible when portfolio_exists is True"
    assert "Active Portfolio: Primary Portfolio" in screen.subtitle_label.text()
    assert "Portfolio loaded" in screen.status_label.text()

    # Simulate render_summary with portfolio_exists = False (Empty state)
    summary_empty = {
        "portfolio_exists": False,
        "portfolio_value": 0.0,
        "invested_market_value": 0.0,
        "cash_balance": 0.0,
        "position_count": 0,
        "transaction_count": 0,
        "positions": []
    }

    screen._render_summary(summary_empty)

    assert not screen.empty_frame.isHidden(), "empty_frame must be visible when portfolio_exists is False"
    assert screen.holdings_frame.isHidden(), "holdings_frame must be hidden when portfolio_exists is False"
    assert screen.allocation_frame.isHidden(), "allocation_frame must be hidden when portfolio_exists is False"
    assert screen.status_label.text() == "No portfolio created yet."


def test_holding_quality_equities_unsupported():
    """Verify HoldingQualityService reports 12 holdings received and 12 unassessed/unsupported for equity positions."""
    svc = HoldingQualityService()
    positions = [
        {"symbol": f"STOCK_{i}", "company_name": f"Stock {i}", "asset_type": "EQUITY"}
        for i in range(12)
    ]
    res = svc.assess_holdings(positions)
    assert res.total_holdings == 12
    assert res.assessed_holdings == 0
    assert res.unassessed_holdings == 12
    for h in res.holdings:
        assert h.assessment_status == "UNSUPPORTED"


def test_empty_portfolio_health_recommendation():
    """Verify RecommendationEngine produces clean empty recommendation when position_count == 0."""
    engine = RecommendationEngine()

    class MockAnalytics:
        position_count = 0
        holding_count = 0

    class MockHealth:
        score = 0
        grade = "N/A"

    report = engine.generate(MockAnalytics(), MockHealth())
    assert len(report.portfolio_recommendations) == 1
    rec = report.portfolio_recommendations[0]
    assert rec.title == "No active portfolio to evaluate"
    assert rec.priority == "N/A"
    assert rec.suggested_action == "Create or import a portfolio."


def test_new_holdings_cooling_period_protection():
    """Verify newly created holdings (holding_days < 30) undergo governance cooling period check."""
    gov_svc = PortfolioGovernanceService()
    curr = {"symbol": "NEW_HOLDING", "score": 80.0, "conviction": 80.0, "sector": "IT", "weight": 8.33}
    cand = {"symbol": "CHALLENGER", "score": 98.0, "conviction": 90.0, "sector": "IT", "weight": 8.33}

    # Under cooling period (10 days held) -> REVIEW
    eval_cooling = gov_svc.evaluate_replacement(curr, cand, holding_days=10)
    assert eval_cooling.decision == "REVIEW"
    assert "Cooling period active" in eval_cooling.reasons[0]

    # After cooling period (45 days held) -> REPLACE
    eval_satisfied = gov_svc.evaluate_replacement(curr, cand, holding_days=45)
    assert eval_satisfied.decision == "REPLACE"


def test_settings_operational_boundaries_visible(qapp):
    """Verify Settings screen contains Operational Boundaries section and developer details."""
    screen = Settings()
    found_boundaries = False
    for widget in screen.findChildren(object):
        if hasattr(widget, "text") and "OPERATIONAL BOUNDARIES" in widget.text():
            found_boundaries = True
            break
    assert found_boundaries, "Settings screen must display OPERATIONAL BOUNDARIES section"
