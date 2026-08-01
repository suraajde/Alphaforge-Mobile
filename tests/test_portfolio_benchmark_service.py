import pytest
from unittest.mock import patch, MagicMock

from services.portfolio_benchmark_service import PortfolioBenchmarkService


def test_get_nifty_return_1y_success():
    service = PortfolioBenchmarkService()
    with patch.object(service, "_fetch_symbol_1y_return", return_value=12.5) as mock_fetch:
        nifty_return = service.get_nifty_return_1y()
        mock_fetch.assert_called_once_with("^NSEI")
        assert nifty_return == 12.5


def test_get_nifty_return_1y_failure():
    service = PortfolioBenchmarkService()
    with patch.object(service, "_fetch_symbol_1y_return", return_value=None):
        nifty_return = service.get_nifty_return_1y()
        assert nifty_return is None


def test_get_portfolio_return_1y_success_dict_input():
    service = PortfolioBenchmarkService()
    portfolio = {
        "positions": {
            "RELIANCE": {"weight": 0.6, "current_value": 600.0},
            "TATA": {"weight": 0.4, "current_value": 400.0},
        }
    }

    def mock_fetch(symbol):
        if symbol == "RELIANCE":
            return 20.0
        elif symbol == "TATA":
            return 10.0
        return None

    with patch.object(service, "_fetch_symbol_1y_return", side_effect=mock_fetch):
        port_return = service.get_portfolio_return_1y(portfolio)
        # 0.6 * 20.0 + 0.4 * 10.0 = 12.0 + 4.0 = 16.0
        assert port_return == 16.0


def test_get_portfolio_return_1y_success_list_input():
    service = PortfolioBenchmarkService()
    portfolio = [
        {"symbol": "INFY", "target_weight": 0.5},
        {"symbol": "TCS", "target_weight": 0.5},
    ]

    def mock_fetch(symbol):
        if symbol == "INFY":
            return 15.0
        elif symbol == "TCS":
            return 5.0
        return None

    with patch.object(service, "_fetch_symbol_1y_return", side_effect=mock_fetch):
        port_return = service.get_portfolio_return_1y(portfolio)
        # 0.5 * 15.0 + 0.5 * 5.0 = 10.0
        assert port_return == 10.0


def test_get_alpha_return_1y_positive():
    service = PortfolioBenchmarkService()
    with patch.object(service, "get_portfolio_return_1y", return_value=18.5), \
         patch.object(service, "get_nifty_return_1y", return_value=12.0):
        alpha = service.get_alpha_return_1y({"positions": {}})
        assert alpha == 6.5


def test_get_alpha_return_1y_negative():
    service = PortfolioBenchmarkService()
    with patch.object(service, "get_portfolio_return_1y", return_value=8.0), \
         patch.object(service, "get_nifty_return_1y", return_value=12.0):
        alpha = service.get_alpha_return_1y({"positions": {}})
        assert alpha == -4.0


def test_get_benchmark_summary_beating_benchmark():
    service = PortfolioBenchmarkService()
    portfolio = {
        "positions": {
            "RELIANCE": {"weight": 1.0}
        }
    }
    with patch.object(service, "get_portfolio_return_1y", return_value=25.0), \
         patch.object(service, "get_nifty_return_1y", return_value=15.0):
        summary = service.get_benchmark_summary(portfolio)

        assert summary["portfolio_return_1y"] == 25.0
        assert summary["benchmark_return_1y"] == 15.0
        assert summary["alpha_return_1y"] == 10.0
        assert summary["status"] == "BEATING_BENCHMARK"
        assert summary["portfolio_symbol_count"] == 1
        assert summary["benchmark_symbol"] == "^NSEI"


def test_get_benchmark_summary_lagging_benchmark():
    service = PortfolioBenchmarkService()
    portfolio = [
        {"symbol": "TATA", "weight": 1.0}
    ]
    with patch.object(service, "get_portfolio_return_1y", return_value=5.0), \
         patch.object(service, "get_nifty_return_1y", return_value=15.0):
        summary = service.get_benchmark_summary(portfolio)

        assert summary["portfolio_return_1y"] == 5.0
        assert summary["benchmark_return_1y"] == 15.0
        assert summary["alpha_return_1y"] == -10.0
        assert summary["status"] == "LAGGING_BENCHMARK"
        assert summary["portfolio_symbol_count"] == 1
        assert summary["benchmark_symbol"] == "^NSEI"


def test_defensive_none_portfolio():
    service = PortfolioBenchmarkService()
    summary = service.get_benchmark_summary(None)

    assert summary["status"] == "UNKNOWN"
    assert summary["portfolio_symbol_count"] == 0
    assert summary["benchmark_symbol"] == "^NSEI"
    assert isinstance(summary["portfolio_return_1y"], float)
    assert isinstance(summary["benchmark_return_1y"], float)
    assert isinstance(summary["alpha_return_1y"], float)


def test_defensive_empty_portfolio():
    service = PortfolioBenchmarkService()
    summary = service.get_benchmark_summary({})

    assert summary["status"] == "UNKNOWN"
    assert summary["portfolio_symbol_count"] == 0
    assert summary["benchmark_symbol"] == "^NSEI"


def test_defensive_zero_weights_and_missing_symbols():
    service = PortfolioBenchmarkService()
    portfolio = [
        {"symbol": "", "weight": 0},
        {"weight": 0},
        {"symbol": "INVALID", "weight": 0}
    ]
    with patch.object(service, "_fetch_symbol_1y_return", return_value=None):
        summary = service.get_benchmark_summary(portfolio)
        assert summary["status"] == "UNKNOWN"
        assert summary["benchmark_symbol"] == "^NSEI"


def test_defensive_benchmark_fetch_failure():
    service = PortfolioBenchmarkService()
    portfolio = [{"symbol": "TATA", "weight": 1.0}]
    with patch.object(service, "get_nifty_return_1y", return_value=None), \
         patch.object(service, "get_portfolio_return_1y", return_value=12.0):
        summary = service.get_benchmark_summary(portfolio)

        assert summary["status"] == "UNKNOWN"
        assert summary["benchmark_return_1y"] == 0.0


def test_defensive_stock_data_failure():
    service = PortfolioBenchmarkService()
    portfolio = [{"symbol": "FAILSTOCK", "weight": 1.0}]
    with patch.object(service, "get_nifty_return_1y", return_value=15.0), \
         patch.object(service, "get_portfolio_return_1y", return_value=None):
        summary = service.get_benchmark_summary(portfolio)

        assert summary["status"] == "UNKNOWN"
        assert summary["portfolio_return_1y"] == 0.0


def test_output_schema():
    service = PortfolioBenchmarkService()
    summary = service.get_benchmark_summary(None)
    expected_keys = {
        "portfolio_return_1y",
        "benchmark_return_1y",
        "alpha_return_1y",
        "status",
        "portfolio_symbol_count",
        "benchmark_symbol",
    }
    assert set(summary.keys()) == expected_keys
