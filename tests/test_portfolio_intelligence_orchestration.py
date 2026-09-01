from copy import deepcopy
from pathlib import Path
import tempfile

from services.portfolio_analytics_service import (
    PortfolioAnalytics,
)
from services.portfolio_health_service import (
    PortfolioHealth,
)
from services.recommendation_models import (
    RecommendationReport,
)
from services.decision_models import (
    DecisionReport,
)
from services.portfolio_orchestration_service import (
    PortfolioOrchestrationService,
)
from services.portfolio_application_service import (
    PortfolioApplicationService,
)


def test_orchestration_get_portfolio_intelligence():
    orchestrator = PortfolioOrchestrationService()

    state = {
        "positions": {
            "TATA": {
                "symbol": "TATA",
                "quantity": 10,
                "average_price": 100.0,
                "current_price": 120.0,
                "current_value": 1200.0,
                "actual_weight": 40.0,
                "target_weight": 35.0,
            },
            "RELIANCE": {
                "symbol": "RELIANCE",
                "quantity": 5,
                "average_price": 200.0,
                "current_price": 240.0,
                "current_value": 1200.0,
                "actual_weight": 40.0,
                "target_weight": 35.0,
            },
            "INFY": {
                "symbol": "INFY",
                "quantity": 3,
                "average_price": 150.0,
                "current_price": 200.0,
                "current_value": 600.0,
                "actual_weight": 20.0,
                "target_weight": 30.0,
            },
        },
        "cash_balance": 0.0,
        "total_portfolio_value": 3000.0,
        "invested_market_value": 3000.0,
    }

    intelligence = orchestrator.get_portfolio_intelligence(state)

    assert intelligence["status"] == "OK"
    assert intelligence["mode"] == "PORTFOLIO_INTELLIGENCE"
    assert isinstance(intelligence["state"], dict)
    assert isinstance(intelligence["analytics"], PortfolioAnalytics)
    assert isinstance(intelligence["health"], PortfolioHealth)
    assert isinstance(intelligence["recommendations"], RecommendationReport)
    assert isinstance(intelligence["decisions"], DecisionReport)

    analytics = intelligence["analytics"]
    assert analytics.holding_count == 3
    assert abs(analytics.total_weight - 100.0) < 0.01

    health = intelligence["health"]
    assert health.overall_score > 0
    assert health.overall_grade in ("A", "B", "C", "D", "F")

    print()
    print("=" * 70)
    print("PORTFOLIO INTELLIGENCE ORCHESTRATION TEST PASS")
    print("=" * 70)


def test_orchestration_price_map_refresh():
    orchestrator = PortfolioOrchestrationService()

    state = {
        "positions": {
            "TATA": {
                "symbol": "TATA",
                "quantity": 10,
                "average_price": 100.0,
                "current_price": 100.0,
                "current_value": 1000.0,
                "actual_weight": 50.0,
                "target_weight": 50.0,
            },
            "RELIANCE": {
                "symbol": "RELIANCE",
                "quantity": 5,
                "average_price": 200.0,
                "current_price": 200.0,
                "current_value": 1000.0,
                "actual_weight": 50.0,
                "target_weight": 50.0,
            },
        },
        "cash_balance": 0.0,
        "total_portfolio_value": 2000.0,
        "invested_market_value": 2000.0,
    }

    price_map = {"TATA": 200.0, "RELIANCE": 200.0}

    intelligence = orchestrator.get_portfolio_intelligence(
        state,
        price_map=price_map,
    )

    assert intelligence["status"] == "OK"
    refreshed_state = intelligence["state"]
    assert refreshed_state["positions"]["TATA"]["current_price"] == 200.0
    assert refreshed_state["positions"]["TATA"]["current_value"] == 2000.0

    print()
    print("=" * 70)
    print("PORTFOLIO INTELLIGENCE PRICE MAP REFRESH TEST PASS")
    print("=" * 70)


def test_application_service_intelligence_boundary():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = Path(tmpdir) / "test_state.json"

        orchestrator = PortfolioOrchestrationService(max_stock_weight=50.0)

        alpha12 = [
            {"symbol": "TATA", "target_weight": 50.0, "sector": "AUTO"},
            {"symbol": "RELIANCE", "target_weight": 50.0, "sector": "ENERGY"},
        ]

        prep = orchestrator.prepare_initial_investment(
            alpha12=alpha12,
            capital=10000.0,
            price_map={"TATA": 500.0, "RELIANCE": 2000.0},
        )

        confirm_res = orchestrator.confirm_initial_investment(
            recommendation=prep,
            save=True,
            path=state_path,
        )

        assert confirm_res["status"] == "OK"

        app_service = PortfolioApplicationService(
            orchestration_service=orchestrator,
            state_path=state_path,
        )

        intelligence = app_service.get_portfolio_intelligence(
            price_map={"TATA": 550.0, "RELIANCE": 2100.0}
        )

        assert intelligence["status"] == "OK"
        assert isinstance(intelligence["analytics"], PortfolioAnalytics)
        assert isinstance(intelligence["health"], PortfolioHealth)
        assert isinstance(intelligence["recommendations"], RecommendationReport)
        assert isinstance(intelligence["decisions"], DecisionReport)

        print()
        print("=" * 70)
        print("APPLICATION SERVICE PORTFOLIO INTELLIGENCE PASS")
        print("=" * 70)


if __name__ == "__main__":
    test_orchestration_get_portfolio_intelligence()
    test_orchestration_price_map_refresh()
    test_application_service_intelligence_boundary()

