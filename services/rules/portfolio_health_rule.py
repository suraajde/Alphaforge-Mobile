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


class PortfolioHealthRule:
    """
    Generates recommendations based on
    overall portfolio health.
    """

    def apply(
        self,
        report: RecommendationReport,
        analytics: PortfolioAnalytics,
        health: PortfolioHealth,
    ) -> None:

        if health.overall_grade == "A":

            report.portfolio_recommendations.append(

                Recommendation(
                    category="Portfolio",
                    priority=RecommendationPriority.LOW,
                    action=RecommendationAction.HOLD,
                    confidence=98,
                    target="Portfolio",
                    title="Portfolio is healthy",
                    reasons=[
                        "Portfolio health score is excellent.",
                        "No immediate rebalance required.",
                    ],
                    suggested_action="Continue current investment strategy.",
                )
            )

        elif health.overall_grade == "B":

            report.portfolio_recommendations.append(

                Recommendation(
                    category="Portfolio",
                    priority=RecommendationPriority.MEDIUM,
                    action=RecommendationAction.MONITOR,
                    confidence=90,
                    target="Portfolio",
                    title="Minor optimisation recommended",
                    reasons=[
                        "Portfolio remains healthy.",
                        "Some metrics can be improved.",
                    ],
                    suggested_action="Review portfolio during next rebalance cycle.",
                )
            )

        else:

            report.portfolio_recommendations.append(

                Recommendation(
                    category="Portfolio",
                    priority=RecommendationPriority.HIGH,
                    action=RecommendationAction.REBALANCE,
                    confidence=88,
                    target="Portfolio",
                    title="Portfolio requires attention",
                    reasons=[
                        "Portfolio health has deteriorated.",
                    ],
                    suggested_action="Review allocations and rebalance.",
                )
            )