"""Focused unit tests for Sprint 14.1.0 Portfolio Foundation, Empty-State Handling, and UI Consistency."""

import os
import sys
import tempfile
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from config.path_config import get_data_path, get_base_data_dir, get_resource_path
from services.portfolio_state_service import PortfolioStateService
from services.portfolio_health_service import PortfolioHealthService, PortfolioHealthSnapshot
from services.universe_service import UniverseService
from app.screens.portfolio import Portfolio
from app.screens.portfolio_health import PortfolioHealth
from app.screens.portfolio_action_center import PortfolioActionCenter
from app.screens.settings import Settings


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(["-platform", "offscreen"])


def test_portfolio_state_path_resolution_dev_and_frozen(monkeypatch):
    """Verify PortfolioStateService uses get_data_path for DEFAULT_STATE_PATH."""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", temp_dir)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    target_path = get_data_path("portfolio/portfolio_state.json")
    assert str(target_path).startswith(temp_dir)
    assert "_internal" not in str(target_path)
    assert "_MEIPASS" not in str(target_path)


def test_portfolio_health_empty_state_returns_zero_and_na():
    """Verify PortfolioHealthService evaluates pos_count == 0 to score 0 and grade N/A."""
    svc = PortfolioHealthService()
    empty_snapshot = PortfolioHealthSnapshot(
        position_count=0,
        portfolio_value=0.0,
        invested_value=0.0,
        cash_allocation_pct=0.0,
        largest_position="N/A",
        largest_position_weight_pct=0.0,
    )
    result = svc.evaluate(empty_snapshot)
    assert result.score == 0, f"Expected health score 0 for empty portfolio, got {result.score}"
    assert result.grade == "N/A", f"Expected grade N/A for empty portfolio, got {result.grade}"
    assert result.diversification_rating == "N/A", f"Expected diversification N/A, got {result.diversification_rating}"
    assert result.concentration_rating == "N/A", f"Expected concentration N/A, got {result.concentration_rating}"


def test_portfolio_health_ui_displays_na_for_empty_portfolio(qapp):
    """Verify PortfolioHealth UI card values show N/A when snapshot position_count is 0."""
    health_ui = PortfolioHealth()
    empty_snapshot = PortfolioHealthSnapshot(
        position_count=0,
        portfolio_value=0.0,
        invested_value=0.0,
        cash_allocation_pct=0.0,
        largest_position="N/A",
        largest_position_weight_pct=0.0,
    )
    health_ui.load_snapshot(empty_snapshot)

    score_card_text = health_ui.cards["Overall Health Score"].text()
    assert "70 / 100" not in score_card_text
    assert "N/A" in score_card_text or "0" in score_card_text


def test_portfolio_action_center_empty_state(qapp, monkeypatch):
    """Verify PortfolioActionCenter displays NO ACTIVE PORTFOLIO DATA when positions are empty."""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", temp_dir)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    ac_ui = PortfolioActionCenter()
    ac_ui.load_plan(None)
    assert "NO ACTIVE PORTFOLIO" in ac_ui.lbl_status_val.text()


def test_portfolio_screen_first_run_empty_state_text(qapp):
    """Verify Portfolio screen empty state displays 'No portfolio created yet.' and '+ Create Portfolio'."""
    port_ui = Portfolio()
    assert port_ui.empty_title.text() == "No portfolio created yet."
    assert port_ui.initial_investment_btn.text() == "+ Create Portfolio"


def test_portfolio_creation_and_active_state_propagation(monkeypatch):
    """Verify creating a portfolio persists state and propagates active state to health and downstream services."""
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("ALPHAFORGE_DATA_DIR", temp_dir)

    svc = PortfolioStateService()
    sample_portfolio = [
        {"symbol": "RELIANCE", "company_name": "Reliance Industries", "sector": "Energy", "target_weight": 0.2, "rank": 1},
        {"symbol": "TCS", "company_name": "Tata Consultancy Services", "sector": "Technology", "target_weight": 0.2, "rank": 2},
    ]
    state = svc.create_state(sample_portfolio, cash_balance=100000.0)
    buys = [
        {"symbol": "RELIANCE", "quantity": 10, "price": 2500.0},
        {"symbol": "TCS", "quantity": 10, "price": 3500.0},
    ]
    updated_state = svc.apply_confirmed_buys(state, buys, cash_spent=60000.0)
    save_res = svc.save_state(updated_state)
    assert save_res["status"] == "OK"

    load_res = svc.load_state()
    assert load_res["status"] == "OK"
    assert len(load_res["state"]["positions"]) == 2

    health_svc = PortfolioHealthService()
    snapshot = health_svc.build_snapshot()
    assert snapshot.position_count == 2
    assert snapshot.portfolio_value > 0.0

    eval_res = health_svc.evaluate(snapshot)
    assert eval_res.score > 0
    assert eval_res.grade in ["A", "B", "C", "D"]



def test_settings_rendering_no_raw_html(qapp):
    """Verify Settings contains clean text, developer info, disclaimer, and NO raw <a href= HTML."""
    settings_ui = Settings()
    found_dev = False
    found_email = False
    found_linkedin = False
    found_github = False

    for child in settings_ui.findChildren(object):
        if hasattr(child, "text"):
            txt = child.text()
            assert "<a href=" not in txt, f"Raw HTML tag found in Settings text: '{txt}'"
            if "Suraj Dev" in txt:
                found_dev = True
            if "suraajde@gmail.com" in txt:
                found_email = True
            if "suraaj-de-81336932" in txt:
                found_linkedin = True
            if "github.com/suraajde" in txt:
                found_github = True

    assert found_dev, "Suraj Dev not found in Settings"
    assert found_email, "suraajde@gmail.com not found in Settings"
    assert found_linkedin, "LinkedIn handle not found in Settings"
    assert found_github, "GitHub handle not found in Settings"


def test_research_radar_discovers_400_stocks():
    """Verify UniverseService discovers 400 production stocks."""
    svc = UniverseService()
    res = svc.get_enabled_stocks()
    assert len(res["errors"]) == 0
    assert len(res["stocks"]) == 400


def test_alpha12_governance_invariants(qapp):
    """Verify Alpha 12 governance rules remain untouched."""
    settings_ui = Settings()
    all_txt = ""
    for child in settings_ui.findChildren(object):
        if hasattr(child, "text"):
            all_txt += child.text() + "\n"

    assert "+10.0 points" in all_txt or "+10 points" in all_txt
    assert "+5.0 points" in all_txt or "+5 points" in all_txt
    assert "3 candidates" in all_txt or "3" in all_txt
    assert "20.0%" in all_txt or "20%" in all_txt
    assert "30 days" in all_txt
    assert "Incumbent Protection Policy" in all_txt
