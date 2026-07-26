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


class PositionSizingRule:
    """
    Evaluates overall portfolio position sizing.
    """

    def apply(
        self,
        report: RecommendationReport,
        analytics: PortfolioAnalytics,
        health: PortfolioHealth,
    ) -> None:

        overweight_count = analytics.overweight_positions
        underweight_count = analytics.underweight_positions

        if overweight_count == 0 and underweight_count == 0:

            report.portfolio_recommendations.append(
                Recommendation(
                    category="Position Sizing",
                    priority=RecommendationPriority.LOW,
                    action=RecommendationAction.MAINTAIN,
                    confidence=97,
                    target="Portfolio",
                    title="Position sizing is well balanced",
                    reasons=[
                        "No significantly overweight positions detected.",
                        "No significantly underweight positions detected.",
                    ],
                    suggested_action="Maintain current allocation strategy.",
                )
            )

            return

        reasons = []

        if overweight_count > 0:
            reasons.append(
                f"{overweight_count} overweight position(s) detected."
            )

        if underweight_count > 0:
            reasons.append(
                f"{underweight_count} underweight position(s) detected."
            )

        reasons.append(
            f"Largest position: {analytics.largest_weight:.2f}%"
        )

        report.portfolio_recommendations.append(
            Recommendation(
                category="Position Sizing",
                priority=RecommendationPriority.MEDIUM,
                action=RecommendationAction.REVIEW_POSITION_SIZES,
                confidence=91,
                target="Portfolio",
                title="Position sizing can be improved",
                reasons=reasons,
                suggested_action=(
                    "Review overweight and underweight holdings during the next rebalance."
                ),
            )
        )