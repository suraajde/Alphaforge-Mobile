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

from services.recommendation_constants import (
    RecommendationPriority,
    RecommendationAction,
)


class PortfolioStructureRule:
    """
    Evaluates the overall portfolio structure.
    """

    def apply(
        self,
        report: RecommendationReport,
        analytics: PortfolioAnalytics,
        health: PortfolioHealth,
    ) -> None:

        reasons = []

        if analytics.holding_count < 10:
            reasons.append(
                f"Portfolio contains only {analytics.holding_count} holdings."
            )

        elif analytics.holding_count > 20:
            reasons.append(
                f"Portfolio contains {analytics.holding_count} holdings."
            )

        if analytics.effective_holdings < 6:
            reasons.append(
                f"Effective holdings: {analytics.effective_holdings:.2f}"
            )

        if analytics.weight_range > 15:
            reasons.append(
                f"Weight range: {analytics.weight_range:.2f}%"
            )

        if not reasons:

            report.portfolio_recommendations.append(

                Recommendation(
                    category="Portfolio Structure",
                    priority=RecommendationPriority.LOW,
                    action=RecommendationAction.MAINTAIN,
                    confidence=96,
                    target="Portfolio",
                    title="Portfolio structure is healthy",
                    reasons=[
                        "Overall portfolio structure is well balanced."
                    ],
                    suggested_action="Maintain current portfolio structure.",
                )
            )

            return

        report.portfolio_recommendations.append(

            Recommendation(
                category="Portfolio Structure",
                priority=RecommendationPriority.MEDIUM,
                action=RecommendationAction.REVIEW_STRUCTURE,
                confidence=89,
                target="Portfolio",
                title="Portfolio structure can be improved",
                reasons=reasons,
                suggested_action=(
                    "Review portfolio construction during the next rebalance."
                ),
            )
        )