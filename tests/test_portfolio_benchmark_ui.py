import os
import pytest
from unittest.mock import patch, MagicMock

# Set Qt platform to offscreen for headless unit testing
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication

# Ensure single QApplication instance
app = QApplication.instance() or QApplication([])

from app.screens.portfolio import Portfolio


@pytest.fixture
def portfolio_screen():
    with patch("app.screens.portfolio.create_portfolio_application_service") as mock_app_svc:
        mock_svc = MagicMock()
        mock_svc.refresh_portfolio.return_value = {"status": "OK"}
        mock_svc.get_portfolio_summary.return_value = {"status": "OK", "portfolio_exists": False}
        mock_svc.get_portfolio_intelligence.return_value = {"status": "NOT_FOUND"}
        mock_app_svc.return_value = mock_svc

        screen = Portfolio()
        yield screen


def test_benchmark_widget_creation(portfolio_screen):
    assert hasattr(portfolio_screen, "benchmark_frame")
    assert hasattr(portfolio_screen, "bm_portfolio_return_value")
    assert hasattr(portfolio_screen, "bm_nifty_return_value")
    assert hasattr(portfolio_screen, "bm_alpha_return_value")
    assert hasattr(portfolio_screen, "bm_status_value")
    assert portfolio_screen.benchmark_frame is not None


def test_render_benchmark_summary_beating(portfolio_screen):
    bm_summary = {
        "portfolio_return_1y": 24.8,
        "benchmark_return_1y": 11.2,
        "alpha_return_1y": 13.6,
        "status": "BEATING_BENCHMARK",
        "portfolio_symbol_count": 5,
        "benchmark_symbol": "^NSEI"
    }

    portfolio_screen._render_benchmark_summary(bm_summary)

    assert portfolio_screen.bm_portfolio_return_value.text() == "+24.8%"
    assert portfolio_screen.bm_nifty_return_value.text() == "+11.2%"
    assert portfolio_screen.bm_alpha_return_value.text() == "+13.6%"
    assert portfolio_screen.bm_status_value.text() == "✓ Outperforming Nifty 50"


def test_render_benchmark_summary_lagging(portfolio_screen):
    bm_summary = {
        "portfolio_return_1y": -5.2,
        "benchmark_return_1y": 10.0,
        "alpha_return_1y": -15.2,
        "status": "LAGGING_BENCHMARK",
        "portfolio_symbol_count": 3,
        "benchmark_symbol": "^NSEI"
    }

    portfolio_screen._render_benchmark_summary(bm_summary)

    assert portfolio_screen.bm_portfolio_return_value.text() == "-5.2%"
    assert portfolio_screen.bm_nifty_return_value.text() == "+10.0%"
    assert portfolio_screen.bm_alpha_return_value.text() == "-15.2%"
    assert portfolio_screen.bm_status_value.text() == "⚠ Underperforming Nifty 50"


def test_render_benchmark_summary_unknown(portfolio_screen):
    bm_summary = {
        "portfolio_return_1y": 0.0,
        "benchmark_return_1y": 0.0,
        "alpha_return_1y": 0.0,
        "status": "UNKNOWN",
        "portfolio_symbol_count": 0,
        "benchmark_symbol": "^NSEI"
    }

    portfolio_screen._render_benchmark_summary(bm_summary)

    assert portfolio_screen.bm_portfolio_return_value.text() == "N/A"
    assert portfolio_screen.bm_nifty_return_value.text() == "N/A"
    assert portfolio_screen.bm_alpha_return_value.text() == "N/A"
    assert portfolio_screen.bm_status_value.text() == "Benchmark Data Unavailable"


def test_render_benchmark_summary_fallback_on_invalid_input(portfolio_screen):
    # Should not raise exception on None or malformed dict
    portfolio_screen._render_benchmark_summary(None)
    assert portfolio_screen.bm_status_value.text() == "Benchmark Data Unavailable"

    portfolio_screen._render_benchmark_summary("invalid_data")
    assert portfolio_screen.bm_status_value.text() == "Benchmark Data Unavailable"
