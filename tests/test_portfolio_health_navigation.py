import pytest
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.screens.portfolio_health import PortfolioHealth


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_portfolio_health_screen_instantiation(qapp):
    # Verify PortfolioHealth screen instantiates without exception
    screen = PortfolioHealth()
    assert screen is not None


def test_main_window_instantiation(qapp):
    # Verify MainWindow instantiates without exception
    win = MainWindow()
    assert win is not None


def test_portfolio_health_page_exists(qapp):
    # Verify PortfolioHealth page exists on MainWindow stacked widget
    win = MainWindow()
    assert hasattr(win, "portfolio_health")
    assert isinstance(win.portfolio_health, PortfolioHealth)
    assert win.pages.indexOf(win.portfolio_health) != -1


def test_health_btn_exists(qapp):
    # Verify health_btn exists on Sidebar
    win = MainWindow()
    assert hasattr(win.sidebar, "health_btn")


def test_navigation_wiring(qapp):
    # Verify navigation wiring: clicking health_btn sets current widget to portfolio_health
    win = MainWindow()
    win.sidebar.health_btn.click()
    assert win.pages.currentWidget() == win.portfolio_health


def test_no_exceptions_during_screen_creation(qapp):
    # Verify no exceptions during screen creation and placeholder cards presence
    try:
        screen = PortfolioHealth()
        assert screen is not None
        assert "Overall Health Score" in screen.cards
        assert screen.cards["Overall Health Score"].text() == "85 / 100"
        assert screen.cards["Diversification"].text() == "GOOD"
        assert screen.cards["Concentration"].text() == "MODERATE"
        assert screen.cards["Position Count"].text() == "12"
        assert screen.cards["Cash Allocation"].text() == "5%"
        assert screen.cards["Largest Position"].text() == "KPITTECH"
    except Exception as e:
        pytest.fail(f"PortfolioHealth screen creation raised an exception: {e}")
