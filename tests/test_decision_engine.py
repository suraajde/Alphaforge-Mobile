from services.portfolio_analytics_service import (
    PortfolioAnalytics,
)

from services.portfolio_health_service import (
    PortfolioHealth,
)

from services.recommendation_engine import (
    RecommendationEngine,
)

from services.decision_engine import (
    DecisionEngine,
)


def test_decision_engine():

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

    recommendation_engine = RecommendationEngine()

    recommendation_report = recommendation_engine.generate(
        analytics,
        health,
    )

    decision_engine = DecisionEngine()

    decision_report = decision_engine.generate(
        recommendation_report,
    )

    print()
    print("=" * 70)
    print("AI DECISION ENGINE")
    print("=" * 70)
    print()

    print(
        f"Total Decisions : {decision_report.total_decisions}"
    )

    print()

    for decision in decision_report.decisions:

        stars = "★" * max(
            1,
            min(5, decision.score // 20),
        )

        print("-" * 70)
        print(f"Score         : {decision.score}/100")
        print(f"Rating        : {stars}")
        print(f"Decision      : {decision.decision_type}")
        print(f"Priority      : {decision.priority}")
        print(f"Source        : {decision.source_recommendation}")
        print(f"Title         : {decision.title}")

        print()

        print("Description")
        print(decision.description)

        print()

    assert decision_report.total_decisions == 4

    assert (
        decision_report.decisions[0].decision_type
        == "MONITOR"
    )

    print("=" * 70)
    print("Sprint 12.7 Decision Engine PASS")
    print("=" * 70)


if __name__ == "__main__":
    test_decision_engine()