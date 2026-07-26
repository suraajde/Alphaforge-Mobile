from services.portfolio_health_service import (
    PortfolioHealth,
)

from services.portfolio_analytics_service import (
    PortfolioAnalytics,
)

from services.recommendation_models import (
    Recommendation,
    RecommendationReport,
)


class ConcentrationRule:
    """
    Generates recommendations based on
    portfolio concentration.
    """

    def apply(
        self,
        report: RecommendationReport,
        analytics: PortfolioAnalytics,
        health: PortfolioHealth,
    ) -> None:

        if analytics.concentration_risk not in (
            "High",
            "Very High",
        ):
            return

        report.risk_recommendations.append(

            Recommendation(
                category="Risk",
                priority="HIGH",
                action="REDUCE CONCENTRATION",
                confidence=92,
                target="Portfolio",
                title="Portfolio concentration is elevated",
                reasons=[
                    f"Concentration risk: {analytics.concentration_risk}",
                    f"Top 3 exposure: {analytics.top3_weight:.2f}%",
                    f"HHI: {analytics.hhi:.4f}",
                ],
                suggested_action=(
                    "Reduce allocation to the largest holdings and "
                    "increase diversification."
                ),
            )
        )