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


class CashDeploymentRule:
    """
    Generates cash deployment recommendations based on
    overall portfolio health.

    This is the first decision-oriented recommendation
    within the Recommendation Engine.
    """

    def apply(
        self,
        report: RecommendationReport,
        analytics: PortfolioAnalytics,
        health: PortfolioHealth,
    ) -> None:

        if health.overall_grade == "A":

            report.cash_recommendations.append(

                Recommendation(
                    category="Cash Deployment",
                    priority=RecommendationPriority.LOW,
                    action=RecommendationAction.BUY,
                    confidence=96,
                    target="Cash",
                    title="Deploy available cash",
                    reasons=[
                        "Portfolio health is excellent.",
                        "No significant portfolio risks detected.",
                        "Current allocation supports additional investment.",
                    ],
                    suggested_action=(
                        "Deploy available cash according to "
                        "your target asset allocation."
                    ),
                )
            )

        elif health.overall_grade == "B":

            report.cash_recommendations.append(

                Recommendation(
                    category="Cash Deployment",
                    priority=RecommendationPriority.MEDIUM,
                    action=RecommendationAction.MONITOR,
                    confidence=90,
                    target="Cash",
                    title="Deploy cash gradually",
                    reasons=[
                        "Portfolio remains healthy.",
                        "Some optimisation opportunities exist.",
                        "Maintain flexibility for future opportunities.",
                    ],
                    suggested_action=(
                        "Deploy approximately 50% of available cash "
                        "over upcoming investment cycles."
                    ),
                )
            )

        else:

            report.cash_recommendations.append(

                Recommendation(
                    category="Cash Deployment",
                    priority=RecommendationPriority.HIGH,
                    action=RecommendationAction.HOLD,
                    confidence=92,
                    target="Cash",
                    title="Hold available cash",
                    reasons=[
                        "Portfolio health requires attention.",
                        "Improving the existing portfolio takes priority.",
                    ],
                    suggested_action=(
                        "Delay new investments until portfolio health "
                        "improves."
                    ),
                )
            )