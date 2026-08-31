import pytest
from PySide6.QtWidgets import QApplication, QFrame, QLabel

@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_portfolio_total_pnl_kpi_card(qapp):
    from app.screens.portfolio import Portfolio

    portfolio = Portfolio()
    assert hasattr(portfolio, "card_total_pnl")
    assert isinstance(portfolio.card_total_pnl, QFrame)
    assert portfolio.card_total_pnl.objectName() == "metricCard"

    assert hasattr(portfolio, "lbl_pnl_title")
    assert isinstance(portfolio.lbl_pnl_title, QLabel)
    assert portfolio.lbl_pnl_title.text() == "TOTAL RUNNING P&L"

    assert hasattr(portfolio, "lbl_total_pnl_val")
    assert isinstance(portfolio.lbl_total_pnl_val, QLabel)
    assert "Rs. " in portfolio.lbl_total_pnl_val.text()
    assert "%" in portfolio.lbl_total_pnl_val.text()


def test_dashboard_total_pnl_kpi_card(qapp):
    from app.screens.dashboard import Dashboard

    dashboard = Dashboard()
    assert hasattr(dashboard, "card_total_pnl")
    assert isinstance(dashboard.card_total_pnl, QFrame)
    assert dashboard.card_total_pnl.objectName() == "metricCard"

    assert hasattr(dashboard, "lbl_pnl_title")
    assert isinstance(dashboard.lbl_pnl_title, QLabel)
    assert dashboard.lbl_pnl_title.text() == "TOTAL RUNNING P&L"

    assert hasattr(dashboard, "lbl_total_pnl_val")
    assert isinstance(dashboard.lbl_total_pnl_val, QLabel)
    assert "Rs. " in dashboard.lbl_total_pnl_val.text()
    assert "%" in dashboard.lbl_total_pnl_val.text()
