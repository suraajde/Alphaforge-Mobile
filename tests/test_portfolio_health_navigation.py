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
    # Verify no exceptions during screen creation and card structure presence
    try:
        screen = PortfolioHealth()
        assert screen is not None
        assert "Overall Health Score" in screen.cards
        assert "Diversification" in screen.cards
        assert "Concentration" in screen.cards
        assert "Position Count" in screen.cards
        assert "Cash Allocation" in screen.cards
        assert "Largest Position" in screen.cards
    except Exception as e:
        pytest.fail(f"PortfolioHealth screen creation raised an exception: {e}")


def test_live_data_binding(qapp):
    from services.portfolio_health_service import PortfolioHealthSnapshot

    class DummyHealthService:
        def build_snapshot(self):
            return PortfolioHealthSnapshot(
                position_count=15,
                portfolio_value=200000.0,
                invested_value=180000.0,
                cash_allocation_pct=10.0,
                largest_position="TCS",
                largest_position_weight_pct=12.5,
            )

    screen = PortfolioHealth(service=DummyHealthService())
    assert screen.cards["Position Count"].text() == "15"
    assert screen.cards["Cash Allocation"].text() == "10%"
    assert screen.cards["Largest Position"].text() == "TCS"


def test_evaluate_result_bound_to_cards(qapp):
    from services.portfolio_health_service import (
        PortfolioHealthResult,
        PortfolioHealthSnapshot,
    )

    class MockHealthService:
        def build_snapshot(self):
            return PortfolioHealthSnapshot(
                position_count=12,
                portfolio_value=100000.0,
                invested_value=95000.0,
                cash_allocation_pct=5.0,
                largest_position="RELIANCE",
                largest_position_weight_pct=15.0,
            )

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=85,
                grade="B",
                diversification_rating="GOOD",
                concentration_rating="MODERATE",
                position_count=12,
                largest_position_weight_pct=15.0,
                cash_allocation_pct=5.0,
            )

    screen = PortfolioHealth(service=MockHealthService())
    assert "85 / 100" in screen.cards["Overall Health Score"].text()
    assert screen.cards["Diversification"].text() == "GOOD"
    assert screen.cards["Concentration"].text() == "MODERATE"


def test_empty_portfolio_ui_safety(qapp):
    class EmptyHealthService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            from services.portfolio_health_service import PortfolioHealthResult
            return PortfolioHealthResult(
                score=70,
                grade="C",
                diversification_rating="POOR",
                concentration_rating="LOW",
                position_count=0,
                largest_position_weight_pct=0.0,
                cash_allocation_pct=0.0,
            )

    screen = PortfolioHealth(service=EmptyHealthService())
    assert "70 / 100" in screen.cards["Overall Health Score"].text()
    assert screen.cards["Diversification"].text() == "POOR"
    assert screen.cards["Concentration"].text() == "LOW"


def test_analytics_section_loads(qapp):
    screen = PortfolioHealth()
    assert hasattr(screen, "lbl_breakdown_div")
    assert hasattr(screen, "lbl_breakdown_conc")
    assert hasattr(screen, "lbl_breakdown_cash")
    assert hasattr(screen, "strengths_container")
    assert hasattr(screen, "weaknesses_container")


def test_breakdown_section_displays(qapp):
    from services.portfolio_health_service import (
        PortfolioHealthAnalytics,
        PortfolioHealthResult,
    )

    class MockService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=85,
                grade="B",
                diversification_rating="GOOD",
                concentration_rating="MODERATE",
                position_count=12,
                largest_position_weight_pct=15.0,
                cash_allocation_pct=5.0,
                analytics=PortfolioHealthAnalytics(
                    diversification_score=40,
                    concentration_score=30,
                    cash_score=15,
                    strengths=["Good diversification"],
                    weaknesses=["Elevated concentration"],
                ),
            )

    screen = PortfolioHealth(service=MockService())
    assert "Diversification: 40 / 40" in screen.lbl_breakdown_div.text()
    assert "Concentration: 30 / 40" in screen.lbl_breakdown_conc.text()
    assert "Cash Allocation: 15 / 20" in screen.lbl_breakdown_cash.text()


def test_strengths_section_displays(qapp):
    from services.portfolio_health_service import (
        PortfolioHealthAnalytics,
        PortfolioHealthResult,
    )

    class MockService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=100,
                grade="A",
                diversification_rating="GOOD",
                concentration_rating="LOW",
                position_count=12,
                largest_position_weight_pct=8.0,
                cash_allocation_pct=5.0,
                analytics=PortfolioHealthAnalytics(
                    diversification_score=40,
                    concentration_score=40,
                    cash_score=20,
                    strengths=["Good diversification", "Low concentration risk"],
                    weaknesses=[],
                ),
            )

    screen = PortfolioHealth(service=MockService())
    assert screen.strengths_container.count() == 2


def test_weaknesses_section_displays(qapp):
    from services.portfolio_health_service import (
        PortfolioHealthAnalytics,
        PortfolioHealthResult,
    )

    class MockService:
        def build_snapshot(self):
            return None

        def evaluate(self, snapshot=None):
            return PortfolioHealthResult(
                score=60,
                grade="D",
                diversification_rating="POOR",
                concentration_rating="HIGH",
                position_count=3,
                largest_position_weight_pct=35.0,
                cash_allocation_pct=25.0,
                analytics=PortfolioHealthAnalytics(
                    diversification_score=10,
                    concentration_score=10,
                    cash_score=5,
                    strengths=[],
                    weaknesses=[
                        "Portfolio may be under-diversified",
                        "High concentration risk",
                    ],
                ),
            )

    screen = PortfolioHealth(service=MockService())
    assert screen.weaknesses_container.count() == 2



