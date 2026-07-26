from services.portfolio_analytics_service import (
    PortfolioAnalyticsService,
    PortfolioHolding,
)


def test_portfolio_analytics():

    service = PortfolioAnalyticsService()

    portfolio = [
        PortfolioHolding("A", 25.0),
        PortfolioHolding("B", 20.0),
        PortfolioHolding("C", 15.0),
        PortfolioHolding("D", 15.0),
        PortfolioHolding("E", 10.0),
        PortfolioHolding("F", 8.0),
        PortfolioHolding("G", 7.0),
    ]

    analytics = service.analyze(portfolio)

    print()
    print("=" * 70)
    print("PORTFOLIO ANALYTICS REPORT")
    print("=" * 70)

    print(f"Holdings                : {analytics.holding_count}")
    print(f"Total Weight            : {analytics.total_weight:.2f}%")
    print(f"Equal Weight            : {analytics.equal_weight:.2f}%")
    print(f"Average Weight          : {analytics.average_weight:.2f}%")

    print()

    print(f"Largest Weight          : {analytics.largest_weight:.2f}%")
    print(f"Smallest Weight         : {analytics.smallest_weight:.2f}%")
    print(f"Weight Range            : {analytics.weight_range:.2f}%")

    print()

    print(f"Concentration Score     : {analytics.concentration_score:.2f}")
    print(f"Diversification Score   : {analytics.diversification_score:.2f}")

    print()

    print(f"Overweight Positions    : {analytics.overweight_positions}")
    print(f"Underweight Positions   : {analytics.underweight_positions}")

    print()

    print(f"HHI                     : {analytics.hhi:.4f}")
    print(f"Effective Holdings      : {analytics.effective_holdings:.2f}")

    print()

    print(f"Top 3 Exposure          : {analytics.top3_weight:.2f}%")
    print(f"Top 5 Exposure          : {analytics.top5_weight:.2f}%")

    print()

    print(f"Risk Level              : {analytics.concentration_risk}")
    print(f"Diversification Grade   : {analytics.diversification_grade}")

    if analytics.warnings:
        print()
        print("Warnings")
        for warning in analytics.warnings:
            print(f" - {warning}")

    assert analytics.holding_count == 7
    assert abs(analytics.total_weight - 100.0) < 0.01

    assert analytics.largest_weight == 25.0
    assert analytics.smallest_weight == 7.0

    assert analytics.overweight_positions == 4
    assert analytics.underweight_positions == 3

    assert analytics.top3_weight == 60.0
    assert analytics.top5_weight == 85.0

    assert analytics.hhi > 0
    assert analytics.effective_holdings > 0

    assert analytics.concentration_risk in (
        "Low",
        "Moderate",
        "High",
        "Very High",
    )

    assert analytics.diversification_grade in (
        "A",
        "B",
        "C",
        "D",
    )

    print()
    print("=" * 70)
    print("Sprint 12.1.1B Analytics PASS")
    print("=" * 70)


if __name__ == "__main__":
    test_portfolio_analytics()