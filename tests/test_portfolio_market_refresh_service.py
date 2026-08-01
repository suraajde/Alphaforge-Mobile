import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest

from services.portfolio_market_refresh_service import PortfolioMarketRefreshService


def test_extract_symbols_from_state_dict():
    service = PortfolioMarketRefreshService()
    state = {
        "status": "OK",
        "positions": {
            "TATA": {"quantity": 10, "current_price": 100.0},
            "RELIANCE": {"quantity": 5, "current_price": 2500.0},
        },
    }
    symbols = service.extract_symbols(state)
    assert symbols == ["RELIANCE", "TATA"]


def test_extract_symbols_from_list_of_dicts():
    service = PortfolioMarketRefreshService()
    positions = [
        {"symbol": "infy", "quantity": 10},
        {"ticker": "tcs", "quantity": 20},
    ]
    symbols = service.extract_symbols(positions)
    assert symbols == ["INFY", "TCS"]


def test_extract_symbols_from_string_list():
    service = PortfolioMarketRefreshService()
    symbols = service.extract_symbols(["lupin", "  marico ", ""])
    assert symbols == ["LUPIN", "MARICO"]


@patch("services.portfolio_market_refresh_service.get_stock_data")
def test_fetch_live_prices_success_and_failure(mock_get_stock_data):
    def mock_stock_side_effect(symbol):
        if symbol == "TATA":
            return {"name": "Tata Motors", "price": 250.50}
        elif symbol == "RELIANCE":
            return {"name": "Reliance Industries", "price": 2900.00}
        elif symbol == "FAILSTOCK":
            return {"error": "Ticker not found"}
        elif symbol == "NOPRICE":
            return {"name": "No Price Stock", "price": "N/A"}
        return {"error": "Unknown symbol"}

    mock_get_stock_data.side_effect = mock_stock_side_effect

    service = PortfolioMarketRefreshService()
    portfolio = {
        "positions": {
            "TATA": {"quantity": 10},
            "RELIANCE": {"quantity": 5},
            "FAILSTOCK": {"quantity": 1},
            "NOPRICE": {"quantity": 2},
        }
    }

    result = service.fetch_live_prices(portfolio)

    assert set(result.keys()) == {"price_map", "updated_symbols", "failed_symbols"}
    assert result["price_map"] == {"TATA": 250.50, "RELIANCE": 2900.00}
    assert result["updated_symbols"] == ["RELIANCE", "TATA"]
    assert result["failed_symbols"] == ["FAILSTOCK", "NOPRICE"]


@patch("services.portfolio_market_refresh_service.get_stock_data")
def test_portfolio_application_service_auto_refresh(mock_get_stock_data):
    from services.portfolio_application_service import PortfolioApplicationService
    from services.portfolio_orchestration_service import PortfolioOrchestrationService
    from services.portfolio_state_service import PortfolioStateService

    mock_get_stock_data.return_value = {"price": 150.0}

    with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmpdir:
        state_path = Path(tmpdir) / "portfolio_state.json"
        state_service = PortfolioStateService()
        state_service.save_state({
            "status": "OK",
            "positions": {
                "TATA": {"quantity": 10, "current_price": 100.0, "current_value": 1000.0}
            },
            "cash_balance": 500.0,
            "invested_market_value": 1000.0,
            "portfolio_value": 1500.0
        }, path=state_path)

        orchestrator = PortfolioOrchestrationService(state_service=state_service)
        app_service = PortfolioApplicationService(
            orchestration_service=orchestrator,
            state_path=state_path
        )

        # Call refresh_portfolio without explicit price_map
        res = app_service.refresh_portfolio()

        assert res["status"] == "OK"
        assert res["state"]["positions"]["TATA"]["current_price"] == 150.0
        assert res["state"]["positions"]["TATA"]["current_value"] == 1500.0




