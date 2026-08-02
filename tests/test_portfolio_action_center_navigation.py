import pytest
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.screens.portfolio_action_center import PortfolioActionCenter
from app.screens.sidebar import Sidebar


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_screen_registration(qapp):
    win = MainWindow()

    # Verify action_center is instantiated on MainWindow
    assert hasattr(win, "action_center")
    assert isinstance(win.action_center, PortfolioActionCenter)

    # Verify action_center is added to QStackedWidget
    assert win.pages.indexOf(win.action_center) != -1


def test_sidebar_navigation(qapp):
    win = MainWindow()

    # Verify sidebar button exists
    assert hasattr(win.sidebar, "action_center_btn")

    # Simulate sidebar click for Action Center
    win.sidebar.action_center_btn.click()

    # Verify current widget switched to action_center
    assert win.pages.currentWidget() == win.action_center


def test_mock_viewmodel_loading(qapp):
    screen = PortfolioActionCenter()

    # Verify initial load of mock data + integrated governance observation
    assert screen.lbl_status_val.text() == "NO ACTION REQUIRED"
    assert screen.lbl_approved_count_val.text() == "0"
    assert screen.lbl_deferred_count_val.text() == "2"
    assert screen.lbl_turnover_val.text() == "0.0%"
    assert screen.deferred_table.rowCount() == 2
    assert screen.deferred_table.item(0, 0).text() == "WARNING"
    assert screen.deferred_table.item(0, 1).text() == "Sector Concentration: Technology"
    assert screen.deferred_table.item(1, 1).text() == "HDFCBANK"
    assert screen.deferred_table.item(1, 2).text() == "ICICIBANK"

    # Governance Snapshot labels verification
    assert screen.lbl_gov_freq.text() == "Monthly Review"
    assert screen.lbl_gov_mode.text() == "Conditional Rebalance"
    assert screen.lbl_gov_max.text() == "Max Replacements: 3"
    assert screen.lbl_gov_budget.text() == "Turnover Budget: 20%"
    assert screen.lbl_gov_emergency.text() == "Emergency Override: Enabled"
