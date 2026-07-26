from services.portfolio_analytics_service import (
    PortfolioAnalytics,
)

from services.portfolio_health_service import (
    PortfolioHealth,
)

from services.recommendation_engine import (
    RecommendationEngine,
)


def test_recommendation_engine():

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

    health = PortfolioHealth(
        overall_score=87,
        overall_grade="B",
        diversification_score=18,
        concentration_score=18,
        position_sizing_score=18,
        weight_balance_score=18,
        portfolio_structure_score=15,
        recommendation="Good portfolio. Minor optimisation recommended.",
    )

    engine = RecommendationEngine()

    report = engine.generate(
        analytics,
        health,
    )

    print()
    print("=" * 70)
    print("AI RECOMMENDATION ENGINE")
    print("=" * 70)

    print()

    print(
        f"Total Recommendations : {len(report.all_recommendations)}"
    )

    print()

    for recommendation in report.all_recommendations:

        print("-" * 70)
        print(f"Category      : {recommendation.category}")
        print(f"Priority      : {recommendation.priority}")
        print(f"Action        : {recommendation.action}")
        print(f"Confidence    : {recommendation.confidence}%")
        print(f"Target        : {recommendation.target}")
        print(f"Title         : {recommendation.title}")

        print()

        print("Reasons")

        for reason in recommendation.reasons:
            print(f" • {reason}")

        print()

        print("Suggested Action")
        print(recommendation.suggested_action)

        print()

    assert len(report.portfolio_recommendations) == 2
    assert report.portfolio_recommendations[0].action == "MONITOR"

    assert len(report.risk_recommendations) == 0

    print("=" * 70)
    print("Sprint 12.2 Recommendation Engine PASS")
    print("=" * 70)


if __name__ == "__main__":
    test_recommendation_engine()