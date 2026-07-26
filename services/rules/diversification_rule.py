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


class DiversificationRule:
    """
    Generates recommendations based on
    portfolio diversification.
    """

    def apply(
        self,
        report: RecommendationReport,
        analytics: PortfolioAnalytics,
        health: PortfolioHealth,
    ) -> None:

        if analytics.diversification_grade == "A":

            report.portfolio_recommendations.append(

                Recommendation(
                    category="Diversification",
                    priority=RecommendationPriority.LOW,
                    action=RecommendationAction.MAINTAIN,
                    confidence=97,
                    target="Portfolio",
                    title="Diversification is healthy",
                    reasons=[
                        f"Diversification grade: {analytics.diversification_grade}",
                        f"Effective holdings: {analytics.effective_holdings:.2f}",
                    ],
                    suggested_action=(
                        "Maintain current diversification."
                    ),
                )
            )

        elif analytics.diversification_grade == "B":

            report.portfolio_recommendations.append(

                Recommendation(
                    category="Diversification",
                    priority=RecommendationPriority.MEDIUM,
                    action=RecommendationAction.MONITOR,
                    confidence=90,
                    target="Portfolio",
                    title="Diversification can be improved",
                    reasons=[
                        f"Diversification grade: {analytics.diversification_grade}",
                        f"HHI: {analytics.hhi:.4f}",
                    ],
                    suggested_action=(
                        "Consider improving diversification during future rebalancing."
                    ),
                )
            )

        else:

            report.portfolio_recommendations.append(

                Recommendation(
                    category="Diversification",
                    priority=RecommendationPriority.HIGH,
                    action=RecommendationAction.INCREASE_DIVERSIFICATION,
                    confidence=92,
                    target="Portfolio",
                    title="Portfolio diversification is weak",
                    reasons=[
                        f"Diversification grade: {analytics.diversification_grade}",
                        f"Effective holdings: {analytics.effective_holdings:.2f}",
                    ],
                    suggested_action=(
                        "Reduce concentration and diversify into additional high-quality holdings."
                    ),
                )
            )