"""Unit tests for Emergency Eject UI, direct capital transfer, sequential numbering, and Research Radar dynamic sync."""
import os
import sys
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMessageBox

# Ensure a headless QApplication exists for PySide6 widget tests
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


# ===========================================================================
# 1. RESEARCH RADAR TOP 30 & DYNAMIC SYNC TESTS
# ===========================================================================

def test_research_radar_populate_table_renders_strictly_30(qapp):
    """Verify that populate_table strictly renders 30 candidates without off-by-one errors."""
    from app.screens.research_radar import ResearchRadar

    radar = ResearchRadar()

    mock_candidates = [
        {
            "rank": i + 1,
            "symbol": f"SYM{i+1}",
            "company_name": f"Company {i+1}",
            "category": "MIDCAP",
            "sector": "TECH",
            "fundamental_score": 85.0,
            "technical_score": 75.0,
            "composite_score": 80.0,
            "readiness_score": 88.0,
            "market_health_score": 70.0,
            "data_confidence": 95.0,
            "coverage_score": 90.0,
            "data_status": "FRESH",
            "classification": "TOP TIER",
        }
        for i in range(45)
    ]

    radar.populate_table(mock_candidates)

    assert radar.table.rowCount() == 30
    assert radar.table.item(0, 0).text() == "1"
    assert radar.table.item(0, 1).text() == "SYM1"
    assert radar.table.item(29, 0).text() == "30"
    assert radar.table.item(29, 1).text() == "SYM30"


def test_dynamic_radar_and_reserve_bench_sync():
    """Verify dynamic synchronization of Alpha 12 and Reserve 8 based on live portfolio holdings."""
    from services.alpha12_mapping_service import Alpha12MappingService

    mapping_svc = Alpha12MappingService()

    # Radar universe with 30 ranked stocks: STOCK1 to STOCK30
    mock_universe = [
        {"symbol": f"STOCK{i+1}", "name": f"Company {i+1}", "rank": i + 1, "sector": "TECH", "composite_score": 80.0}
        for i in range(30)
    ]

    # Scenario 1: Active portfolio holds STOCK2 to STOCK13 (STOCK1 was ejected, STOCK13 promoted)
    active_portfolio = {
        f"STOCK{i+1}": {"symbol": f"STOCK{i+1}", "company_name": f"Company {i+1}", "current_value": 10000.0}
        for i in range(1, 13) # STOCK2 to STOCK13 (12 items)
    }

    result = mapping_svc.get_dynamic_alpha12_and_reserves(
        active_symbols=active_portfolio,
        radar_snapshot={"ranked": mock_universe},
    )

    alpha12 = result["alpha12"]
    reserve8 = result["alpha12_reserves"]

    # Active Alpha 12 must contain exactly 12 items, including promoted STOCK13 and NOT ejected STOCK1
    assert len(alpha12) == 12
    alpha_symbols = {a["symbol"] for a in alpha12}
    assert "STOCK13" in alpha_symbols
    assert "STOCK1" not in alpha_symbols

    # Reserve 8 bench must contain exactly 8 items not in active portfolio
    assert len(reserve8) == 8
    reserve_symbols = {r["symbol"] for r in reserve8}
    assert "STOCK13" not in reserve_symbols
    assert "STOCK1" in reserve_symbols # Ejected stock dropped onto reserve bench
    assert "STOCK20" in reserve_symbols

    # Scenario 2: When ejected stock drops out of universe and 12 constituents from top 20 are active,
    # then STOCK21 automatically slides up into the 8th slot of the visual Reserve 8 bench!
    universe_after_eject = [
        {"symbol": f"STOCK{i+1}", "name": f"Company {i+1}", "rank": i + 1, "sector": "TECH", "composite_score": 80.0}
        for i in range(1, 30) # STOCK2 to STOCK30 (STOCK1 removed)
    ]
    result2 = mapping_svc.get_dynamic_alpha12_and_reserves(
        active_symbols=active_portfolio, # Holds STOCK2 to STOCK13 (12 items)
        radar_snapshot={"ranked": universe_after_eject},
    )
    reserve_symbols2 = {r["symbol"] for r in result2["alpha12_reserves"]}
    assert len(reserve_symbols2) == 8
    assert "STOCK21" in reserve_symbols2 # STOCK21 slides up to fill slot 8


# ===========================================================================
# 2. PORTFOLIO SCREEN SEQUENTIAL NUMBERING & CAPITAL TRANSFER TESTS
# ===========================================================================

