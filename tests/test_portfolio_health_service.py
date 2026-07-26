from services.portfolio_analytics_service import (
    PortfolioAnalytics,
)

from services.portfolio_health_service import (
    PortfolioHealthService,
)


def test_portfolio_health():

    analytics = PortfolioAnalytics(
        holding_count=7,
        total_weight=100.0,
        equal_weight=14.29,
        average_weight=14.29,
        largest_weight=25.0,
        smallest_weight=7.0,
        weight_range=18.0,
        concentration_score=25.0,
        diversification_score=75.0,
        overweight_positions=4,
        underweight_positions=3,
        hhi=0.1688,
        effective_holdings=5.92,
        top3_weight=60.0,
        top5_weight=85.0,
        concentration_risk="Moderate",
        diversification_grade="B",
        warnings=[],
    )

    service = PortfolioHealthService()

    health = service.evaluate(analytics)

    print()
    print("=" * 70)
    print("PORTFOLIO HEALTH REPORT")
    print("=" * 70)

    print(f"Overall Score           : {health.overall_score}/100")
    print(f"Overall Grade           : {health.overall_grade}")

    print()

    print(f"Diversification         : {health.diversification_score}/20")
    print(f"Concentration           : {health.concentration_score}/20")
    print(f"Position Sizing         : {health.position_sizing_score}/20")
    print(f"Weight Balance          : {health.weight_balance_score}/20")
    print(f"Portfolio Structure     : {health.portfolio_structure_score}/20")

    print()
    print("Recommendation")
    print("----------------------------")
    print(health.recommendation)

    assert health.overall_score > 0
    assert health.overall_grade in (
        "A",
        "B",
        "C",
        "D",
    )

    assert health.diversification_score <= 20
    assert health.concentration_score <= 20
    assert health.position_sizing_score <= 20
    assert health.weight_balance_score <= 20
    assert health.portfolio_structure_score <= 20

    print()
    print("=" * 70)
    print("Sprint 12.1.2 Portfolio Health PASS")
    print("=" * 70)


if __name__ == "__main__":
    test_portfolio_health()