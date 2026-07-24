from services.portfolio_construction_service import (
    PortfolioConstructionService,
)


def run_tests():

    service = PortfolioConstructionService(
        max_stock_weight=10.0,
    )

    def conviction(**overrides):

        item = {
            "alpha12_selection_score": 80,
            "fundamental_score": 80,
            "readiness_score": 70,
            "profitability_score": 80,
            "growth_score": 80,
            "financial_strength_score": 80,
            "valuation_score": 70,
            "risk_score": 80,
        }

        item.update(
            overrides
        )

        return service._conviction_score(
            item
        )

    # ------------------------------------------
    # QUALITY COMPOUNDER VS SPECULATIVE HOT GROWTH
    #
    # Strong profitability, growth and balance-sheet
    # quality must outweigh hot readiness when the
    # speculative candidate has weaker investment quality.
    # ------------------------------------------

    quality_compounder = conviction(
        profitability_score=95,
        growth_score=92,
        financial_strength_score=90,
        valuation_score=55,
        risk_score=88,
        readiness_score=45,
    )

    speculative_hot_growth = conviction(
        profitability_score=55,
        growth_score=95,
        financial_strength_score=45,
        valuation_score=40,
        risk_score=45,
        readiness_score=98,
    )

    print(
        "QUALITY_COMPOUNDER           =>",
        round(
            quality_compounder,
            2,
        ),
    )

    print(
        "SPECULATIVE_HOT_GROWTH       =>",
        round(
            speculative_hot_growth,
            2,
        ),
    )

    assert (
        quality_compounder
        >
        speculative_hot_growth
    )

    # ------------------------------------------
    # RISK RESILIENCE MUST MATTER
    #
    # Otherwise-similar investment candidates should
    # favor the more resilient stock.
    # ------------------------------------------

    resilient_quality = conviction(
        profitability_score=90,
        growth_score=88,
        financial_strength_score=90,
        valuation_score=60,
        risk_score=92,
        readiness_score=65,
    )

    same_quality_high_risk = conviction(
        profitability_score=90,
        growth_score=88,
        financial_strength_score=90,
        valuation_score=60,
        risk_score=40,
        readiness_score=65,
    )

    print(
        "RESILIENT_QUALITY            =>",
        round(
            resilient_quality,
            2,
        ),
    )

    print(
        "SAME_QUALITY_HIGH_RISK       =>",
        round(
            same_quality_high_risk,
            2,
        ),
    )

    assert (
        resilient_quality
        >
        same_quality_high_risk
    )

    # ------------------------------------------
    # MOMENTUM / READINESS MUST NOT DOMINATE
    #
    # A stronger long-term business with temporarily weak
    # readiness must remain above a weaker business whose
    # current market setup is hot.
    # ------------------------------------------

    strong_weak_momentum = conviction(
        profitability_score=92,
        growth_score=88,
        financial_strength_score=90,
        valuation_score=65,
        risk_score=85,
        readiness_score=30,
    )

    weaker_hot_momentum = conviction(
        profitability_score=65,
        growth_score=72,
        financial_strength_score=65,
        valuation_score=60,
        risk_score=70,
        readiness_score=98,
    )

    print(
        "STRONG_WEAK_MOMENTUM         =>",
        round(
            strong_weak_momentum,
            2,
        ),
    )

    print(
        "WEAKER_HOT_MOMENTUM          =>",
        round(
            weaker_hot_momentum,
            2,
        ),
    )

    assert (
        strong_weak_momentum
        >
        weaker_hot_momentum
    )

    # ------------------------------------------
    # LEGACY BACKWARD COMPATIBILITY
    #
    # Historical payloads without granular factors must
    # still produce a valid conviction score using the
    # aggregate fundamental fallback.
    # ------------------------------------------

    legacy = {
        "alpha12_selection_score": 82,
        "fundamental_score": 78,
        "readiness_score": 65,
    }

    legacy_score = (
        service._conviction_score(
            legacy
        )
    )

    print(
        "LEGACY_FALLBACK              =>",
        round(
            legacy_score,
            2,
        ),
    )

    assert legacy_score > 0

    # ------------------------------------------
    # GRANULAR FUNDAMENTALS MUST ACTUALLY MATTER
    #
    # Same aggregate fundamental score and same selection
    # score, but superior direct business factors must
    # produce stronger conviction.
    # ------------------------------------------

    granular_strong = conviction(
        fundamental_score=75,
        profitability_score=95,
        growth_score=92,
        financial_strength_score=90,
        valuation_score=60,
    )

    granular_weak = conviction(
        fundamental_score=75,
        profitability_score=60,
        growth_score=62,
        financial_strength_score=65,
        valuation_score=60,
    )

    assert (
        granular_strong
        >
        granular_weak
    ), (
        "Granular investment quality is not influencing "
        "portfolio conviction"
    )

    print()
    print(
        "Sprint 11.5B.2B direct investment "
        "conviction regression: PASS"
    )


if __name__ == "__main__":
    run_tests()
