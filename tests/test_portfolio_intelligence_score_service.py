from services.portfolio_intelligence_score_service import (
    PortfolioIntelligenceScoreService,
)
from services.portfolio_analytics_service import (
    PortfolioAnalytics,
    PortfolioHolding,
)
from services.portfolio_health_service import (
    PortfolioHealth,
)


def make_healthy_analytics():
    return PortfolioAnalytics(
        holding_count=12,
        total_weight=100.0,
        equal_weight=100.0 / 12,
        average_weight=8.33,
        largest_weight=8.5,
        smallest_weight=6.0,
        weight_range=2.5,
        concentration_score=8.5,
        diversification_score=91.5,
        overweight_positions=3,
        underweight_positions=9,
        hhi=0.05,
        effective_holdings=20.0,
        top3_weight=20.0,
        top5_weight=35.0,
        concentration_risk="Low",
        diversification_grade="A",
        warnings=[],
    )


def make_healthy_health():
    return PortfolioHealth(
        overall_score=95,
        overall_grade="A",
        diversification_score=19,
        concentration_score=19,
        position_sizing_score=19,
        weight_balance_score=19,
        portfolio_structure_score=19,
        recommendation="Healthy portfolio",
    )


def make_concentrated_analytics():
    return PortfolioAnalytics(
        holding_count=4,
        total_weight=100.0,
        equal_weight=25.0,
        average_weight=25.0,
        largest_weight=40.0,
        smallest_weight=10.0,
        weight_range=30.0,
        concentration_score=40.0,
        diversification_score=60.0,
        overweight_positions=3,
        underweight_positions=1,
        hhi=0.20,
        effective_holdings=5.0,
        top3_weight=85.0,
        top5_weight=95.0,
        concentration_risk="High",
        diversification_grade="C",
        warnings=["Example analytics warning"],
    )


def make_poor_health():
    return PortfolioHealth(
        overall_score=55,
        overall_grade="D",
        diversification_score=10,
        concentration_score=10,
        position_sizing_score=10,
        weight_balance_score=10,
        portfolio_structure_score=15,
        recommendation="Rebalance recommended",
    )


def test_score_range_and_components():
    svc = PortfolioIntelligenceScoreService()

    analytics = make_healthy_analytics()
    health = make_healthy_health()

    result = svc.score(analytics, health)

    # Score bounds
    assert 0.0 <= result.overall_score <= 100.0

    # Component scores present and in range
    assert isinstance(result.component_scores, dict)
    assert set(result.component_scores.keys()) >= set(
        [
            "health_overall",
            "diversification",
            "concentration",
            "position_sizing",
            "weight_balance",
            "structure",
        ]
    )

    for v in result.component_scores.values():
        assert 0.0 <= v <= 100.0

    # Summary non-empty
    assert isinstance(result.summary, str) and result.summary.strip()


def test_strengths_for_healthy_portfolio():
    svc = PortfolioIntelligenceScoreService()
    analytics = make_healthy_analytics()
    health = make_healthy_health()

    result = svc.score(analytics, health)

    assert isinstance(result.strengths, list) and result.strengths
    # Expect at least one positive strength
    assert any("Well diversified" in s or "Strong overall health" in s for s in result.strengths)


def test_weaknesses_for_concentrated_portfolio_and_warnings():
    svc = PortfolioIntelligenceScoreService()
    analytics = make_concentrated_analytics()
    health = make_poor_health()

    result = svc.score(analytics, health)

    assert isinstance(result.weaknesses, list) and result.weaknesses
    assert any("Large single holding" in w or "Top 3 holdings" in w for w in result.weaknesses)

    # Warnings from analytics should be propagated
    assert "Example analytics warning" in result.warnings


def test_summary_and_grade_ranges():
    svc = PortfolioIntelligenceScoreService()

    # All max scores -> should be A+
    analytics = make_healthy_analytics()
    health = PortfolioHealth(
        overall_score=100,
        overall_grade="A",
        diversification_score=20,
        concentration_score=20,
        position_sizing_score=20,
        weight_balance_score=20,
        portfolio_structure_score=20,
        recommendation="Excellent",
    )

    result = svc.score(analytics, health)
    assert result.investment_grade == "A+"
    assert result.summary and isinstance(result.summary, str)

    # Low scores -> grade D
    health_low = make_poor_health()
    analytics_low = make_concentrated_analytics()
    result_low = svc.score(analytics_low, health_low)
    assert result_low.investment_grade == "D"


def test_missing_or_partial_inputs_handled():
    svc = PortfolioIntelligenceScoreService()

    # Missing analytics
    health = make_healthy_health()
    result = svc.score(None, health)
    assert result.overall_score == 0.0
    assert any("Missing portfolio analytics" in w for w in result.warnings)

    # Missing health
    analytics = make_healthy_analytics()
    result2 = svc.score(analytics, None)
    assert result2.overall_score == 0.0
    assert any("Missing portfolio health" in w for w in result2.warnings)


def test_optional_inputs_do_not_break_api():
    svc = PortfolioIntelligenceScoreService()
    analytics = make_healthy_analytics()
    health = make_healthy_health()

    # Pass arbitrary objects for recommendations and decisions
    rec = {"dummy": True}
    dec = {"decision_summary": "none"}

    result = svc.score(analytics, health, recommendations=rec, decisions=dec)
    assert 0.0 <= result.overall_score <= 100.0
    assert isinstance(result.summary, str) and result.summary


if __name__ == "__main__":
    test_score_range_and_components()
    test_strengths_for_healthy_portfolio()
    test_weaknesses_for_concentrated_portfolio_and_warnings()
    test_summary_and_grade_ranges()
    test_missing_or_partial_inputs_handled()
    test_optional_inputs_do_not_break_api()
    print("All portfolio intelligence score tests passed")