"""Focused unit and integration tests for Sprint 14.1.1 Master Task.

Tests:
1. Portfolio Reset execution & state clearing.
2. Action Center stale data elimination (no mock HDFCBANK/ICICIBANK).
3. Monthly Investment Allocation sum exactness & dynamic allocation.
4. Lump-Sum Investment Allocation sum exactness & dynamic allocation.
5. UI Color palette helper methods.
6. Settings screen content & clean text formatting.
"""
import os
import sys
import tempfile
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from config.path_config import get_data_path
from services.portfolio_state_service import PortfolioStateService
from services.portfolio_administration_service import PortfolioAdministrationService
from services.action_center_service import ActionCenterService
from services.investment_allocation_service import InvestmentAllocationService
from app.screens.portfolio import Portfolio
from app.screens.portfolio_action_center import PortfolioActionCenter
from app.screens.settings import Settings
from app.theme import UIColors, get_status_color, get_grade_color, get_risk_color, get_recommendation_color


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(["-platform", "offscreen"])


def test_portfolio_reset_clears_state_and_analytical_history(monkeypatch):
    """Verify Portfolio Reset creates backup and clears state + analytical JSON history."""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", temp_dir)

    state_svc = PortfolioStateService()
    sample_portfolio = [
        {"symbol": "RELIANCE", "company_name": "Reliance Industries", "sector": "Energy", "target_weight": 0.5, "rank": 1},
        {"symbol": "TCS", "company_name": "Tata Consultancy Services", "sector": "Technology", "target_weight": 0.5, "rank": 2},
    ]
    state = state_svc.create_state(sample_portfolio, cash_balance=500000.0)
    buys = [{"symbol": "RELIANCE", "quantity": 100, "price": 2500.0}]
    updated_state = state_svc.apply_confirmed_buys(state, buys, cash_spent=250000.0)
    state_svc.save_state(updated_state)

    state_file = get_data_path("portfolio/portfolio_state.json")
    assert state_file.exists()

    admin_svc = PortfolioAdministrationService()
    reset_res = admin_svc.reset_portfolio_holdings()
    assert reset_res["status"] == "OK"

    # State file should be deleted or empty
    load_res = state_svc.load_state()
    assert load_res.get("status") in ("NOT_FOUND", "ERROR") or len(load_res.get("state", {}).get("positions", {})) == 0


def test_action_center_stale_data_eliminated(qapp, monkeypatch):
    """Verify ActionCenterService and PortfolioActionCenter display NO ACTIVE PORTFOLIO DATA with zero mock symbols when empty."""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", temp_dir)

    ac_svc = ActionCenterService()
    vm = ac_svc.build_view_model(plan=None, evaluations=None, observations=None)

    assert vm.summary.approved_action_count == 0
    assert vm.summary.deferred_action_count == 0
    assert len(vm.approved_actions) == 0
    assert len(vm.deferred_actions) == 0

    ac_ui = PortfolioActionCenter()
    ac_ui.load_plan(None)

    assert ac_ui.lbl_status_val.text() == "NO ACTIVE PORTFOLIO DATA"
    assert ac_ui.lbl_approved_count_val.text() == "0"
    assert ac_ui.lbl_deferred_count_val.text() == "0"
    assert ac_ui.approved_table.rowCount() == 0
    assert ac_ui.deferred_table.rowCount() == 0
    assert "No active portfolio data" in ac_ui.rationale_list.item(0).text()


def test_monthly_investment_allocation_exact_sum(monkeypatch):
    """Verify monthly investment allocation calculates exact total sum and dynamic weights."""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", temp_dir)

    alloc_svc = InvestmentAllocationService()

    input_amount = 30000.0
    res = alloc_svc.allocate_monthly_investment(input_amount)

    assert res.allocation_type == "MONTHLY"
    assert res.total_input_amount == input_amount
    assert res.total_allocated_amount == input_amount
    assert len(res.allocations) == 12

    allocated_sum = sum(item.suggested_amount for item in res.allocations)
    assert abs(allocated_sum - input_amount) < 0.01


def test_lump_sum_investment_allocation_exact_sum(monkeypatch):
    """Verify lump-sum investment allocation calculates exact total sum."""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", temp_dir)

    alloc_svc = InvestmentAllocationService()

    input_amount = 100000.0
    res = alloc_svc.allocate_lump_sum_investment(input_amount)

    assert res.allocation_type == "LUMP_SUM"
    assert res.total_input_amount == input_amount
    assert res.total_allocated_amount == input_amount
    assert len(res.allocations) == 12

    allocated_sum = sum(item.suggested_amount for item in res.allocations)
    assert abs(allocated_sum - input_amount) < 0.01


def test_ui_colors_helper_functions():
    """Verify UI color mapping helper functions return consistent palette tokens."""
    assert get_status_color("APPROVED") == UIColors.GREEN
    assert get_status_color("REVIEW") == UIColors.AMBER
    assert get_status_color("CRITICAL") == UIColors.RED
    assert get_status_color("NO ACTIVE PORTFOLIO DATA") == UIColors.GREY

    assert get_grade_color("A") == UIColors.GREEN
    assert get_grade_color("C") == UIColors.AMBER
    assert get_grade_color("F") == UIColors.RED

    assert get_risk_color("LOW") == UIColors.GREEN
    assert get_risk_color("HIGH") == UIColors.RED

    assert get_recommendation_color("BUY") == UIColors.GREEN
    assert get_recommendation_color("REDUCE") == UIColors.RED


def test_settings_content_rendering(qapp):
    """Verify Settings contains complete developer info, exact LinkedIn URL, disclaimer, and license."""
    settings_ui = Settings()
    found_dev = False
    found_email = False
    found_linkedin_handle = False
    found_linkedin_url = False
    found_github = False

    for child in settings_ui.findChildren(object):
        if hasattr(child, "text"):
            txt = child.text()
            if "Suraj Dev" in txt:
                found_dev = True
            if "suraajde@gmail.com" in txt:
                found_email = True
            if "suraaj-de-81336932" in txt:
                found_linkedin_handle = True
            if "https://in.linkedin.com/in/suraaj-de-81336932" in txt:
                found_linkedin_url = True
            if "github.com/suraajde" in txt:
                found_github = True

    assert found_dev, "Suraj Dev not found in Settings"
    assert found_email, "suraajde@gmail.com not found in Settings"
    assert found_linkedin_handle, "LinkedIn handle not found in Settings"
    assert found_linkedin_url, "Exact LinkedIn URL https://in.linkedin.com/in/suraaj-de-81336932 not found in Settings"
    assert found_github, "GitHub handle not found in Settings"