def test_portfolio_screen_sequential_serial_numbers(qapp, tmp_path):
    """Verify that Portfolio screen first column displays clean sequential numbers 1..N."""
    from app.screens.portfolio import Portfolio
    from services.portfolio_state_service import PortfolioStateService

    state_svc = PortfolioStateService()
    positions = [
        {"symbol": "CASTROLIND", "company_name": "Castrol India", "target_weight": 8.3333, "sector": "ENERGY", "category": "MIDCAP", "rank": 5},
        {"symbol": "GLAND", "company_name": "Gland Pharma", "target_weight": 8.3333, "sector": "HEALTHCARE", "category": "MIDCAP", "rank": 19},
        {"symbol": "AJANTPHARM", "company_name": "Ajanta Pharma", "target_weight": 8.3333, "sector": "HEALTHCARE", "category": "MIDCAP", "rank": 27},
    ]
    state = state_svc.create_state(portfolio=positions, cash_balance=50000.0)
    state_file = str(tmp_path / "portfolio_state.json")
    state_svc.save_state(state, path=state_file)

    portfolio_screen = Portfolio()
    portfolio_screen.portfolio_service.state_path = state_file
    portfolio_screen.portfolio_service.orchestrator.state_service.state_path = state_file
    portfolio_screen.load_portfolio()

    # Column 0 must be sequential 1, 2, 3 (ignoring internal ranks 5, 19, 27)
    assert portfolio_screen.table.rowCount() == 3
    assert portfolio_screen.table.item(0, 0).text() == "1"
    assert portfolio_screen.table.item(1, 0).text() == "2"
    assert portfolio_screen.table.item(2, 0).text() == "3"


def test_portfolio_screen_confirm_and_emergency_eject_capital_transfer(qapp, tmp_path):
    """Verify that emergency eject performs capital transfer and refreshes table."""
    from app.screens.portfolio import Portfolio
    from services.portfolio_state_service import PortfolioStateService

    state_svc = PortfolioStateService()
    positions = [
        {"symbol": "CASTROLIND", "company_name": "Castrol India", "target_weight": 8.3333, "sector": "ENERGY", "category": "MIDCAP", "rank": 1},
        {"symbol": "GLAND", "company_name": "Gland Pharma", "target_weight": 8.3333, "sector": "HEALTHCARE", "category": "MIDCAP", "rank": 2},
    ]
    state = state_svc.create_state(portfolio=positions, cash_balance=50000.0)
    state = state_svc.apply_confirmed_buys(state=state, buys=[{"symbol": "CASTROLIND", "quantity": 15, "price": 1000.0}])
    state_file = str(tmp_path / "portfolio_state.json")
    state_svc.save_state(state, path=state_file)

    portfolio_screen = Portfolio()
    portfolio_screen.portfolio_service.state_path = state_file
    portfolio_screen.portfolio_service.orchestrator.state_service.state_path = state_file
    portfolio_screen.load_portfolio()

    # Capture CASTROLIND's market value in state before ejection
    state_before = state_svc.load_state(path=state_file)["state"]
    castrol_val = state_before["positions"]["CASTROLIND"]["current_value"]
    assert castrol_val > 0.0

    with patch.object(QMessageBox, "warning", return_value=QMessageBox.Yes), \
         patch.object(QMessageBox, "information", return_value=QMessageBox.Ok):
        portfolio_screen.confirm_and_emergency_eject("CASTROLIND")

    loaded = state_svc.load_state(path=state_file)["state"]
    assert "CASTROLIND" not in loaded["positions"]
    assert len(loaded["positions"]) == 2

    # Check that capital was transferred and conserved (ejected market value + cash balance strictly conserved)
    rep_key = [k for k in loaded["positions"].keys() if k != "GLAND"][0]
    rep_pos = loaded["positions"][rep_key]
    assert round(rep_pos["invested_cost"] + loaded["cash_balance"], 2) == round(castrol_val + state_before.get("cash_balance", 0.0), 2)
    assert rep_pos["symbol"] == rep_key


# ===========================================================================
# 3. PORTFOLIO ACTION CENTER TESTS
# ===========================================================================

def test_portfolio_action_center_emergency_governance_table(qapp, tmp_path):
    """Verify that PortfolioActionCenter renders holdings governance table with Emergency Swap buttons."""
    from app.screens.portfolio_action_center import PortfolioActionCenter
    from services.portfolio_state_service import PortfolioStateService

    state_svc = PortfolioStateService()
    positions = [
        {"symbol": "CASTROLIND", "company_name": "Castrol India", "target_weight": 8.3333, "sector": "ENERGY", "category": "MIDCAP", "rank": 1},
        {"symbol": "GLAND", "company_name": "Gland Pharma", "target_weight": 8.3333, "sector": "HEALTHCARE", "category": "MIDCAP", "rank": 2},
    ]
    state = state_svc.create_state(portfolio=positions, cash_balance=50000.0)
    state_file = str(tmp_path / "portfolio_state.json")
    state_svc.save_state(state, path=state_file)

    with patch("config.path_config.get_data_path", return_value=state_file), \
         patch("services.portfolio_application_service.PortfolioApplicationService.get_status", return_value={"status": "OK", "state": state}):
        action_center = PortfolioActionCenter()
        action_center.load_plan(None)

        assert action_center.holdings_gov_table.columnCount() == 7
        assert action_center.holdings_gov_table.rowCount() == 2
        assert action_center.holdings_gov_table.horizontalHeaderItem(6).text() == "Emergency Swap"

        widget_row0 = action_center.holdings_gov_table.cellWidget(0, 6)
        assert widget_row0 is not None
        btn = widget_row0.findChild(QPushButton)
        assert btn is not None
        assert "Emergency Swap" in btn.text()
