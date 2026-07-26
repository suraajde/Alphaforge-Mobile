"""
Sprint 11.x Conviction Weighting Regression Tests
"""

from services.portfolio_construction_service import (
    PortfolioConstructionService,
)


def run_tests():
    service = PortfolioConstructionService()

    print("=" * 60)
    print("Sprint 11.x Conviction Weighting Regression")
    print("=" * 60)

    # ----------------------------------------------------------
    # Test 1
    # Readiness should remain a secondary influence.
    # ----------------------------------------------------------

    lower_readiness = {
        "selection_score": 90,
        "investment_quality": 90,
        "risk_score": 80,
        "portfolio_readiness": 40,
    }

    higher_readiness = {
        "selection_score": 90,
        "investment_quality": 90,
        "risk_score": 80,
        "portfolio_readiness": 90,
    }

    lower_score = service._conviction_score(lower_readiness)
    higher_score = service._conviction_score(higher_readiness)

    difference = higher_score - lower_score

    print(
        "Readiness-only conviction difference:",
        round(difference, 2),
    )

    assert 1.0 <= difference <= 2.0, (
        "Readiness influence is outside the "
        "expected secondary range."
    )

    print("✓ Readiness weighting regression passed")

    # ----------------------------------------------------------
    # Test 2
    # Better investment quality should increase conviction.
    # ----------------------------------------------------------

    weaker_quality = {
        "selection_score": 90,
        "investment_quality": 70,
        "risk_score": 80,
        "portfolio_readiness": 80,
    }

    stronger_quality = {
        "selection_score": 90,
        "investment_quality": 90,
        "risk_score": 80,
        "portfolio_readiness": 80,
    }

    weak = service._conviction_score(weaker_quality)
    strong = service._conviction_score(stronger_quality)

    print(
        "Investment quality improvement:",
        round(strong - weak, 2),
    )

    assert strong > weak

    print("✓ Investment quality regression passed")

    # ----------------------------------------------------------
    # Test 3
    # Lower risk should improve conviction.
    # ----------------------------------------------------------

    high_risk = {
        "selection_score": 90,
        "investment_quality": 90,
        "risk_score": 60,
        "portfolio_readiness": 80,
    }

    low_risk = {
        "selection_score": 90,
        "investment_quality": 90,
        "risk_score": 90,
        "portfolio_readiness": 80,
    }

    high = service._conviction_score(high_risk)
    low = service._conviction_score(low_risk)

    print(
        "Risk contribution difference:",
        round(low - high, 2),
    )

    assert low > high

    print("✓ Risk regression passed")

    print()
    print("=" * 60)
    print("All conviction weighting regression tests passed.")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()